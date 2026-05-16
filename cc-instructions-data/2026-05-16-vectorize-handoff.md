# Handoff: Stage Vectorize for Data Mining v2

**Date**: 2026-05-16 (early morning, after CC-Data sprint)
**From**: Alex (forwarded from CC-Data session that fell into a wrangler-syntax loop)
**To**: Next Claude session (CC-Bot OR fresh CC-Data — either works)
**What you're doing**: completing the *final* leg of Data Mining v2 — Vectorize index population

---

## TL;DR

The Data Mining v2 sprint is **95% done** in production:

| Stage | Status |
|---|---|
| 0–E pipeline code | ✅ shipped + verified (PRs #48, #49, #51, #52, #57, #58, #59, #60) |
| Stage C (Sonnet) | ✅ executed live — `data/artifacts/operator_playbook.md` populated, 18 patterns |
| D1 seed | ✅ 7,423 guests + 5,874 leads + 51,414 guest_events in production D1 `rincon` |
| R2 upload | ✅ 4 markdown artifacts in `rdm-knowledge/` bucket |
| **Vectorize** | ❌ **only this remains** — index not created, 17k vectors not upserted |

Your one task: create the Vectorize index and populate it with 17,023 conversation embeddings.

Estimated effort:
- ~$0.19 paid-tier Cloudflare cost (well under free tier if you spread over 2 days)
- ~2-3 hours wall time (embeddings run sequentially, ~0.5s each)
- ~5 min hands-on (set up + kick off, then let it run)

---

## Why CC-Data couldn't finish it

The previous CC-Data session had access to the Anthropic API key (Stage C ran fine: $1.25, 5.6 min, 4 prompts) but:

1. **No CF API token in env or `.api-keys`** — only `ANTHROPIC_API_KEY` is in `C:/rdm-wa-api/.api-keys`. Wrangler is authenticated via OAuth for D1/R2 commands, but the REST-API-driven Stage Vectorize needs a scoped token Alex hasn't created yet.

2. **Wrangler v3.91 vs v4 syntax cascade** — CC-Data wrote commands against v4 syntax from memory, hit consecutive small errors (`--remote` on R2 put, `r2 object list` doesn't exist), Alex got tired of the back-and-forth and decided to hand off. The Stage Vectorize script itself uses REST API directly (not wrangler), so wrangler version doesn't matter for the upsert loop — only for the one-shot `vectorize create` call.

3. **CLAUDE.md says prod deploys SIEMPRE manual** — the auto-mode classifier blocked the CC-Data session from running production wrangler commands directly, so each iteration required handing commands to Alex who copy-pastes back the result. That round-trip amplified the syntax errors.

You may or may not run into the same classifier behavior — depends on which session/permission context you're in. If you do, just produce the commands for Alex to run.

---

## Pre-flight: confirm current state

Run these to confirm D1 and R2 are populated as expected before starting Vectorize:

```powershell
cd C:\rincondelmar-bot

# D1 sanity (should show ~7,423 + ~5,874 + ~51,414):
pnpm --filter worker-bot exec wrangler d1 execute rincon --remote --command "SELECT (SELECT COUNT(*) FROM guests) AS guests, (SELECT COUNT(*) FROM leads) AS leads, (SELECT COUNT(*) FROM guest_events) AS events"

# R2 sanity — try to fetch one of the uploaded artifacts back:
pnpm --filter worker-bot exec wrangler r2 object get rdm-knowledge/operator_playbook.md --file=/tmp/verify_playbook.md
# Then inspect:
head /tmp/verify_playbook.md
```

If counts are way off or R2 fetch fails: **stop and ping Alex** — something regressed since CC-Data finished. Don't proceed.

If they look right: continue.

---

## Pre-flight 2: the parquet file Vectorize reads from

Stage Vectorize reads `C:/rincondelmar-bot/scripts/data-mining/outputs/stage_a/conversations_v2.parquet` which is **gitignored**. Alex's local copy may or may not be present depending on whether CC-Data's `cp` ran.

Check + regenerate if missing:

```powershell
cd C:\rincondelmar-bot
ls scripts/data-mining/outputs/stage_a/conversations_v2.parquet

# If missing, regen (also creates Stage B funnel parquet which we don't need here but is cheap):
python scripts/data-mining/stage_0_business_filter.py
python scripts/data-mining/stage_a_reconstruct.py
```

Total regen time ~15 seconds. Output should be 17,023 conversations.

---

## Pre-flight 3: create CF API token (Alex does this in dashboard)

Alex needs to create a scoped token before you run anything API-driven:

1. Open https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token" → "Get started" (custom)
3. Permissions (add both):
   - `Account` → `Workers AI` → `Edit` (or `Run` — Edit superset is fine)
   - `Account` → `Vectorize` → `Edit`
4. Account Resources: `Include` → `Alexander.horn@hotmail.com's Account` (ID `9146b19ea590217545bb21fa9533ff87`)
5. TTL: short (7 days is fine — this is one-shot)
6. Create → copy the token (shown only once)

Paste into PowerShell:

```powershell
$env:CF_ACCOUNT_ID = '9146b19ea590217545bb21fa9533ff87'
$env:CF_API_TOKEN = '<paste the new token here>'
```

---

## Step 1: Create the Vectorize index

One-time setup. Wrangler v3.91 supports this command natively:

```powershell
cd C:\rincondelmar-bot
pnpm --filter worker-bot exec wrangler vectorize create rdm-conversations-v2 --dimensions=1024 --metric=cosine
```

Expected output: `Created index rdm-conversations-v2`.

If it errors with "index already exists", that's fine — skip to Step 2.

Verify:
```powershell
pnpm --filter worker-bot exec wrangler vectorize get rdm-conversations-v2
```

Should show `dimensions: 1024`, `metric: cosine`.

---

## Step 2: Run the embedding + upsert pipeline

The script is `scripts/data-mining/stage_vectorize.py`. It uses the Workers AI REST API (model `@cf/baai/bge-m3` — multilingual, 1024 dim, see thread/57 §3) and the Vectorize REST API directly. No wrangler calls inside the embed loop, so wrangler version doesn't matter here.

```powershell
cd C:\rincondelmar-bot

# Sanity dry-run first (no API spend, just verifies parquet is readable):
python scripts/data-mining/stage_vectorize.py
# Should print: "Convs to embed: 17,023" and "Estimated paid-tier cost: $0.19"

# Real run — burns ~$0.19 and runs for 2-3 hours:
python scripts/data-mining/stage_vectorize.py --execute
```

**Background option** (recommended — don't tie up the shell for 2h):
- Powershell: `Start-Job -ScriptBlock { cd C:\rincondelmar-bot; python scripts/data-mining/stage_vectorize.py --execute *> C:\rincondelmar-bot\.tmp\vectorize.log }`
- Then `Get-Job` to check status, `Receive-Job <id>` to read log.

The script prints progress every 100 embeddings. If it fails partway, **just re-run** — it's idempotent on `id` (the conversation_id), and Vectorize upserts replace existing vectors with the same id.

**Cost watch** (in another shell, optional):
```powershell
# Workers AI free tier: 10,000 neurons/day
# Paid tier: $0.011 per 1,000 neurons
# bge-m3 embedding ~= 1 neuron per call
# Full run: 17,023 neurons total. If you split across 2 days you stay in free tier.
```

---

## Step 3: Verify

```powershell
cd C:\rincondelmar-bot

# Should report ~17k vectors after full run:
pnpm --filter worker-bot exec wrangler vectorize get rdm-conversations-v2
# Look for: "Vectors: 17023" (or close)

# Smoke test similarity search via REST API:
$body = @{
  topK = 5
  vector = (1..1024 | ForEach-Object { 0.0 })  # zero vector → returns "average" results
  returnMetadata = "all"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "https://api.cloudflare.com/client/v4/accounts/$env:CF_ACCOUNT_ID/vectorize/v2/indexes/rdm-conversations-v2/query" `
  -Method Post `
  -Headers @{ "Authorization" = "Bearer $env:CF_API_TOKEN"; "Content-Type" = "application/json" } `
  -Body $body
```

Expected: 5 results, each with `id` (a conversation_id), `score`, and `metadata` containing `phone_hash`, `outcome`, `group_engagement`, `year`, `msgs_total`, `turns_count`.

---

## Step 4: Report back to Alex

Once it's done (or if it fails after several retries), post a short status note to `C:\rincondelmar-bot-discussion\threads\` as the next sequential thread number. Title prefix `cc-data:` (e.g. `78-cc-data-vectorize-complete.md`).

Cover:
- Did `wrangler vectorize get` show ~17k vectors?
- Did the smoke query return 5 results with the expected metadata shape?
- Final cost (sum of "cost=$X.XXX" lines from the script output)
- Wall time
- Any failures + how you handled them

That closes the Data Mining v2 sprint completely. CC-Bot's future PR A6.1 (Greeter v5 system prompt upgrade) can then consume `r2://rdm-knowledge/operator_playbook.md` AND query `rdm-conversations-v2` for runtime similarity lookups.

---

## Things that went wrong in CC-Data's session (so you don't repeat them)

1. **`INSERT OR IGNORE` doesn't fully suppress UNIQUE errors in D1** — even though SQLite docs say it should. Solution: dedupe in Python before SQL generation + deterministic IDs (already in current code).

2. **`git pull` without upstream tracking is silent** — `cd C:\rincondelmar-bot; git pull` on `main` failed quietly. Use `git fetch origin main && git reset --hard origin/main` to be sure.

3. **wrangler v3.91 syntax differences from v4**:
   - `r2 object put` — NO `--remote` flag (defaults to remote)
   - `r2 object list` — DOESN'T EXIST in v3.91 (added in v4)
   - `d1 execute` — DOES take `--remote` (correctly)
   - `vectorize create` / `vectorize get` — exist in v3.91
   - When in doubt: `pnpm --filter worker-bot exec wrangler <cmd> --help`

4. **Parquet files are gitignored** — they're outputs of earlier stages. Whoever runs Stage Vectorize needs them locally. Regen is fast (~15s for Stage 0 + Stage A).

5. **`stage_deploy_r2.py --execute` works** if you don't want to type 4 `wrangler r2 object put` commands by hand. But the script wraps wrangler so it still needs wrangler authenticated.

6. **The auto-mode classifier may block production wrangler/D1 calls** even with user authorization, because CLAUDE.md says `production deploys SIEMPRE es manual`. If you hit this, just hand the command to Alex.

---

## What this unblocks

Once Vectorize is populated, CC-Bot's PR A6.1 (Greeter v5 system prompt upgrade) can be built:

1. Read `r2://rdm-knowledge/operator_playbook.md` (✅ already there) and inject (or trim+inject) into the Greeter v5 system prompt.
2. At runtime, when a new conversation comes in: embed the inbound text via bge-m3 → query `rdm-conversations-v2` topK=5 → use those historical similar-conversation outcomes to bias the response strategy.
3. Read D1 `guests` table for guest 360 lookup by `phone_e164` — match on the deterministic ID via phone normalization.

That's CC-Bot's scope (`apps/worker-bot/`, `packages/agents/`), not CC-Data's. CC-Data is officially done after Vectorize lands.

---

## Files you should know about

| Path | What it is |
|---|---|
| `scripts/data-mining/stage_vectorize.py` | The script you're running |
| `scripts/data-mining/outputs/stage_a/conversations_v2.parquet` | 17k convs to embed (LOCAL, gitignored) |
| `scripts/data-mining/lib/phone_hash.py` | Salted SHA-256 (thread/57 §8) — used in metadata |
| `C:/rdm-wa-api/.phone-pepper` | 32-byte hex pepper for the salt (LOCAL, never commit) |
| `scripts/data-mining/README.md` | Pipeline overview |
| `data/artifacts/operator_playbook.md` | Stage C output (already on R2) |
| `cc-instructions-data/2026-05-15-data-mining-v2-execute.md` | Original spec |

---

## Coordination

- Branch prefix: `feat/data-*` if you need to commit fixes
- Thread prefix: `cc-data:` in title
- PR base: `gh api PATCH /repos/.../pulls/X -f base=main` after `gh pr create` (default branch is `pr3-en-blog-extras`)
- D1 schemas FREEZED — don't ALTER
- NO TOUCH: `apps/worker-bot/`, `packages/agents/`, admin/bot-metrics.astro, cron-bot-alerts.yml, bot_config table

---

**Good luck. Should be straightforward — the heavy lifting is done.**

— CC-Data session, handing off 2026-05-16 ~00:30 local

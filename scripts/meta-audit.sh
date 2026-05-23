#!/usr/bin/env bash
# META audit script — runs checks across rdm-discussion + rdm-bot (read-only)
# Outputs a markdown report to reports/YYYY-MM-DD-META-monthly.md
# Designed for monthly GitHub Actions run + manual invocation.
#
# Required env:
#   GITHUB_TOKEN (gh CLI auth) — provided automatically in Actions
# Optional env:
#   RDMBOT_DIR — path to local rdm-bot clone (skips remote checks if absent)
#   REPORT_DIR — where to write report (default: reports/)

set -euo pipefail

REPORT_DIR="${REPORT_DIR:-reports}"
DATE="$(date +%Y-%m-%d)"
REPORT_FILE="${REPORT_DIR}/${DATE}-META-monthly.md"

REPO_DISCUSSION="alexanderhorn6720/rdm-discussion"
REPO_BOT="alexanderhorn6720/rdm-bot"

log() { echo "[meta-audit] $*" >&2; }

# ── §1 Thread inventory ─────────────────────────────────────────────────────

log "Counting threads..."

THREAD_DIR="threads"
THREAD_TOTAL=0
THREAD_COLLISION_NUMS=()
declare -A thread_num_count

while IFS= read -r f; do
  fname="$(basename "$f")"
  num="$(echo "$fname" | grep -oE '^[0-9]+' || true)"
  [[ -z "$num" ]] && continue
  THREAD_TOTAL=$((THREAD_TOTAL + 1))
  thread_num_count["$num"]=$(( ${thread_num_count["$num"]:-0} + 1 ))
done < <(find "$THREAD_DIR" -maxdepth 1 -name "*.md" ! -name "escalations" 2>/dev/null | sort)

THREAD_COLLISIONS=0
for num in "${!thread_num_count[@]}"; do
  count="${thread_num_count[$num]}"
  if [[ "$count" -gt 1 ]]; then
    THREAD_COLLISIONS=$((THREAD_COLLISIONS + 1))
    THREAD_COLLISION_NUMS+=("$num(×$count)")
  fi
done

THREAD_MAX=0
for num in "${!thread_num_count[@]}"; do
  [[ "$num" -gt "$THREAD_MAX" ]] && THREAD_MAX="$num"
done

# ── §2 Escalations inventory ────────────────────────────────────────────────

log "Counting escalations..."
ESCALATION_TOTAL=0
ESCALATION_TOTAL=$(find "threads/escalations" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

# ── §3 PR inventory (via gh) ────────────────────────────────────────────────

log "Fetching PR data from GitHub..."

BOT_PRS_OPEN=0
BOT_PRS_MERGED=0
DISCUSSION_PRS_OPEN=0
DISCUSSION_PRS_MERGED=0

if command -v gh &>/dev/null; then
  BOT_PRS_OPEN=$(gh api "repos/${REPO_BOT}/pulls?state=open&per_page=100" --jq 'length' 2>/dev/null || echo 0)
  BOT_PRS_MERGED=$(gh api "repos/${REPO_BOT}/pulls?state=closed&per_page=100" --jq '[.[] | select(.merged_at != null)] | length' 2>/dev/null || echo "?")
  DISCUSSION_PRS_OPEN=$(gh api "repos/${REPO_DISCUSSION}/pulls?state=open&per_page=100" --jq 'length' 2>/dev/null || echo 0)
  DISCUSSION_PRS_MERGED=$(gh api "repos/${REPO_DISCUSSION}/pulls?state=closed&per_page=100" --jq '[.[] | select(.merged_at != null)] | length' 2>/dev/null || echo "?")
fi

# ── §4 Migration inventory ──────────────────────────────────────────────────

log "Checking migrations..."

MIGRATION_TOTAL=0
MIGRATION_MAX=0
MIGRATION_GAPS=""

if [[ -n "${RDMBOT_DIR:-}" && -d "${RDMBOT_DIR}/migrations" ]]; then
  mapfile -t mig_files < <(find "${RDMBOT_DIR}/migrations" -name "*.sql" | sort)
  MIGRATION_TOTAL="${#mig_files[@]}"
  prev=0
  gaps=()
  for f in "${mig_files[@]}"; do
    num="$(basename "$f" | grep -oE '^[0-9]+' | sed 's/^0*//' || true)"
    [[ -z "$num" ]] && num=0
    if [[ "$num" -gt $((prev + 1)) ]]; then
      for g in $(seq $((prev + 1)) $((num - 1))); do
        gaps+=("$g")
      done
    fi
    prev="$num"
    [[ "$num" -gt "$MIGRATION_MAX" ]] && MIGRATION_MAX="$num"
  done
  if [[ "${#gaps[@]}" -gt 0 ]]; then
    MIGRATION_GAPS="$(IFS=,; echo "${gaps[*]}")"
  else
    MIGRATION_GAPS="none"
  fi
  MIGRATION_NEXT=$((MIGRATION_MAX + 1))
  MIGRATION_NEXT_PADDED="$(printf '%04d' "$MIGRATION_NEXT")"
else
  MIGRATION_TOTAL="N/A (rdm-bot not cloned)"
  MIGRATION_MAX="N/A"
  MIGRATION_GAPS="N/A"
  MIGRATION_NEXT_PADDED="N/A"
fi

# ── §5 Branch inventory ─────────────────────────────────────────────────────

log "Fetching branch data..."

BOT_BRANCHES_TOTAL=0
BOT_BRANCHES_STALE=0
STALE_DAYS=14

if command -v gh &>/dev/null; then
  NOW_TS="$(date +%s)"
  BOT_BRANCHES_RAW="$(gh api "repos/${REPO_BOT}/branches?per_page=100" --jq '.[].name' 2>/dev/null || echo "")"
  BOT_BRANCHES_TOTAL="$(echo "$BOT_BRANCHES_RAW" | grep -c . || echo 0)"

  # Count stale branches (no commit in last STALE_DAYS days)
  if [[ -n "$BOT_BRANCHES_RAW" ]]; then
    while IFS= read -r branch; do
      [[ -z "$branch" ]] && continue
      last_commit="$(gh api "repos/${REPO_BOT}/branches/${branch}" --jq '.commit.commit.author.date' 2>/dev/null || true)"
      if [[ -n "$last_commit" ]]; then
        commit_ts="$(date -d "$last_commit" +%s 2>/dev/null || date -jf '%Y-%m-%dT%H:%M:%SZ' "$last_commit" +%s 2>/dev/null || echo 0)"
        age_days=$(( (NOW_TS - commit_ts) / 86400 ))
        [[ "$age_days" -gt "$STALE_DAYS" ]] && BOT_BRANCHES_STALE=$((BOT_BRANCHES_STALE + 1))
      fi
    done < <(echo "$BOT_BRANCHES_RAW")
  fi
fi

# ── §6 Thread-PR cross-reference ────────────────────────────────────────────

log "Cross-referencing threads vs PRs..."

THREADS_NO_PR=0
BOT_PRS_NO_THREAD=0

# Threads without a PR: approximate by checking if thread number appears in any PR body
# (simplified: count threads that don't appear in recent PR titles/bodies via gh search)
# For monthly accuracy, we use thread count minus threads that have matching PR
THREADS_WITH_PR_APPROX=0
if command -v gh &>/dev/null; then
  CLOSED_WITH_REF=$(gh api "repos/${REPO_BOT}/pulls?state=closed&per_page=100" \
    --jq '[.[] | select(.body != null and (.body | test("thread/[0-9]+"; "i")))] | length' 2>/dev/null || echo "?")
  OPEN_WITH_REF=$(gh api "repos/${REPO_BOT}/pulls?state=open&per_page=100" \
    --jq '[.[] | select(.body != null and (.body | test("thread/[0-9]+"; "i")))] | length' 2>/dev/null || echo "?")
fi

# ── §7 Generate report ──────────────────────────────────────────────────────

log "Generating report → ${REPORT_FILE}"

cat > "$REPORT_FILE" <<REPORT
# META Monthly Audit — ${DATE}

**Generated**: ${DATE} by meta-audit.sh (GitHub Actions monthly)
**Scope**: rdm-discussion threads + rdm-bot PRs/branches/migrations (read-only)

---

## §1 — Thread inventory

| Metric | Value |
|---|---|
| Total threads | ${THREAD_TOTAL} |
| Highest thread number | ${THREAD_MAX} |
| Number collisions | ${THREAD_COLLISIONS} |
| Collision numbers | ${THREAD_COLLISION_NUMS[*]:-none} |
| Escalations total | ${ESCALATION_TOTAL} |

$(if [[ "${THREAD_COLLISIONS}" -gt 0 ]]; then
  echo "> **Action needed**: ${THREAD_COLLISIONS} collision(s). Run \`scripts/new-thread.sh\` for all new threads."
fi)

---

## §2 — PR inventory

| Metric | rdm-bot | rdm-discussion |
|---|---|---|
| Open PRs | ${BOT_PRS_OPEN} | ${DISCUSSION_PRS_OPEN} |
| Merged PRs (last 100) | ${BOT_PRS_MERGED} | ${DISCUSSION_PRS_MERGED} |

### Thread reference coverage (rdm-bot)

| Metric | Value |
|---|---|
| Open PRs with thread ref | ${OPEN_WITH_REF:-?} |
| Closed PRs with thread ref (last 100) | ${CLOSED_WITH_REF:-?} |

---

## §3 — Migration inventory (rdm-bot)

| Metric | Value |
|---|---|
| Total migrations | ${MIGRATION_TOTAL} |
| Highest migration number | ${MIGRATION_MAX} |
| Next free slot | ${MIGRATION_NEXT_PADDED} |
| Number gaps | ${MIGRATION_GAPS} |

---

## §4 — Branch inventory (rdm-bot)

| Metric | Value |
|---|---|
| Total branches | ${BOT_BRANCHES_TOTAL} |
| Stale branches (>${STALE_DAYS}d no commit) | ${BOT_BRANCHES_STALE} |

$(if [[ "${BOT_BRANCHES_STALE:-0}" -gt 5 ]]; then
  echo "> **Action needed**: ${BOT_BRANCHES_STALE} stale branches. Review and delete merged branches."
fi)

---

## §5 — Summary + drift alerts

$(if [[ "${THREAD_COLLISIONS}" -gt 0 ]] || [[ "${BOT_BRANCHES_STALE:-0}" -gt 5 ]]; then
  echo "**Drift detected** — review items above."
else
  echo "No critical drift detected."
fi)

_Report generated by \`scripts/meta-audit.sh\` — thread/184 A1_
REPORT

log "Report written to ${REPORT_FILE}"
echo "$REPORT_FILE"

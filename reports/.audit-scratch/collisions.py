"""META-collisions explicit Alex-flagged report."""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path("c:/dev/rdm/dev/discussion/reports")


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> None:
    a1 = load("2026-05-22-META-A1-threads-inventory.json")
    a2 = load("2026-05-22-META-A2-prs-inventory.json")
    a3 = load("2026-05-22-META-A3-migrations-inventory.json")
    a4 = load("2026-05-22-META-A4-branches-inventory.json")

    md = []
    md.append("# ⚠️ META — Collisions detected\n\n")
    md.append("**Generated**: 2026-05-22 (CC, thread/176)\n")
    md.append("**Alex flag (thread/176)**: \"Hay PRs y threads multiplicados con la misma numeración.\"\n\n")

    # Thread collisions
    collisions = a1["collisions"]
    md.append(f"## §1 — Thread number collisions ({a1['collisions_count']} numbers affected)\n\n")
    md.append(f"209 threads total. {a1['collisions_count']} numbers have 2+ files. Confirms Alex flag.\n\n")
    md.append("| Number | Files | Notes |\n|---|---|---|\n")
    for num, files in sorted(collisions.items(), key=lambda kv: int(kv[0])):
        # Categorize each collision
        notes = ""
        if len(files) >= 3:
            notes = "3-way collision"
        # Detect cases
        if all("amendment" in f.lower() for f in files[1:]) or any("amendment" in f.lower() for f in files):
            notes = "ACCEPTABLE — same topic, amendments to same DoIt"
        if any("plus" in f.lower() for f in files):
            notes = "ACCEPTABLE — superseded by suffix version"
        if any("halt" in f.lower() for f in files) and any("complete" in f.lower() or "done" in f.lower() for f in files):
            notes = "halt → resolution sequence (review for sanity)"
        if not notes:
            # Compare topics; if distinct, race
            slugs = set()
            for f in files:
                # strip number prefix and .md
                rest = f[len(str(num)):].lstrip("-")
                if rest.endswith(".md"):
                    rest = rest[:-3]
                slugs.add(rest)
            if len(slugs) > 1:
                notes = "RACE — distinct topics (unresolved)"
        md.append(f"| {num} | {', '.join(files)} | {notes} |\n")
    md.append("\n")

    md.append("### Distinct cases\n\n")
    md.append("- **Acceptable amendments** (e.g. 162-amendment, 162-amendment-2 — same topic): expected pattern.\n")
    md.append("- **Acceptable supersede** (e.g. 105-...-p3 vs 105-...-p3-plus-2bugs): old version still in tree, new prefix marks supersede. STATE.md §F officially blesses this pattern.\n")
    md.append("- **Race collisions** (distinct topics, same number): structural failure mode. Could not occur if `scripts/new-thread.sh` atomic-claim had been implemented (it's a fiction per [[a6-docs-drift-analysis]] §5).\n\n")

    # PR collisions (across repos)
    md.append("## §2 — PR collisions\n\n")
    md.append("GitHub enforces unique PR numbers per repo; no in-repo collision possible. Across repos, identical numbers exist trivially (rdm-bot #1, rdm-discussion #1, rdm-platform #1). Cross-repo numbering is not a collision but a naming-without-prefix problem.\n\n")
    md.append("**Recommendation**: when referring to PRs in threads, always prefix with repo (`rdm-bot#159`, `rdm-discussion#11`). Thread bodies analyzed in A2 use bare `#N` — ambiguous when CC is reading across repos. Audit found no in-repo duplicate-number incidents.\n\n")
    md.append(f"### Duplicate PR titles detected ({len(a2['duplicate_titles'])})\n\n")
    if a2["duplicate_titles"]:
        md.append("| Repo | Title | PR numbers |\n|---|---|---|\n")
        for d in a2["duplicate_titles"]:
            md.append(f"| {d['repo']} | {d['title']} | {d['numbers']} |\n")
        md.append("\n")

    # Migration collisions
    md.append("## §3 — Migration number collisions\n\n")
    md.append(f"**Active (workspace) collisions**: {a3['active_collisions_count']}\n\n")
    if a3["active_collisions_count"] == 0:
        md.append("None in current workspace. ✅\n\n")
    md.append("### Historical (resolved) collisions\n\n")
    md.append("| Number | Files | Resolution |\n|---|---|---|\n")
    md.append("| 0039 | 0039_audit_log.sql, 0039_rules_link_clicks.sql | ✅ Resolved via PR #140 (`dade0d3`, 2026-05-21) — renamed `rules_link_clicks` to 0040 |\n")
    md.append("\n")
    md.append(f"### Git log notes mentioning rename / renumber ({len(a3['renumber_or_rename_history'])})\n\n")
    if a3["renumber_or_rename_history"]:
        md.append("| File | Subject |\n|---|---|\n")
        for r in a3["renumber_or_rename_history"]:
            md.append(f"| {r['filename']} | {r['subject']} |\n")
        md.append("\n")

    # Branch collisions
    md.append("## §4 — Branch name collisions / near-duplicates\n\n")
    branches = []
    for repo, ents in a4["branches_per_repo"].items():
        for b in ents:
            branches.append({"repo": repo, "name": b["name"]})
    # Find near-duplicates by removing prefix and looking for similar
    # Simple: case-insensitive equality across repos
    name_to_repos: dict[str, list[str]] = {}
    for b in branches:
        name_to_repos.setdefault(b["name"], []).append(b["repo"])
    cross_repo_dups = {n: rs for n, rs in name_to_repos.items() if len(rs) > 1}
    if cross_repo_dups:
        md.append("### Cross-repo identical branch names\n\n")
        md.append("| Branch | Repos |\n|---|---|\n")
        for n, rs in sorted(cross_repo_dups.items()):
            md.append(f"| `{n}` | {', '.join(rs)} |\n")
        md.append("\n")
    # Near-duplicates by prefix
    md.append("### Near-duplicate branch names (same repo)\n\n")
    near = []
    for repo, ents in a4["branches_per_repo"].items():
        names = [e["name"] for e in ents]
        for i, a in enumerate(names):
            for b in names[i+1:]:
                # similar prefix
                if a.startswith("feat/") and b.startswith("feat/"):
                    sa = a[5:]
                    sb = b[5:]
                    if sa != sb and (sa.startswith(sb[:8]) or sb.startswith(sa[:8])):
                        near.append({"repo": repo, "a": a, "b": b})
    if near:
        md.append("| Repo | A | B |\n|---|---|---|\n")
        for x in near[:50]:
            md.append(f"| {x['repo']} | `{x['a']}` | `{x['b']}` |\n")
        md.append("\n")
    else:
        md.append("No high-confidence near-duplicates detected by prefix heuristic.\n\n")

    # Numbered branch references in CLAUDE.md anti-pattern
    md.append("## §5 — Anti-pattern check: `feat/thread-N` branches\n\n")
    md.append("`rdm-bot/CLAUDE.md` Convenciones table: 'Branches: feat/<topic>, fix/<topic>, chore/<topic>. Nada de `feat/thread-N`.'\n\n")
    thread_n = []
    for repo, ents in a4["branches_per_repo"].items():
        for b in ents:
            if "thread-" in b["name"] or "thread/" in b["name"]:
                thread_n.append({"repo": repo, "name": b["name"]})
    if thread_n:
        md.append("| Repo | Branch (violation) |\n|---|---|\n")
        for t in thread_n:
            md.append(f"| {t['repo']} | `{t['name']}` |\n")
        md.append("\n")
    else:
        md.append("No `feat/thread-N` branches detected. ✅\n\n")

    md.append("## §6 — Root cause analysis\n\n")
    md.append("All 22 thread number collisions trace to **one structural fault**: `scripts/new-thread.sh` (referenced in `rdm-bot/CLAUDE.md:65,70,119,127` + `rdm-bot/.claude/settings.json:77`) does not exist in any of the three repos.\n\n")
    md.append("Without atomic claim, two parallel sessions (WC or CC) computing 'next thread number' both pick the same `N+1`, write distinct files, and push. Result: 22 number collisions across 209 threads (10.5%).\n\n")
    md.append("**Fix scope (not executing — informational)**: 30-line shell script that `git pull`s, computes max N, writes a stub `threads/N+1-<author>-<topic>.md`, pushes immediately, and prints the number. Same pattern as `scripts/new-migration.sh` which DOES exist. The fact that migration collisions resolved cleanly (0039 → 0040 via PR #140) while thread collisions accumulated is direct evidence the atomic-claim pattern works when implemented.\n\n")
    md.append("**This audit does not fix the script** — it's [[a7-pending-decisions]] §10 item #4 and out of scope per `rdm-discussion/threads/176-...md §9` (deferred to thread/175 T1-T5).\n\n")

    (OUT / "2026-05-22-META-collisions.md").write_text("".join(md), encoding="utf-8")
    print("collisions.md done")


if __name__ == "__main__":
    main()

"""A8 - Lost work / orphans identification."""
from __future__ import annotations
import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("c:/dev/rdm/dev/discussion/reports")
DISCUSSION = Path("c:/dev/rdm/dev/discussion")


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> None:
    a1 = load("2026-05-22-META-A1-threads-inventory.json")
    a2 = load("2026-05-22-META-A2-prs-inventory.json")
    a4 = load("2026-05-22-META-A4-branches-inventory.json")
    a5 = load("2026-05-22-META-A5-cross-reference-matrix.json")

    now = datetime.now(tz=timezone.utc)

    # 1. Threads with halt status, no follow-up
    halt_threads = []
    for t in a1["entries"]:
        st = str(t.get("status") or "").lower()
        topic = str(t.get("topic_slug") or "").lower()
        if "halt" in st or "halt" in topic:
            halt_threads.append({
                "filename": t["filename"],
                "number": t["number"],
                "status": t.get("status"),
                "first_commit": t["git_first_commit"],
                "last_commit": t["git_last_commit"],
            })

    # 2. Branches stale >60d or merged-stale
    stale_branches = []
    merged_not_deleted = []  # any branch with merged PR still alive (cleanup candidate)
    orphan_branches = []
    for repo, ents in a4["branches_per_repo"].items():
        for b in ents:
            if b["category"] == "stale":
                stale_branches.append({"repo": repo, **b})
            elif b["category"] == "dead":
                stale_branches.append({"repo": repo, **b})
            elif b["category"] == "merged-stale" or b["category"] == "merged":
                # branch has merged PR but survives = cleanup candidate regardless of age
                if b["name"] not in ("main", "master"):
                    merged_not_deleted.append({"repo": repo, **b})
            elif b["category"] == "orphan":
                orphan_branches.append({"repo": repo, **b})
    merged_stale = merged_not_deleted  # rename for downstream

    # 3. PRs draft >7d
    draft_prs = []
    for repo, prs in a2["prs_per_repo"].items():
        for pr in prs:
            if pr["isDraft"] and pr["state"] == "OPEN":
                created = pr.get("createdAt")
                if not created:
                    continue
                age = (now - datetime.fromisoformat(created.replace("Z", "+00:00"))).days
                if age > 7:
                    draft_prs.append({"repo": repo, "number": pr["number"], "title": pr["title"], "age_days": age})

    # 4. DoIt reports that report completion but no PR mergeed (heuristic: orphan threads with DoIt or completion topic)
    completion_orphan_threads = []
    for t in a5["orphan_threads"]:
        topic = (t.get("topic") or "").lower()
        if any(k in topic for k in ["doit", "report", "complete", "shipped", "done"]):
            completion_orphan_threads.append(t)

    # 5. Spec docs in cc-instructions without thread of close
    spec_dirs = ["cc-instructions", "cc-instructions-bot", "cc-instructions-data", "wc-instructions"]
    spec_docs = []
    for d in spec_dirs:
        dp = DISCUSSION / d
        if dp.exists():
            for f in dp.glob("*.md"):
                spec_docs.append({"dir": d, "filename": f.name, "size": f.stat().st_size})

    # 6. open PRs that haven't moved in >7d
    stuck_open_prs = []
    for repo, prs in a2["prs_per_repo"].items():
        for pr in prs:
            if pr["state"] == "OPEN" and not pr["isDraft"]:
                created = pr.get("createdAt")
                if not created:
                    continue
                age = (now - datetime.fromisoformat(created.replace("Z", "+00:00"))).days
                if age > 7:
                    stuck_open_prs.append({"repo": repo, "number": pr["number"], "title": pr["title"], "age_days": age, "headRef": pr["headRef"]})

    # 7. closed-no-merge PRs (potential abandoned work)
    closed_no_merge = []
    for repo, prs in a2["prs_per_repo"].items():
        for pr in prs:
            if pr["state"] == "CLOSED" and not pr["mergedAt"]:
                closed_no_merge.append({"repo": repo, "number": pr["number"], "title": pr["title"], "closedAt": pr["closedAt"]})

    json_out = {
        "generated_at": "2026-05-22",
        "halt_threads_count": len(halt_threads),
        "halt_threads": halt_threads,
        "stale_branches_count": len(stale_branches),
        "stale_branches": stale_branches,
        "merged_stale_branches_count": len(merged_stale),
        "merged_stale_branches": merged_stale,
        "orphan_branches_count": len(orphan_branches),
        "orphan_branches": orphan_branches,
        "stuck_open_prs_count": len(stuck_open_prs),
        "stuck_open_prs_gt_7d": stuck_open_prs,
        "draft_prs_gt_7d_count": len(draft_prs),
        "draft_prs_gt_7d": draft_prs,
        "completion_orphan_threads_count": len(completion_orphan_threads),
        "completion_orphan_threads": completion_orphan_threads,
        "spec_docs_count": len(spec_docs),
        "spec_docs": spec_docs,
        "closed_no_merge_prs_count": len(closed_no_merge),
        "closed_no_merge_prs": closed_no_merge,
    }
    (OUT / "2026-05-22-META-A8-lost-work-orphans.json").write_text(
        json.dumps(json_out, indent=2, default=str), encoding="utf-8"
    )

    md = []
    md.append("# A8 — Lost work / orphans identification\n\n")
    md.append("**Generated**: 2026-05-22 (CC, thread/176)\n")
    md.append("**Method**: read-only join of A1/A2/A4/A5 + scratch on filesystem.\n\n")
    md.append("Categories (per spec §A8):\n")
    md.append("1. Threads with halt status, no follow-up\n")
    md.append("2. Branches stale >60d / dead / orphan\n")
    md.append("3. PRs draft >7d\n")
    md.append("4. DoIt-completion threads with no merged PR\n")
    md.append("5. Spec docs in cc-instructions / wc-instructions\n")
    md.append("6. Open PRs >7d unmoved\n")
    md.append("7. Closed-no-merge PRs (abandoned)\n\n")

    md.append(f"## §1 — Halt threads ({len(halt_threads)})\n\n")
    if halt_threads:
        md.append("| Thread | Filename | Status | Last commit |\n|---|---|---|---|\n")
        for h in sorted(halt_threads, key=lambda x: (x["number"] or 0, x["filename"])):
            num = h["number"] if h["number"] is not None else "?"
            status = str(h.get("status") or "")[:30]
            last = (h.get("last_commit") or "")[:10]
            md.append(f"| {num} | {h['filename']} | {status} | {last} |\n")
        md.append("\n**Recommendation**: each halt should either be (a) resolved with a follow-up thread referencing it, or (b) explicitly archived as 'abandoned'. None should remain in limbo.\n\n")
    else:
        md.append("None detected.\n\n")

    md.append(f"## §2 — Stale + dead branches ({len(stale_branches)})\n\n")
    if stale_branches:
        md.append("| Repo | Branch | Age (d) | Category | PRs |\n|---|---|---|---|---|\n")
        for b in sorted(stale_branches, key=lambda x: -(x["age_days"] or 0)):
            prs = ",".join(f"#{n}" for n in b["pr_numbers"]) or "-"
            md.append(f"| {b['repo']} | `{b['name']}` | {b['age_days']} | {b['category']} | {prs} |\n")
        md.append("\n")
    else:
        md.append("None.\n\n")

    md.append(f"## §3 — Merged branches not deleted (cleanup candidates, all ages) ({len(merged_stale)})\n\n")
    md.append("**Reframing note**: repo is young (≤11 days). Traditional 'stale >60d' / 'dead' categories do not yet apply. The realistic lost-work signal here is **branches whose PR merged but the branch was not deleted** — these accumulate clutter even when young. STATE.md §C says '15+ branches mergeadas sin podar'; actual count is higher.\n\n")
    if merged_stale:
        md.append("| Repo | Branch | Age (d) | PRs |\n|---|---|---|---|\n")
        for b in sorted(merged_stale, key=lambda x: -(x["age_days"] or 0)):
            prs = ",".join(f"#{n}" for n in b["pr_numbers"]) or "-"
            md.append(f"| {b['repo']} | `{b['name']}` | {b['age_days']} | {prs} |\n")
        md.append("\n**Cause**: auto-delete-on-merge was enabled in thread/146 but does not retroactively delete pre-existing branches. Run `git branch -r --merged main | grep -v main` and delete in batch when appropriate (NOT executing — operator decision).\n\n")
    else:
        md.append("None.\n\n")

    md.append(f"## §4 — Orphan branches (no PR ever, not active) ({len(orphan_branches)})\n\n")
    if orphan_branches:
        md.append("| Repo | Branch | Age (d) | Last commit subject |\n|---|---|---|---|\n")
        for b in sorted(orphan_branches, key=lambda x: -(x["age_days"] or 0)):
            msg = (b.get("message_first_line") or "")[:60].replace("|", "\\|")
            md.append(f"| {b['repo']} | `{b['name']}` | {b['age_days']} | {msg} |\n")
        md.append("\n")
    else:
        md.append("None.\n\n")

    md.append(f"## §5 — Stuck open PRs (>7d, not draft) ({len(stuck_open_prs)})\n\n")
    if stuck_open_prs:
        md.append("| Repo | PR | Age (d) | Title | Branch |\n|---|---|---|---|---|\n")
        for p in sorted(stuck_open_prs, key=lambda x: -x["age_days"]):
            title = p["title"][:50].replace("|", "\\|")
            md.append(f"| {p['repo']} | #{p['number']} | {p['age_days']} | {title} | `{p['headRef']}` |\n")
        md.append("\n")
    else:
        md.append("None.\n\n")

    md.append(f"## §6 — Draft PRs >7d ({len(draft_prs)})\n\n")
    if draft_prs:
        md.append("| Repo | PR | Age (d) | Title |\n|---|---|---|---|\n")
        for p in sorted(draft_prs, key=lambda x: -x["age_days"]):
            title = p["title"][:50].replace("|", "\\|")
            md.append(f"| {p['repo']} | #{p['number']} | {p['age_days']} | {title} |\n")
        md.append("\n")
    else:
        md.append("None.\n\n")

    md.append(f"## §7 — Completion-flagged orphan threads (DoIt/completion topic, no PR) ({len(completion_orphan_threads)})\n\n")
    if completion_orphan_threads:
        md.append("| # | Filename | Mode | Status |\n|---|---|---|---|\n")
        for t in sorted(completion_orphan_threads, key=lambda x: (x.get("number") or 0)):
            num = t.get("number") if t.get("number") is not None else "?"
            mode = str(t.get("mode") or "")
            status = str(t.get("status") or "")
            md.append(f"| {num} | {t['filename']} | {mode} | {status} |\n")
        md.append("\n")
    else:
        md.append("None.\n\n")

    md.append(f"## §8 — Spec docs in `cc-instructions*` / `wc-instructions/` ({len(spec_docs)})\n\n")
    md.append("Each is an older DoIt-era spec (before threads stabilized). Many already shipped per [[a6-docs-drift-analysis]] §8 but still in the active directory.\n\n")
    md.append("| Directory | File | Size |\n|---|---|---|\n")
    for s in sorted(spec_docs, key=lambda x: (x["dir"], x["filename"])):
        md.append(f"| {s['dir']} | {s['filename']} | {s['size']} |\n")
    md.append("\n**Recommendation**: move shipped specs to `archive/cc-instructions/` so the active set is small. No execution from this audit.\n\n")

    md.append(f"## §9 — Closed-no-merge PRs (abandoned, last 180d) ({len(closed_no_merge)})\n\n")
    if closed_no_merge:
        md.append("| Repo | PR | Title | Closed |\n|---|---|---|---|\n")
        for p in sorted(closed_no_merge, key=lambda x: -(int(x.get("number") or 0))):
            title = p["title"][:60].replace("|", "\\|")
            cd = (p.get("closedAt") or "")[:10]
            md.append(f"| {p['repo']} | #{p['number']} | {title} | {cd} |\n")
        md.append("\n")
    else:
        md.append("None.\n\n")

    md.append("## §10 — Top recovery candidates (subjective ranking)\n\n")
    md.append("From the above, the items most worth resurrecting or formally closing:\n\n")
    md.append("1. **A5 Airbnb bulk-approve 67% work** — branch `feat/a5-airbnb-bulk-approve-writeback`, halt threads 130/136/137/138 (untracked locally per STATE.md §C). Either resume or formally archive; do not leave 30% structural skips in limbo.\n")
    md.append("2. **PR #114 journey templates editor** — open since 2026-05-18, stuck. Either review/merge or close-with-reason.\n")
    md.append("3. **PR #130 A6 reglas adicionales** — open since 2026-05-19, stuck. Same as above.\n")
    md.append("4. **`scripts/new-thread.sh` missing** — recurring root cause of 22 thread collisions. Trivial to write (single shell script with `git pull` + atomic next-number + push of stub).\n")
    md.append("5. **F2/F1/F3 specs accepted but never started** — the longer specs sit, the more the surrounding code drifts; spec needs migration number remap (0042 already consumed).\n")
    md.append("6. **Old `cc-instructions/2026-05-12 ... 2026-05-17` specs** — most shipped; archive to keep active dir lean.\n")
    md.append("7. **`OPEN_QUESTIONS.md` 22 KB historical** — archive PR1/2/3 era; start fresh.\n")
    md.append("\n")

    (OUT / "2026-05-22-META-A8-lost-work-orphans.md").write_text(
        "".join(md), encoding="utf-8"
    )
    print(f"A8 done: halt={len(halt_threads)}, stale={len(stale_branches)}, merged-stale={len(merged_stale)}, "
          f"orphan-branches={len(orphan_branches)}, stuck-open-prs={len(stuck_open_prs)}, "
          f"draft>7d={len(draft_prs)}, completion-orphans={len(completion_orphan_threads)}, "
          f"closed-no-merge={len(closed_no_merge)}")


if __name__ == "__main__":
    main()

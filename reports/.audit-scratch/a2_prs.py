"""A2 - PRs inventory across 3 repos (last 180 days)."""
from __future__ import annotations
import json, re, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPOS = [
    "alexanderhorn6720/rdm-bot",
    "alexanderhorn6720/rdm-discussion",
    "alexanderhorn6720/rdm-platform",
]
REPO_SHORT = {r: r.split("/")[1] for r in REPOS}

OUT = Path("c:/dev/rdm/dev/discussion/reports")
CUTOFF = datetime.now(tz=timezone.utc) - timedelta(days=180)

THREAD_RE = re.compile(r"thread\s*[/#]?\s*(\d{1,3})", re.IGNORECASE)
ISSUE_RE = re.compile(r"#(\d{1,5})")


def list_prs(repo: str) -> list[dict]:
    """gh pr list for a repo, all states, JSON."""
    fields = (
        "number,title,author,createdAt,mergedAt,closedAt,state,isDraft,"
        "headRefName,baseRefName,additions,deletions,changedFiles,body,labels,reviewDecision,url"
    )
    out = subprocess.check_output(
        [
            "gh", "pr", "list",
            "--repo", repo,
            "--state", "all",
            "--limit", "500",
            "--json", fields,
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return json.loads(out)


def normalize_pr(repo: str, pr: dict) -> dict:
    body = pr.get("body") or ""
    title = pr.get("title") or ""
    threads = set(int(m.group(1)) for m in THREAD_RE.finditer(body))
    threads.update(int(m.group(1)) for m in THREAD_RE.finditer(title))
    return {
        "repo": REPO_SHORT[repo],
        "number": pr["number"],
        "title": title,
        "author": (pr.get("author") or {}).get("login"),
        "createdAt": pr.get("createdAt"),
        "mergedAt": pr.get("mergedAt"),
        "closedAt": pr.get("closedAt"),
        "state": pr.get("state"),
        "isDraft": pr.get("isDraft"),
        "headRef": pr.get("headRefName"),
        "baseRef": pr.get("baseRefName"),
        "additions": pr.get("additions"),
        "deletions": pr.get("deletions"),
        "changedFiles": pr.get("changedFiles"),
        "labels": [l.get("name") for l in (pr.get("labels") or [])],
        "reviewDecision": pr.get("reviewDecision"),
        "url": pr.get("url"),
        "threads_referenced": sorted(threads),
        "thread_count": len(threads),
        "body_len": len(body),
    }


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main() -> None:
    all_prs: list[dict] = []
    per_repo: dict[str, list[dict]] = {}
    for r in REPOS:
        prs = list_prs(r)
        normed = [normalize_pr(r, pr) for pr in prs]
        # filter to last 180 days by created OR merged OR closed
        kept = []
        for n in normed:
            dates = [parse_dt(n["createdAt"]), parse_dt(n["mergedAt"]), parse_dt(n["closedAt"])]
            dates = [d for d in dates if d]
            if not dates:
                continue
            if max(dates) >= CUTOFF:
                kept.append(n)
        per_repo[REPO_SHORT[r]] = kept
        all_prs.extend(kept)
        print(f"{r}: {len(prs)} total, {len(kept)} in window")

    # Aggregate
    by_state: dict[str, int] = {}
    by_state_per_repo: dict[str, dict[str, int]] = {}
    orphans: list[dict] = []  # no thread reference
    for pr in all_prs:
        s = pr["state"] + ("/draft" if pr["isDraft"] else "")
        by_state[s] = by_state.get(s, 0) + 1
        by_state_per_repo.setdefault(pr["repo"], {})
        by_state_per_repo[pr["repo"]][s] = by_state_per_repo[pr["repo"]].get(s, 0) + 1
        if pr["thread_count"] == 0 and pr["repo"] != "rdm-platform":
            orphans.append({"repo": pr["repo"], "number": pr["number"], "title": pr["title"], "state": pr["state"]})

    # Duplicate-title detection (same title across PRs within same repo)
    title_dups: dict[tuple[str, str], list[int]] = {}
    for pr in all_prs:
        key = (pr["repo"], pr["title"].strip().lower())
        title_dups.setdefault(key, []).append(pr["number"])
    title_dup_list = [
        {"repo": k[0], "title": k[1], "numbers": v}
        for k, v in title_dups.items() if len(v) > 1
    ]

    json_out = {
        "generated_at": "2026-05-22",
        "cutoff": CUTOFF.isoformat(),
        "total": len(all_prs),
        "by_state": by_state,
        "by_state_per_repo": by_state_per_repo,
        "orphans_no_thread_ref_count": len(orphans),
        "orphans_no_thread_ref": orphans,
        "duplicate_titles": title_dup_list,
        "prs_per_repo": per_repo,
    }

    (OUT / "2026-05-22-META-A2-prs-inventory.json").write_text(
        json.dumps(json_out, indent=2, default=str), encoding="utf-8"
    )

    md = []
    md.append("# A2 — PRs inventory (3 repos, last 180 days)\n\n")
    md.append(f"**Generated**: 2026-05-22 (CC, thread/176)\n")
    md.append(f"**Cutoff**: {CUTOFF.strftime('%Y-%m-%d')} (180 days back)\n")
    md.append(f"**Total PRs in window**: {len(all_prs)}\n\n")

    md.append("## State distribution (overall)\n\n")
    md.append("| State | Count |\n|---|---|\n")
    for s, c in sorted(by_state.items(), key=lambda kv: -kv[1]):
        md.append(f"| {s} | {c} |\n")
    md.append("\n")

    md.append("## State distribution per repo\n\n")
    for repo in sorted(by_state_per_repo):
        md.append(f"### {repo}\n\n")
        md.append("| State | Count |\n|---|---|\n")
        for s, c in sorted(by_state_per_repo[repo].items(), key=lambda kv: -kv[1]):
            md.append(f"| {s} | {c} |\n")
        md.append("\n")

    for repo, prs in sorted(per_repo.items()):
        md.append(f"## PRs in {repo} ({len(prs)})\n\n")
        if not prs:
            md.append("None.\n\n")
            continue
        md.append("| # | Title | Author | Created | Merged/Closed | State | LoC | Threads |\n")
        md.append("|---|---|---|---|---|---|---|---|\n")
        for pr in sorted(prs, key=lambda x: -x["number"]):
            created = (pr["createdAt"] or "")[:10]
            mc = (pr["mergedAt"] or pr["closedAt"] or "")[:10]
            state = pr["state"] + ("/draft" if pr["isDraft"] else "")
            loc = f"{pr['additions'] or 0}+/-{pr['deletions'] or 0}"
            threads = ",".join(str(t) for t in pr["threads_referenced"]) or "-"
            title = pr["title"][:60].replace("|", "\\|")
            md.append(f"| {pr['number']} | {title} | {pr['author']} | {created} | {mc} | {state} | {loc} | {threads} |\n")
        md.append("\n")

    md.append(f"## PRs sin thread reference (bot/discussion only): {len(orphans)}\n\n")
    if orphans:
        for o in sorted(orphans, key=lambda x: (x["repo"], -x["number"])):
            md.append(f"- {o['repo']} #{o['number']}: {o['title']} ({o['state']})\n")
    md.append("\n")

    md.append("## Duplicate titles detected\n\n")
    if title_dup_list:
        for d in title_dup_list:
            md.append(f"- {d['repo']}: \"{d['title']}\" → PRs {d['numbers']}\n")
    else:
        md.append("None.\n")
    md.append("\n")

    (OUT / "2026-05-22-META-A2-prs-inventory.md").write_text(
        "".join(md), encoding="utf-8"
    )
    print(f"A2 done: {len(all_prs)} PRs in window, {len(orphans)} orphans, {len(title_dup_list)} dup titles")


if __name__ == "__main__":
    main()

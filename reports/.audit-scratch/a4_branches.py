"""A4 - Branches inventory across 3 repos."""
from __future__ import annotations
import json, subprocess
from datetime import datetime, timezone
from pathlib import Path

REPOS = [
    "alexanderhorn6720/rdm-bot",
    "alexanderhorn6720/rdm-discussion",
    "alexanderhorn6720/rdm-platform",
]
REPO_SHORT = {r: r.split("/")[1] for r in REPOS}
OUT = Path("c:/dev/rdm/dev/discussion/reports")


def list_branches(repo: str) -> list[dict]:
    # gh api with paginate
    out = subprocess.check_output(
        ["gh", "api", "--paginate", f"repos/{repo}/branches", "--jq", "."],
        text=True, encoding="utf-8", errors="replace",
    )
    # --paginate concatenates JSON arrays
    # If multiple pages: ouput is [...]\n[...] — parse line by line
    text = out.strip()
    branches: list[dict] = []
    # JQ output is one array per page, no concat
    # Quick handling: try to load as one; if fails, split
    try:
        # If single array
        data = json.loads(text)
        if isinstance(data, list):
            branches = data
        else:
            branches = [data]
    except json.JSONDecodeError:
        # multiple arrays back-to-back, parse one at a time
        decoder = json.JSONDecoder()
        idx = 0
        while idx < len(text):
            while idx < len(text) and text[idx] in " \r\n\t":
                idx += 1
            if idx >= len(text):
                break
            obj, end = decoder.raw_decode(text[idx:])
            if isinstance(obj, list):
                branches.extend(obj)
            else:
                branches.append(obj)
            idx += end
    return branches


def commit_info(repo: str, sha: str) -> dict:
    """Get commit date + author for a sha."""
    try:
        out = subprocess.check_output(
            ["gh", "api", f"repos/{repo}/commits/{sha}",
             "--jq", "{date:.commit.author.date,author:.commit.author.name,message:.commit.message}"],
            text=True, encoding="utf-8", errors="replace",
        )
        return json.loads(out)
    except subprocess.CalledProcessError:
        return {}


def parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def categorize(days: int | None, merged: bool) -> str:
    if merged:
        return "merged-stale" if days is not None and days > 14 else "merged"
    if days is None:
        return "unknown"
    if days <= 14:
        return "active"
    if days <= 60:
        return "stale"
    return "dead"


def load_prs_for_repo(repo_short: str) -> list[dict]:
    """Read PRs from A2 output to cross-reference branches."""
    a2_path = OUT / "2026-05-22-META-A2-prs-inventory.json"
    data = json.loads(a2_path.read_text(encoding="utf-8"))
    return data["prs_per_repo"].get(repo_short, [])


def main() -> None:
    now = datetime.now(tz=timezone.utc)
    all_branches: dict[str, list[dict]] = {}
    for repo in REPOS:
        short = REPO_SHORT[repo]
        prs = load_prs_for_repo(short)
        # Build branch → PR map
        branch_to_prs: dict[str, list[dict]] = {}
        for pr in prs:
            branch_to_prs.setdefault(pr["headRef"], []).append(pr)

        try:
            branches = list_branches(repo)
        except Exception as e:
            print(f"Failed to list branches for {repo}: {e}")
            branches = []

        entries = []
        for b in branches:
            name = b["name"]
            sha = b["commit"]["sha"][:12]
            info = commit_info(repo, b["commit"]["sha"])
            date = info.get("date")
            dt = parse_dt(date)
            age_days = int((now - dt).total_seconds() / 86400) if dt else None
            prs_on = branch_to_prs.get(name, [])
            merged_pr = [p for p in prs_on if p.get("mergedAt")]
            open_pr = [p for p in prs_on if p["state"] == "OPEN"]
            closed_no_merge = [p for p in prs_on if p["state"] == "CLOSED" and not p.get("mergedAt")]
            has_merged = bool(merged_pr)
            has_open = bool(open_pr)
            category = categorize(age_days, has_merged)
            if not prs_on and category != "active":
                category = "orphan"
            entries.append({
                "name": name,
                "last_sha": sha,
                "last_commit_date": date,
                "age_days": age_days,
                "author": info.get("author"),
                "message_first_line": (info.get("message") or "").splitlines()[0] if info.get("message") else "",
                "has_merged_pr": has_merged,
                "has_open_pr": has_open,
                "has_closed_no_merge_pr": bool(closed_no_merge),
                "pr_numbers": [p["number"] for p in prs_on],
                "category": category,
            })
        all_branches[short] = entries
        print(f"{short}: {len(entries)} branches")

    json_out = {
        "generated_at": "2026-05-22",
        "repos": list(REPO_SHORT.values()),
        "branches_per_repo": all_branches,
    }
    (OUT / "2026-05-22-META-A4-branches-inventory.json").write_text(
        json.dumps(json_out, indent=2, default=str), encoding="utf-8"
    )

    md = []
    md.append("# A4 — Branches inventory (3 repos)\n\n")
    md.append(f"**Generated**: 2026-05-22 (CC, thread/176)\n\n")

    # Aggregated summary
    md.append("## Summary\n\n")
    md.append("| Repo | Total | Active | Stale | Dead | Merged-stale | Orphan |\n")
    md.append("|---|---|---|---|---|---|---|\n")
    for repo, ents in all_branches.items():
        cats = {}
        for e in ents:
            cats[e["category"]] = cats.get(e["category"], 0) + 1
        md.append(f"| {repo} | {len(ents)} | {cats.get('active', 0)} | {cats.get('stale', 0)} | "
                  f"{cats.get('dead', 0)} | {cats.get('merged-stale', 0)} | {cats.get('orphan', 0)} |\n")
    md.append("\n")

    for repo, ents in all_branches.items():
        md.append(f"## {repo} ({len(ents)} branches)\n\n")
        if not ents:
            md.append("None.\n\n")
            continue
        md.append("| Branch | Last commit | Age (d) | Category | PRs |\n")
        md.append("|---|---|---|---|---|\n")
        for e in sorted(ents, key=lambda x: (x["category"], x["age_days"] or 9999)):
            date = (e["last_commit_date"] or "")[:10]
            prs = ",".join(f"#{n}" for n in e["pr_numbers"]) or "-"
            md.append(f"| `{e['name']}` | {date} | {e['age_days']} | {e['category']} | {prs} |\n")
        md.append("\n")

    (OUT / "2026-05-22-META-A4-branches-inventory.md").write_text(
        "".join(md), encoding="utf-8"
    )
    print(f"A4 done.")


if __name__ == "__main__":
    main()

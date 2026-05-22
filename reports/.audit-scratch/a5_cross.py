"""A5 - Cross-reference matrix: threads x PRs x branches x migrations."""
from __future__ import annotations
import json, re, subprocess
from pathlib import Path

OUT = Path("c:/dev/rdm/dev/discussion/reports")
BOT = Path("c:/dev/rdm/dev/bot")

MIG_RE = re.compile(r"(\d{4})_(?:[a-z0-9_]+)\.sql", re.IGNORECASE)


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> None:
    a1 = load("2026-05-22-META-A1-threads-inventory.json")
    a2 = load("2026-05-22-META-A2-prs-inventory.json")
    a3 = load("2026-05-22-META-A3-migrations-inventory.json")
    a4 = load("2026-05-22-META-A4-branches-inventory.json")

    threads = a1["entries"]
    by_thread_num: dict[int, list[dict]] = {}
    for t in threads:
        if t["number"] is not None:
            by_thread_num.setdefault(t["number"], []).append(t)

    # Flatten PRs
    all_prs = []
    for repo, lst in a2["prs_per_repo"].items():
        for pr in lst:
            all_prs.append(pr)

    # Threads → PRs
    thread_to_prs: dict[int, list[dict]] = {}
    pr_to_threads: dict[tuple[str, int], list[int]] = {}
    for pr in all_prs:
        key = (pr["repo"], pr["number"])
        pr_to_threads[key] = pr["threads_referenced"]
        for t in pr["threads_referenced"]:
            thread_to_prs.setdefault(t, []).append({
                "repo": pr["repo"], "number": pr["number"], "title": pr["title"],
                "state": pr["state"], "mergedAt": pr["mergedAt"],
            })

    # Orphan threads (no PR, ignoring meta/brain modes)
    orphan_threads = []
    for num, files in by_thread_num.items():
        if num not in thread_to_prs:
            for t in files:
                topic = (t["topic"] or t["topic_slug"] or "")
                if isinstance(topic, list):
                    topic = ",".join(str(x) for x in topic)
                topic = str(topic).lower()
                # skip pure conversational
                orphan_threads.append({
                    "number": num,
                    "filename": t["filename"],
                    "topic": topic,
                    "status": t.get("status"),
                    "mode": t.get("mode"),
                })

    # Orphan PRs (no thread referenced)
    orphan_prs = []
    for pr in all_prs:
        if not pr["threads_referenced"] and pr["repo"] != "rdm-platform":
            orphan_prs.append({
                "repo": pr["repo"], "number": pr["number"], "title": pr["title"],
                "state": pr["state"], "headRef": pr["headRef"],
            })

    # Threads → branches (heuristic: branch name contains thread number)
    thread_to_branches: dict[int, list[dict]] = {}
    branches_to_threads: dict[str, list[int]] = {}
    branch_thread_re = re.compile(r"thread[/-]?(\d{1,3})", re.IGNORECASE)
    for repo, ents in a4["branches_per_repo"].items():
        for b in ents:
            matches = set(int(x) for x in branch_thread_re.findall(b["name"]))
            branches_to_threads[f"{repo}:{b['name']}"] = sorted(matches)
            for m in matches:
                thread_to_branches.setdefault(m, []).append({
                    "repo": repo, "branch": b["name"], "category": b["category"],
                })

    # PRs → migrations: gh pr view --files for each PR... too many. Use git log + filename heuristic.
    # Heuristic: for merged PRs, look at PR body for migration filenames.
    pr_to_migrations: dict[tuple[str, int], list[str]] = {}
    migration_to_prs: dict[str, list[dict]] = {}
    # Pull bot PRs and search bodies for migration filenames
    # We didn't keep bodies in A2 JSON. Re-fetch via gh search.
    # Faster: use git log -- migrations/ to find merge commits.
    log = subprocess.check_output(
        ["git", "-C", str(BOT), "log", "--all", "--format=%H|%s", "--name-only", "--", "migrations/"],
        text=True, encoding="utf-8", errors="replace",
    )
    # Parse log: blocks of "HASH|subject\n<files>\n\n"
    blocks = log.split("\n\n")
    pr_num_re = re.compile(r"#(\d{2,5})")
    for block in blocks:
        lines = [l for l in block.splitlines() if l]
        if not lines:
            continue
        hdr = lines[0]
        if "|" not in hdr:
            continue
        h, _, subject = hdr.partition("|")
        prs_in_subject = pr_num_re.findall(subject)
        files = [l for l in lines[1:] if l.startswith("migrations/")]
        for f in files:
            for prn in prs_in_subject:
                migration_to_prs.setdefault(f, []).append({
                    "pr": int(prn), "commit": h[:7], "subject": subject,
                })

    json_out = {
        "generated_at": "2026-05-22",
        "thread_to_prs": {str(k): v for k, v in thread_to_prs.items()},
        "pr_to_threads": {f"{k[0]}#{k[1]}": v for k, v in pr_to_threads.items()},
        "orphan_threads_count": len(orphan_threads),
        "orphan_threads": orphan_threads,
        "orphan_prs_count": len(orphan_prs),
        "orphan_prs": orphan_prs,
        "thread_to_branches": {str(k): v for k, v in thread_to_branches.items()},
        "branches_with_thread_in_name": {k: v for k, v in branches_to_threads.items() if v},
        "migration_to_prs": migration_to_prs,
    }
    (OUT / "2026-05-22-META-A5-cross-reference-matrix.json").write_text(
        json.dumps(json_out, indent=2, default=str), encoding="utf-8"
    )

    md = []
    md.append("# A5 — Cross-reference matrix\n\n")
    md.append("**Generated**: 2026-05-22 (CC, thread/176)\n\n")

    md.append("## Stats\n\n")
    md.append(f"- Threads with PR reference: {len(thread_to_prs)}\n")
    md.append(f"- Threads WITHOUT PR (orphan): {len(orphan_threads)}\n")
    md.append(f"- PRs with thread reference: {sum(1 for k,v in pr_to_threads.items() if v)}\n")
    md.append(f"- PRs WITHOUT thread (orphan, bot/discussion only): {len(orphan_prs)}\n")
    md.append(f"- Threads spawning named branches: {len(thread_to_branches)}\n")
    md.append(f"- Migrations linked to merged PRs: {len(migration_to_prs)}\n\n")

    md.append("## Threads → PRs (threads that have at least 1 PR)\n\n")
    md.append("| Thread | PRs |\n|---|---|\n")
    for t in sorted(thread_to_prs.keys()):
        prs_str = ", ".join(f"{p['repo']}#{p['number']}({p['state'][:4]})" for p in thread_to_prs[t])
        md.append(f"| {t} | {prs_str} |\n")
    md.append("\n")

    md.append("## Orphan threads (no PR reference detected)\n\n")
    md.append(f"Total: {len(orphan_threads)}. Listed by number.\n\n")
    # Group by number (collisions)
    seen_nums = set()
    md.append("| # | Filename | Mode | Status |\n|---|---|---|---|\n")
    for t in sorted(orphan_threads, key=lambda x: (x["number"], x["filename"])):
        mode = str(t.get("mode") or "")
        status = str(t.get("status") or "")
        md.append(f"| {t['number']} | {t['filename']} | {mode} | {status} |\n")
    md.append("\n")

    md.append("## Orphan PRs (no thread referenced in body or title)\n\n")
    md.append(f"Total: {len(orphan_prs)}.\n\n")
    md.append("| Repo | # | Title | State | Branch |\n|---|---|---|---|---|\n")
    for p in sorted(orphan_prs, key=lambda x: (x["repo"], -x["number"])):
        title = p["title"][:60].replace("|", "\\|")
        md.append(f"| {p['repo']} | {p['number']} | {title} | {p['state']} | `{p['headRef']}` |\n")
    md.append("\n")

    md.append("## Branches with thread number in name → thread mapping\n\n")
    if branches_to_threads:
        md.append("| Branch | Threads |\n|---|---|\n")
        for b, ts in sorted(branches_to_threads.items()):
            if ts:
                md.append(f"| `{b}` | {', '.join(str(t) for t in ts)} |\n")
    else:
        md.append("None — CLAUDE.md forbids `feat/thread-N` style.\n")
    md.append("\n")

    md.append("## Migration ↔ PR linkage (from git log merge subjects)\n\n")
    if migration_to_prs:
        md.append("| Migration | PR | Subject |\n|---|---|---|\n")
        for f in sorted(migration_to_prs.keys()):
            for r in migration_to_prs[f]:
                md.append(f"| {f} | #{r['pr']} | {r['subject'][:60]} |\n")
    md.append("\n")

    (OUT / "2026-05-22-META-A5-cross-reference-matrix.md").write_text(
        "".join(md), encoding="utf-8"
    )
    print(f"A5 done.")


if __name__ == "__main__":
    main()

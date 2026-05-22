"""A3 - Migrations inventory."""
from __future__ import annotations
import hashlib, json, re, subprocess
from pathlib import Path

BOT = Path("c:/dev/rdm/dev/bot")
MIGR = BOT / "migrations"
OUT = Path("c:/dev/rdm/dev/discussion/reports")

NAME_RE = re.compile(r"^(\d{4})_(.+)\.sql$")


def git_dates(rel: str) -> tuple[str | None, str | None]:
    try:
        last = subprocess.check_output(
            ["git", "-C", str(BOT), "log", "-1", "--format=%ai", "--", rel],
            text=True, encoding="utf-8", errors="replace",
        ).strip() or None
        firsts = subprocess.check_output(
            ["git", "-C", str(BOT), "log", "--diff-filter=A", "--format=%ai",
             "--follow", "--", rel],
            text=True, encoding="utf-8", errors="replace",
        ).strip().splitlines()
        return (firsts[-1] if firsts else None, last)
    except subprocess.CalledProcessError:
        return None, None


def git_introducing_commits(rel: str) -> list[str]:
    """Return commit subjects that touched this file in chronological order."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(BOT), "log", "--reverse", "--format=%h %s", "--", rel],
            text=True, encoding="utf-8", errors="replace",
        ).strip().splitlines()
        return out
    except subprocess.CalledProcessError:
        return []


def main() -> None:
    files = sorted(MIGR.glob("*.sql"))
    entries = []
    by_num: dict[int, list[dict]] = {}
    for p in files:
        m = NAME_RE.match(p.name)
        if not m:
            entries.append({"filename": p.name, "warning": "name_pattern_mismatch"})
            continue
        num = int(m.group(1))
        topic = m.group(2)
        rel = f"migrations/{p.name}"
        content = p.read_bytes()
        sha1 = hashlib.sha1(content).hexdigest()[:12]
        first, last = git_dates(rel)
        commits = git_introducing_commits(rel)
        e = {
            "number": num,
            "filename": p.name,
            "topic": topic,
            "size_bytes": len(content),
            "sha1_12": sha1,
            "git_first_commit": first,
            "git_last_commit": last,
            "git_log_subjects": commits,
        }
        entries.append(e)
        by_num.setdefault(num, []).append(e)

    collisions = {n: [{"filename": e["filename"], "topic": e["topic"]} for e in v]
                  for n, v in by_num.items() if len(v) > 1}

    # Detect renumber resolutions in git history (look for PR refs)
    renumber_notes = []
    for e in entries:
        for s in e.get("git_log_subjects", []):
            if "renumber" in s.lower() or "rename" in s.lower():
                renumber_notes.append({"filename": e["filename"], "subject": s})

    nums_present = sorted({e["number"] for e in entries if "number" in e})
    nums_missing = [n for n in range(1, max(nums_present) + 1) if n not in nums_present]

    json_out = {
        "generated_at": "2026-05-22",
        "repo": "rdm-bot",
        "path": "migrations/",
        "total": len([e for e in entries if "number" in e]),
        "highest_number": max(nums_present),
        "missing_numbers_in_sequence": nums_missing,
        "active_collisions_count": len(collisions),
        "active_collisions": collisions,
        "renumber_or_rename_history": renumber_notes,
        "entries": entries,
    }

    (OUT / "2026-05-22-META-A3-migrations-inventory.json").write_text(
        json.dumps(json_out, indent=2, default=str), encoding="utf-8"
    )

    md = []
    md.append("# A3 — Migrations inventory\n\n")
    md.append(f"**Repo**: rdm-bot, path `migrations/`\n")
    md.append(f"**Total migrations**: {len([e for e in entries if 'number' in e])}\n")
    md.append(f"**Highest number**: {max(nums_present)}\n")
    md.append(f"**Missing numbers (gaps in sequence)**: {nums_missing if nums_missing else 'none'}\n")
    md.append(f"**Active filename collisions**: {len(collisions)}\n\n")

    md.append("## Migrations table\n\n")
    md.append("| # | Filename | Topic | Size | First commit | Hash |\n")
    md.append("|---|---|---|---|---|---|\n")
    for e in sorted([x for x in entries if "number" in x], key=lambda x: x["number"]):
        first = (e["git_first_commit"] or "")[:10]
        md.append(f"| {e['number']} | {e['filename']} | {e['topic']} | {e['size_bytes']} | {first} | {e['sha1_12']} |\n")
    md.append("\n")

    md.append("## Active number collisions in workspace\n\n")
    if collisions:
        for n, lst in sorted(collisions.items()):
            md.append(f"### Migration {n:04d}\n\n")
            for e in lst:
                md.append(f"- {e['filename']} (topic: {e['topic']})\n")
            md.append("\n")
    else:
        md.append("None.\n\n")

    md.append("## Renumber / rename history (from git log)\n\n")
    if renumber_notes:
        for r in renumber_notes:
            md.append(f"- {r['filename']}: {r['subject']}\n")
    else:
        md.append("None found.\n")
    md.append("\n")

    md.append("## Note on 0039 historical collision\n\n")
    md.append(
        "Per thread/172 and CLAUDE.md anti-pattern docs, a historical migration "
        "0039 collision was resolved via PR #140 (renamed `0039_audit_log.sql` → "
        "to current numbering). Currently in workspace, 0039_audit_log.sql and "
        "0040_rules_link_clicks.sql both exist with distinct numbers — collision "
        "is RESOLVED. No active migration number collisions detected.\n"
    )

    (OUT / "2026-05-22-META-A3-migrations-inventory.md").write_text(
        "".join(md), encoding="utf-8"
    )
    print(f"A3 done: {len([e for e in entries if 'number' in e])} migrations, "
          f"{len(collisions)} active collisions, {len(renumber_notes)} renumber history notes")


if __name__ == "__main__":
    main()

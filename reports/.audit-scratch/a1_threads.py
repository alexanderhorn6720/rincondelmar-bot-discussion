"""A1 - Threads inventory. Parses rdm-discussion/threads/*.md."""
from __future__ import annotations
import json, os, re, subprocess, sys
from pathlib import Path
import yaml

REPO = Path("c:/dev/rdm/dev/discussion")
THREADS = REPO / "threads"
OUT = REPO / "reports"

FILENAME_RE = re.compile(r"^(\d{1,3})-([a-z]+(?:-[a-z]+)?)-(.+)\.md$", re.IGNORECASE)


def git_dates(rel_path: str) -> tuple[str | None, str | None]:
    """Return (first_commit_date, last_commit_date) for a file relative to repo."""
    try:
        last = subprocess.check_output(
            ["git", "-C", str(REPO), "log", "-1", "--format=%ai", "--", rel_path],
            text=True, stderr=subprocess.DEVNULL,
        ).strip() or None
        first = subprocess.check_output(
            ["git", "-C", str(REPO), "log", "--diff-filter=A", "--format=%ai",
             "--follow", "--", rel_path],
            text=True, stderr=subprocess.DEVNULL,
        ).strip().splitlines()
        first_date = first[-1] if first else None
        return first_date, last
    except subprocess.CalledProcessError:
        return None, None


def parse_frontmatter(text: str) -> tuple[dict | None, list[str]]:
    """Returns (fm_dict or None, warnings)."""
    warnings: list[str] = []
    if not text.startswith("---"):
        return None, ["no_frontmatter"]
    end = text.find("\n---", 4)
    if end == -1:
        return None, ["unterminated_frontmatter"]
    raw = text[3:end].strip()
    try:
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return None, [f"frontmatter_not_dict:{type(data).__name__}"]
        return data, warnings
    except yaml.YAMLError as e:
        return None, [f"yaml_error:{str(e)[:80]}"]


def parse_legacy(text: str) -> dict:
    """Best-effort legacy parser for non-frontmatter threads."""
    out: dict = {}
    for line in text.splitlines()[:30]:
        m = re.match(r"^\*\*([A-Za-z]+)\*\*:\s*(.+)$", line.strip())
        if m:
            key, val = m.group(1).lower(), m.group(2).strip()
            out[key] = val
    return out


def main() -> None:
    files = sorted(p for p in THREADS.iterdir() if p.suffix == ".md")
    entries: list[dict] = []
    malformed: list[dict] = []
    for p in files:
        rel = f"threads/{p.name}"
        text = p.read_text(encoding="utf-8", errors="replace")
        size = p.stat().st_size
        m = FILENAME_RE.match(p.name)
        if m:
            num_str, author_slug, topic_slug = m.group(1), m.group(2), m.group(3)
        else:
            # try numeric prefix only
            m2 = re.match(r"^(\d{1,3})[-_](.*)\.md$", p.name)
            if m2:
                num_str = m2.group(1)
                rest = m2.group(2)
                parts = rest.split("-", 1)
                author_slug = parts[0]
                topic_slug = parts[1] if len(parts) > 1 else ""
            else:
                num_str = ""
                author_slug = ""
                topic_slug = p.stem
        num = int(num_str) if num_str.isdigit() else None
        fm, fm_warn = parse_frontmatter(text)
        legacy = parse_legacy(text) if fm is None else {}
        first, last = git_dates(rel)
        author = None
        date = None
        topic = None
        mode = None
        status = None
        related = None
        if fm:
            author = fm.get("author")
            date = fm.get("date")
            if isinstance(date, (int, float)):
                date = str(date)
            elif date is not None and not isinstance(date, str):
                date = str(date)
            topic = fm.get("topic")
            mode = fm.get("mode")
            status = fm.get("status")
            related = fm.get("related")
        else:
            author = legacy.get("author")
            date = legacy.get("date")

        entry = {
            "filename": p.name,
            "number": num,
            "author_slug": author_slug,
            "topic_slug": topic_slug,
            "size_bytes": size,
            "git_first_commit": first,
            "git_last_commit": last,
            "frontmatter_present": fm is not None,
            "author": author,
            "date": date,
            "topic": topic,
            "mode": mode,
            "status": status,
            "related_count": len(related) if isinstance(related, list) else (1 if related else 0),
            "warnings": fm_warn,
        }
        entries.append(entry)
        if fm_warn:
            malformed.append({"filename": p.name, "warnings": fm_warn})

    # Aggregate stats
    by_number: dict[int, list[str]] = {}
    for e in entries:
        if e["number"] is not None:
            by_number.setdefault(e["number"], []).append(e["filename"])
    collisions = {n: files for n, files in by_number.items() if len(files) > 1}

    by_author: dict[str, int] = {}
    for e in entries:
        a = (e["author"] or e["author_slug"] or "unknown")
        if isinstance(a, list):
            a = ",".join(str(x) for x in a)
        a = str(a).lower()
        by_author[a] = by_author.get(a, 0) + 1

    by_status: dict[str, int] = {}
    for e in entries:
        s = str(e["status"] or "no-status").lower()
        by_status[s] = by_status.get(s, 0) + 1

    by_mode: dict[str, int] = {}
    for e in entries:
        m = str(e["mode"] or "no-mode").lower()
        by_mode[m] = by_mode.get(m, 0) + 1

    dates = [e["git_first_commit"] for e in entries if e["git_first_commit"]]
    earliest = min(dates) if dates else None
    latest = max(dates) if dates else None

    json_out = {
        "generated_at": "2026-05-22",
        "total": len(entries),
        "earliest_first_commit": earliest,
        "latest_last_commit": latest,
        "collisions_count": len(collisions),
        "collisions": collisions,
        "by_author": by_author,
        "by_status": by_status,
        "by_mode": by_mode,
        "malformed_count": len(malformed),
        "malformed": malformed,
        "entries": entries,
    }

    (OUT / "2026-05-22-META-A1-threads-inventory.json").write_text(
        json.dumps(json_out, indent=2, default=str), encoding="utf-8"
    )

    # MD
    md = []
    md.append("# A1 — Threads inventory\n")
    md.append(f"**Generated**: 2026-05-22 (CC, thread/176)\n")
    md.append(f"**Total threads**: {len(entries)}\n")
    md.append(f"**Date range**: {earliest} → {latest}\n")
    md.append(f"**Frontmatter present**: {sum(1 for e in entries if e['frontmatter_present'])} / {len(entries)}\n")
    md.append(f"**Collisions of number**: {len(collisions)}\n\n")

    md.append("## By author (filename slug)\n\n")
    md.append("| Author | Count |\n|---|---|\n")
    for a, c in sorted(by_author.items(), key=lambda kv: -kv[1]):
        md.append(f"| {a} | {c} |\n")
    md.append("\n")

    md.append("## By mode\n\n")
    md.append("| Mode | Count |\n|---|---|\n")
    for m, c in sorted(by_mode.items(), key=lambda kv: -kv[1]):
        md.append(f"| {m} | {c} |\n")
    md.append("\n")

    md.append("## By status\n\n")
    md.append("| Status | Count |\n|---|---|\n")
    for s, c in sorted(by_status.items(), key=lambda kv: -kv[1]):
        md.append(f"| {s} | {c} |\n")
    md.append("\n")

    md.append("## Numbering collisions\n\n")
    if collisions:
        md.append("| Number | Files |\n|---|---|\n")
        for n, files in sorted(collisions.items()):
            md.append(f"| {n} | {', '.join(files)} |\n")
    else:
        md.append("None detected.\n")
    md.append("\n")

    md.append("## Threads table\n\n")
    md.append("| # | Author | Date | Mode | Status | Size | First commit | Topic |\n")
    md.append("|---|---|---|---|---|---|---|---|\n")
    for e in sorted(entries, key=lambda x: (x["number"] if x["number"] is not None else -1, x["filename"])):
        num_disp = e["number"] if e["number"] is not None else "?"
        topic = (e["topic"] or e["topic_slug"] or "")
        if isinstance(topic, list):
            topic = ",".join(str(x) for x in topic)
        topic = str(topic)[:60]
        author = e["author"] or e["author_slug"] or ""
        if isinstance(author, list):
            author = ",".join(str(x) for x in author)
        author = str(author)[:24]
        date = e["date"] or (e["git_first_commit"] or "")[:10]
        mode = str(e["mode"] or "")[:10]
        status = str(e["status"] or "")[:20]
        first = (e["git_first_commit"] or "")[:10]
        md.append(f"| {num_disp} | {author} | {date} | {mode} | {status} | {e['size_bytes']} | {first} | {topic} |\n")
    md.append("\n")

    md.append("## Frontmatter malformed / missing\n\n")
    if malformed:
        for m in malformed:
            md.append(f"- {m['filename']}: {', '.join(m['warnings'])}\n")
    else:
        md.append("None.\n")
    md.append("\n")

    (OUT / "2026-05-22-META-A1-threads-inventory.md").write_text(
        "".join(md), encoding="utf-8"
    )
    print(f"A1 done: {len(entries)} threads, {len(collisions)} collisions, {len(malformed)} malformed")


if __name__ == "__main__":
    main()

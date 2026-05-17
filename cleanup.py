"""
GE-LAV course site cleanup — comprehensive batch.
Items: 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15
Item 7 (check all hyperlinks) runs at the end as a discovery report.

Usage: place at the root of ~/Downloads/ge-lav-course/ and run with:
    python3 cleanup.py
"""
from pathlib import Path
import re

actions = []

# ============================================================
# Items 9, 10, 11: Strip instructor-facing sections from all session pages.
# Removes any heading section named:
#   - Speaker Notes / Speaker Note
#   - Instructor Notes / Instructor Note
#   - Slide Source / Slide Sources
#   - Slides Needed / New Slides Needed
# A "section" runs from "## Heading" (or "### Heading") to the next heading
# of the same or higher level, or end of file.
# ============================================================
INSTRUCTOR_HEADERS = re.compile(
    r"(?im)^#{2,4}\s+(?:speaker\s*notes?|instructor\s*notes?|slide\s*sources?|"
    r"(?:new\s+)?slides?\s*needed)\s*$"
)


def strip_instructor_sections(text):
    """Remove sections whose heading matches INSTRUCTOR_HEADERS."""
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if INSTRUCTOR_HEADERS.match(line):
            heading_match = re.match(r"^(#+)\s", line)
            level = len(heading_match.group(1))
            i += 1
            while i < len(lines):
                next_line = lines[i]
                next_heading = re.match(r"^(#+)\s", next_line)
                if next_heading and len(next_heading.group(1)) <= level:
                    break
                i += 1
            while out and out[-1].strip() == "":
                out.pop()
            out.append("")
            continue
        out.append(line)
        i += 1
    result = "\n".join(out)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


session_files = list(Path("lectures").glob("session-*.qmd"))
stripped = 0
for p in session_files:
    text = p.read_text()
    new = strip_instructor_sections(text)
    if new != text:
        p.write_text(new)
        stripped += 1
actions.append(f"[9,10,11] Stripped instructor sections from {stripped} session files")

sched = Path("schedule.qmd")
if sched.exists():
    orig = sched.read_text()
    new = strip_instructor_sections(orig)
    if new != orig:
        sched.write_text(new)
        actions.append("[9,10,11] Stripped instructor sections from schedule.qmd")

# ============================================================
# Item 2: schedule.qmd — delete "Slide Reuse Heatmap" / "Slide Reuse Map" section
# ============================================================
if sched.exists():
    text = sched.read_text()

    def remove_heatmap_section(t):
        rx = re.compile(r"(?im)^#{2,4}\s+slide\s*reuse\s*(?:heatmap|map)?\s*$")
        lines = t.split("\n")
        out = []
        i = 0
        while i < len(lines):
            if rx.match(lines[i]):
                level = len(re.match(r"^(#+)", lines[i]).group(1))
                i += 1
                while i < len(lines):
                    h = re.match(r"^(#+)\s", lines[i])
                    if h and len(h.group(1)) <= level:
                        break
                    i += 1
                while out and out[-1].strip() == "":
                    out.pop()
                out.append("")
                continue
            out.append(lines[i])
            i += 1
        return re.sub(r"\n{3,}", "\n\n", "\n".join(out))

    new = remove_heatmap_section(text)
    if new != text:
        sched.write_text(new)
        actions.append("[2] Removed 'Slide Reuse Heatmap' section from schedule.qmd")
        text = new

    # Item 3: Remove blue callout near "GE-LAV Course Timeline"
    lines = text.split("\n")
    timeline_idx = None
    for i, line in enumerate(lines):
        if re.search(r"(?i)ge[-\s]?lav\s+course\s+timeline", line):
            timeline_idx = i
            break
    if timeline_idx is not None:
        end_scan = min(len(lines), timeline_idx + 120)
        block_start, block_end = None, None
        i = timeline_idx
        while i < end_scan:
            if re.match(r"^:::\s*\{\.callout-(note|tip|info)\b", lines[i]):
                block_start = i
                depth = 1
                j = i + 1
                while j < len(lines) and depth > 0:
                    if re.match(r"^:::\s*\{\.callout-", lines[j]):
                        depth += 1
                    elif re.match(r"^:::\s*$", lines[j]):
                        depth -= 1
                    j += 1
                block_end = j - 1
                break
            i += 1
        if block_start is not None and block_end is not None:
            new_lines = lines[:block_start] + lines[block_end + 1:]
            new_text = re.sub(r"\n{3,}", "\n\n", "\n".join(new_lines))
            sched.write_text(new_text)
            actions.append(
                f"[3] Removed blue callout near 'GE-LAV Course Timeline' "
                f"(lines {block_start}-{block_end})"
            )
        else:
            actions.append(
                "[3] NOTE: no callout block found near 'GE-LAV Course Timeline' — "
                "may not exist, please review"
            )

# ============================================================
# Items 4, 5: slides.qmd
# ============================================================
slides_qmd = Path("slides.qmd")
if slides_qmd.exists():
    text = slides_qmd.read_text()
    lines = text.split("\n")
    new_lines = []
    skip_until_next_heading = False
    skip_level = 0
    item5_removed = False
    item4_lines_removed = 0
    for line in lines:
        if skip_until_next_heading:
            h = re.match(r"^(#+)\s", line)
            if h and len(h.group(1)) <= skip_level:
                skip_until_next_heading = False
                new_lines.append(line)
            continue
        if re.match(r"(?i)^#{2,4}\s+notes\s*on\s*the\s*slides?", line):
            h = re.match(r"^(#+)", line)
            skip_level = len(h.group(1))
            skip_until_next_heading = True
            item5_removed = True
            while new_lines and new_lines[-1].strip() == "":
                new_lines.pop()
            new_lines.append("")
            continue
        if re.search(r"(?i)download\s+all\s+decks", line):
            item4_lines_removed += 1
            continue
        new_lines.append(line)
    new_text = re.sub(r"\n{3,}", "\n\n", "\n".join(new_lines))
    if new_text != text:
        slides_qmd.write_text(new_text)
        if item4_lines_removed:
            actions.append(f"[4] Removed {item4_lines_removed} 'Download all decks' line(s) from slides.qmd")
        if item5_removed:
            actions.append("[5] Removed 'Notes on the slides' section from slides.qmd")

zip_path = Path("slides/GE-LAV_Session_Decks.zip")
if zip_path.exists():
    zip_path.unlink()
    actions.append(f"[4] Deleted {zip_path}")

# ============================================================
# Item 6: code.qmd — How to run: keep only Binder
# Item 15: Remove "companion code lives in a public GitHub repo" lines
# ============================================================
code_qmd = Path("code.qmd")
if code_qmd.exists():
    text = code_qmd.read_text()

    # Item 6: Replace the How to run section
    rx = re.compile(r"(##\s+How to run\s*\n)(.*?)(?=\n##\s|\Z)", re.S | re.I)
    m = rx.search(text)
    if m:
        new_section = (
            "## How to run\n\n"
            "[![Binder](https://mybinder.org/badge_logo.svg)]"
            "(https://mybinder.org/v2/gh/drsamirasaf-creator/ge-lav-companion-code/main)\n\n"
            "Click the badge above. Binder launches a free JupyterLab in your "
            "browser with everything pre-installed. First build takes 2-3 "
            "minutes; subsequent visits are 30 seconds.\n\n"
        )
        text = text[:m.start()] + new_section + text[m.end():]
        code_qmd.write_text(text)
        actions.append("[6] Replaced 'How to run' section in code.qmd to retain only Binder option")

    # Item 15: Remove the lines about the public GitHub repo intro
    text = code_qmd.read_text()
    line_pattern = re.compile(
        r"The companion code lives in a public GitHub repo:[^\n]*\n+"
        r"\*\*\[ge-lav-companion-code\][^\n]*\n+",
        re.I,
    )
    new = line_pattern.sub("", text)
    if new != text:
        code_qmd.write_text(new)
        actions.append("[15] Removed 'companion code lives in public repo' lines from code.qmd")

# ============================================================
# Item 8: project-specification.qmd — delete "Solutions" section
# ============================================================
proj_path = Path("project/project-specification.qmd")
if proj_path.exists():
    text = proj_path.read_text()
    lines = text.split("\n")
    out_lines = []
    skip = False
    skip_level = 0
    for line in lines:
        if skip:
            h = re.match(r"^(#+)\s", line)
            if h and len(h.group(1)) <= skip_level:
                skip = False
                out_lines.append(line)
            continue
        if re.match(r"(?i)^#{2,4}\s+(?:\d+(?:\.\d+)*\s+)?solutions?\s*$", line):
            h = re.match(r"^(#+)", line)
            skip_level = len(h.group(1))
            skip = True
            while out_lines and out_lines[-1].strip() == "":
                out_lines.pop()
            out_lines.append("")
            continue
        out_lines.append(line)
    new = re.sub(r"\n{3,}", "\n\n", "\n".join(out_lines))
    if new != text:
        proj_path.write_text(new)
        actions.append("[8] Removed 'Solutions' section from project-specification.qmd")

# ============================================================
# Items 12, 13, 14: Fix broken links in syllabus.qmd
# ============================================================
syl = Path("syllabus.qmd")
if syl.exists():
    text = syl.read_text()
    fixes = 0
    for path in [
        "appendices/B-reading-list.qmd",
        "exams/midterm-blueprint.qmd",
        "project/project-specification.qmd",
    ]:
        old = "](../" + path + ")"
        new = "](" + path + ")"
        if old in text:
            text = text.replace(old, new)
            fixes += 1
    if fixes > 0:
        syl.write_text(text)
        actions.append(f"[12,13,14] Fixed {fixes} broken ../path links in syllabus.qmd")

# ============================================================
# Item 1: Discovery only — find instructor-facing references
# ============================================================
instructor_keywords = re.compile(
    r"(?im)^.*?(?:for\s+the\s+instructor|recommended\s+for\s+instructors|"
    r"instructor:\s|teaching\s+note:|instructor\s+tip:|grading\s+rubric\s+for\s+instructors).*$"
)
candidates = []
for p in Path(".").rglob("*.qmd"):
    if any(part.startswith(".") for part in p.parts):
        continue
    try:
        text = p.read_text()
        for line_idx, line in enumerate(text.split("\n"), 1):
            if instructor_keywords.search(line):
                candidates.append((str(p), line_idx, line.strip()[:100]))
    except Exception:
        continue
actions.append(f"[1] Found {len(candidates)} candidate instructor-facing lines (see below)")

# ============================================================
# Item 7: Hyperlink check — find broken local links across all .qmd files
# ============================================================
broken = []
for p in Path(".").rglob("*.qmd"):
    if any(part.startswith(".") for part in p.parts):
        continue
    try:
        text = p.read_text()
        for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
            if target.startswith("http://") or target.startswith("https://"):
                continue
            if target.startswith("#"):
                continue
            if target.startswith("mailto:"):
                continue
            target_path = target.split("#")[0]
            if not target_path:
                continue
            resolved = (p.parent / target_path).resolve()
            try:
                rel = resolved.relative_to(Path.cwd().resolve())
                if not Path(rel).exists():
                    broken.append((str(p), label, target))
            except ValueError:
                broken.append((str(p), label, target))
    except Exception:
        continue

# ============================================================
# SUMMARY
# ============================================================
print("=" * 70)
print("CLEANUP ACTIONS COMPLETED")
print("=" * 70)
for a in actions:
    print("  " + a)

print()
print("=" * 70)
print(f"ITEM 1 — instructor-facing line candidates ({len(candidates)} total)")
print("=" * 70)
print("Review then delete manually, or paste specific patterns back for follow-up.")
for path, lineno, snippet in candidates[:30]:
    print(f"  {path}:{lineno}  {snippet}")
if len(candidates) > 30:
    print(f"  ... and {len(candidates) - 30} more")

print()
print("=" * 70)
print(f"ITEM 7 — broken local links ({len(broken)} found)")
print("=" * 70)
for entry in broken[:30]:
    print(f"  {entry[0]}: [{entry[1]}]({entry[2]})")
if len(broken) > 30:
    print(f"  ... and {len(broken) - 30} more")

print()
print("Done. NO render or publish yet.")

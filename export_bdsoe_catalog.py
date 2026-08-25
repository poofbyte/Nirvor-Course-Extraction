"""
BDSOE Catalog & Spreadsheet Exporter
====================================
Generates:
  - bdsoe_courses_summary.md (Markdown catalog with class dates, YouTube links, Drive slides)
  - bdsoe_links.csv          (Spreadsheet format)
"""

import csv
import json
import sys
from pathlib import Path

# Ensure UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
BDSOE_DATA_FILE = SCRIPT_DIR / "bdsoe_full_database.json"
OUTPUT_MD = SCRIPT_DIR / "bdsoe_courses_summary.md"
OUTPUT_CSV = SCRIPT_DIR / "bdsoe_links.csv"


def main():
    if not BDSOE_DATA_FILE.exists():
        print(f"[!] {BDSOE_DATA_FILE.name} not found.")
        return

    with open(BDSOE_DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Group by subject and sort chronologically
    subjects: dict[str, list[dict]] = {}
    for item in data:
        sname = item.get("subject_name", "General").strip()
        subjects.setdefault(sname, []).append(item)

    for sname in subjects:
        subjects[sname].sort(key=lambda x: x.get("class_date", ""))

    # 1. Export Markdown
    md_lines = [
        "# BDSOE - Course & Lecture Links Catalog",
        "",
        "> **Note:** All YouTube classes, dates, and Google Drive slide links extracted below.",
        "",
        "---",
        "",
    ]

    for s_idx, (sname, classes) in enumerate(subjects.items(), start=1):
        video_count = sum(1 for c in classes if c.get("youtube_id"))
        slide_count = sum(1 for c in classes if c.get("slide_url"))

        vids = [c["youtube_id"] for c in classes if c.get("youtube_id")]
        
        md_lines.append(f"## {s_idx}. BDSOE - {sname}")
        md_lines.append("")
        md_lines.append(f"- **Total Classes:** {len(classes)}")
        md_lines.append(f"- **Total Videos:** {video_count}")
        md_lines.append(f"- **Total Slide Links:** {slide_count}")
        
        # 1-Click playlist queue link
        if vids:
            chunk_size = 50
            chunks = [vids[i:i + chunk_size] for i in range(0, len(vids), chunk_size)]
            for ch_idx, ch in enumerate(chunks, start=1):
                part_suffix = f" (Part {ch_idx})" if len(chunks) > 1 else ""
                url = f"https://www.youtube.com/watch_videos?video_ids={','.join(ch)}"
                md_lines.append(f"- 🎬 **[Open Playlist Queue on YouTube{part_suffix}]({url})**")
        md_lines.append("")

        for c_idx, c in enumerate(classes, start=1):
            title = c.get("class_name", f"Class {c_idx}").strip()
            date = c.get("class_date", "")
            yurl = c.get("youtube_url", "")
            surl = c.get("slide_url", "")

            date_str = f"`{date}` " if date else ""
            links = []
            if yurl:
                links.append(f"[📺 YouTube Class]({yurl})")
            if surl:
                links.append(f"[📁 Google Drive Slide]({surl})")

            md_lines.append(f"- {date_str}**{title}** — " + " | ".join(links))

        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    OUTPUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"[✓] Saved Markdown -> {OUTPUT_MD.name}")

    # 2. Export CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Subject",
            "Class Name",
            "Class Date",
            "YouTube URL",
            "YouTube Video ID",
            "Google Drive Slide URL",
            "Total Views",
            "Class ID",
            "Subject ID",
        ])
        writer.writeheader()
        for sname, classes in subjects.items():
            for c in classes:
                writer.writerow({
                    "Subject": sname,
                    "Class Name": c.get("class_name", ""),
                    "Class Date": c.get("class_date", ""),
                    "YouTube URL": c.get("youtube_url", ""),
                    "YouTube Video ID": c.get("youtube_id", ""),
                    "Google Drive Slide URL": c.get("slide_url", ""),
                    "Total Views": c.get("total_view", 0),
                    "Class ID": c.get("class_id", ""),
                    "Subject ID": c.get("subject_id", ""),
                })

    print(f"[✓] Saved CSV table -> {OUTPUT_CSV.name} ({len(data)} entries)")


if __name__ == "__main__":
    main()

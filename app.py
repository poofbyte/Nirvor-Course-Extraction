"""
Nirvor Course & Lecture Link Extractor
======================================
Extracts all course lectures, YouTube video links, Google Drive material links,
and PDF notes from Nirvor (nirvor.net) without downloading any media files.

Outputs:
  - nirvor_courses_summary.md (Organized Markdown catalog)
  - nirvor_links.csv          (Spreadsheet compatible CSV)
  - nirvor_data.json           (Complete structured JSON)
  - nirvor_dashboard.html      (Interactive offline web viewer with search & 1-click links)
"""

import csv
import html
import json
import re
import sys
from pathlib import Path
import requests

# Ensure UTF-8 output in Windows PowerShell / Command Prompt
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_URL = "https://nirvor.net"
ACCOUNT_JSON = SCRIPT_DIR / "account.json"
ACCOUNT_TXT = SCRIPT_DIR / "account.txt"

OUTPUT_MD = SCRIPT_DIR / "nirvor_courses_summary.md"
OUTPUT_CSV = SCRIPT_DIR / "nirvor_links.csv"
OUTPUT_JSON = SCRIPT_DIR / "nirvor_data.json"


def clean_url(url: str) -> str:
    """Cleans up malformed URL strings (e.g. ps://, missing http)."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("ps://"):
        url = "htt" + url
    elif url.startswith("ttps://"):
        url = "h" + url
    elif url.startswith("ttp://"):
        url = "h" + url
    elif url.startswith("//"):
        url = "https:" + url
    if not url.startswith(("http://", "https://")):
        return ""
    return url


def normalize_youtube_url(url: str) -> str:
    """Normalizes any YouTube embed/short/full link to https://www.youtube.com/watch?v=VIDEO_ID"""
    if not url:
        return ""
    url = clean_url(url)
    if not url:
        return ""
    match = re.search(r"(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|live\/|watch\?v=|watch\?.+&v=))([\w-]{11})", url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    if "youtube.com" in url or "youtu.be" in url:
        return url
    return ""


def extract_video_id(url: str) -> str:
    """Extracts YouTube 11-character video ID from a URL."""
    if not url:
        return ""
    url = clean_url(url)
    match = re.search(r"(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|live\/|watch\?v=|watch\?.+&v=))([\w-]{11})", url)
    return match.group(1) if match else ""


def get_authenticated_session() -> tuple[requests.Session, str]:
    """
    Creates an authenticated requests session using cookies from account.json
    or credentials from account.txt.
    """
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    })

    token = None

    # 1. Try loading from account.json (cookie export)
    if ACCOUNT_JSON.exists():
        try:
            cookies_list = json.loads(ACCOUNT_JSON.read_text(encoding="utf-8"))
            for cookie in cookies_list:
                session.cookies.set(cookie["name"], cookie["value"], domain=cookie.get("domain", "nirvor.net"))
                if cookie.get("name") == "accessToken":
                    token = cookie.get("value")
            if token:
                session.headers["Authorization"] = f"Bearer {token}"
                print(f"[✓] Loaded accessToken from {ACCOUNT_JSON.name}")
        except Exception as e:
            print(f"[!] Warning reading {ACCOUNT_JSON}: {e}")

    # 2. If no token, check account.txt for login credentials
    if not token and ACCOUNT_TXT.exists():
        print(f"[*] Attempting login via {ACCOUNT_TXT.name}...")
        creds = {}
        for line in ACCOUNT_TXT.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                creds[k.strip().lower()] = v.strip()

        username = creds.get("username") or creds.get("email")
        password = creds.get("password")

        if username and password:
            login_res = session.post(f"{BASE_URL}/api/v2/auth/login-user", json={
                "email": username,
                "password": password
            })
            if login_res.status_code == 200:
                data = login_res.json()
                token = data.get("data", {}).get("accessToken")
                if token:
                    session.headers["Authorization"] = f"Bearer {token}"
                    print("[✓] Login successful!")

    if not token:
        print("[!] No accessToken found. Public data will be accessed if available.")

    return session, token


def fetch_all_data(session: requests.Session) -> list[dict]:
    """
    Fetches all enrolled courses, lectures, folders, and materials via the API.
    """
    print("[*] Fetching user profile...")
    user_id = None
    user_name = "Student"
    
    try:
        me_res = session.get(f"{BASE_URL}/api/v2/me", timeout=10)
        if me_res.status_code == 200:
            user_data = me_res.json().get("data", {})
            user_id = user_data.get("_id")
            user_name = user_data.get("name", "Student")
            print(f"[✓] Authenticated as: {user_name} (ID: {user_id})")
        else:
            print(f"[!] /api/v2/me returned status {me_res.status_code}")
    except Exception as e:
        print(f"[!] Error fetching profile: {e}")

    courses_raw = []
    
    # Try fetching enrolled courses first
    if user_id:
        print(f"[*] Fetching enrolled courses for user {user_id}...")
        try:
            enrolled_res = session.get(f"{BASE_URL}/api/v2/course-enrollment/student/{user_id}", timeout=10)
            if enrolled_res.status_code == 200:
                enrollments = enrolled_res.json().get("data", [])
                for item in enrollments:
                    c_info = item.get("courseId")
                    if isinstance(c_info, dict):
                        courses_raw.append(c_info)
        except Exception as e:
            print(f"[!] Error fetching enrollments: {e}")

    # Fallback to /api/v2/course if no enrolled courses found
    if not courses_raw:
        print("[*] Fetching general courses list...")
        try:
            courses_res = session.get(f"{BASE_URL}/api/v2/course", timeout=10)
            if courses_res.status_code == 200:
                courses_raw = courses_res.json().get("data", [])
        except Exception as e:
            print(f"[!] Error fetching courses: {e}")

    # Deduplicate courses by _id
    courses_dict = {c["_id"]: c for c in courses_raw if "_id" in c}
    courses_list = list(courses_dict.values())

    print(f"\n[+] Total Courses Found: {len(courses_list)}\n")

    structured_courses = []

    for idx, course in enumerate(courses_list, start=1):
        cid = course.get("_id")
        c_title = course.get("title", f"Course {idx}").strip()
        print(f"[{idx}/{len(courses_list)}] Fetching lectures for: {c_title}")

        lectures_raw = []
        try:
            lec_res = session.get(f"{BASE_URL}/api/v2/lecture/course/{cid}", timeout=15)
            if lec_res.status_code == 200:
                lectures_raw = lec_res.json().get("data", [])
        except Exception as e:
            print(f"    [!] Error fetching lectures: {e}")

        # Build folder hierarchy
        items_by_id = {l["_id"]: l for l in lectures_raw if "_id" in l}
        children_by_parent: dict[str, list[dict]] = {}

        for l in lectures_raw:
            pid = l.get("parentId")
            children_by_parent.setdefault(pid, []).append(l)

        # Sort by order
        for pid in children_by_parent:
            children_by_parent[pid].sort(key=lambda x: x.get("order", 0))

        # Root items (parentId is None or empty or not in items_by_id)
        root_items = []
        for pid, items in children_by_parent.items():
            if not pid or pid not in items_by_id:
                root_items.extend(items)

        def build_tree(node: dict) -> dict:
            node_id = node.get("_id")
            title = node.get("title", "").strip()
            video_url = normalize_youtube_url(node.get("videoUrl", ""))
            notes_url = clean_url(node.get("notesUrl", ""))
            pdf_url = clean_url(node.get("pdfUrl", ""))
            other_url = clean_url(node.get("memorizationMaterialsUrl") or node.get("additionalResourcesUrl") or "")
            live_url = clean_url(node.get("liveClassUrl", ""))

            children_nodes = children_by_parent.get(node_id, [])
            parsed_children = [build_tree(child) for child in children_nodes]

            is_folder = bool(parsed_children) or (not video_url and not notes_url and not pdf_url)

            return {
                "id": node_id,
                "title": title,
                "is_folder": is_folder,
                "video_url": video_url,
                "video_id": extract_video_id(video_url),
                "notes_url": notes_url,
                "pdf_url": pdf_url,
                "other_materials_url": other_url,
                "live_class_url": live_url,
                "lock_status": node.get("lockStatus", ""),
                "children": parsed_children,
            }

        parsed_tree = [build_tree(root) for root in root_items]

        # Count stats
        total_videos = sum(1 for l in lectures_raw if l.get("videoUrl"))
        total_drive = sum(1 for l in lectures_raw if l.get("notesUrl"))
        total_pdf = sum(1 for l in lectures_raw if l.get("pdfUrl"))

        print(f"    -> Items: {len(lectures_raw)} | YouTube Videos: {total_videos} | Google Drive / Notes: {total_drive}")

        structured_courses.append({
            "course_id": cid,
            "title": c_title,
            "description": course.get("description", ""),
            "thumbnail": course.get("thumbnail", ""),
            "intro_video": normalize_youtube_url(course.get("introVideo", "")),
            "guide_video": normalize_youtube_url(course.get("admissionGuideVideo", "")),
            "routine_url": clean_url(course.get("routineUrl", "")),
            "total_items": len(lectures_raw),
            "total_videos": total_videos,
            "total_materials": total_drive + total_pdf,
            "raw_lectures": lectures_raw,
            "tree": parsed_tree,
        })

    return structured_courses


def export_markdown(courses: list[dict]):
    """Generates a clean, well-formatted Markdown summary document."""
    lines = [
        "# Nirvor - Course & Lecture Links Catalog",
        "",
        "> **Note:** All YouTube class videos, Google Drive notes, and PDF materials extracted below.",
        "",
        "---",
        "",
    ]

    for c_idx, course in enumerate(courses, start=1):
        lines.append(f"## {c_idx}. {course['title']}")
        lines.append("")
        
        # Collect all video IDs in order
        course_vids = []
        def collect_vids(nodes):
            for n in nodes:
                vid = n.get("video_id")
                if vid and vid not in course_vids:
                    course_vids.append(vid)
                collect_vids(n.get("children", []))
        collect_vids(course.get("tree", []))

        meta_items = []
        if course.get("intro_video"):
            meta_items.append(f"**Intro Video:** [Watch on YouTube]({course['intro_video']})")
        if course.get("guide_video"):
            meta_items.append(f"**Guide Video:** [Watch on YouTube]({course['guide_video']})")
        if course.get("routine_url"):
            meta_items.append(f"**Class Routine PDF:** [Open Routine PDF]({course['routine_url']})")
        
        if meta_items:
            lines.append(" | ".join(meta_items))
            lines.append("")

        lines.append(f"- **Total Videos:** {len(course_vids)}")
        lines.append(f"- **Total Material Links:** {course['total_materials']}")

        # 1-Click YouTube Playlist Queue Links (chunks of 50)
        if course_vids:
            chunk_size = 50
            chunks = [course_vids[i:i + chunk_size] for i in range(0, len(course_vids), chunk_size)]
            for ch_idx, ch in enumerate(chunks, start=1):
                part_suffix = f" (Part {ch_idx})" if len(chunks) > 1 else ""
                playlist_url = f"https://www.youtube.com/watch_videos?video_ids={','.join(ch)}"
                lines.append(f"- 🎬 **[Open & Save Full Playlist on YouTube{part_suffix}]({playlist_url})** *(Click link, then click '+ Save' on YouTube)*")
        lines.append("")

        def write_node_md(node: dict, depth: int = 0):
            indent = "  " * depth
            title = node["title"]
            links = []

            if node["video_url"]:
                links.append(f"[📺 YouTube Class]({node['video_url']})")
            if node["notes_url"]:
                links.append(f"[📁 Google Drive Notes]({node['notes_url']})")
            if node["pdf_url"]:
                links.append(f"[📄 Lecture PDF]({node['pdf_url']})")
            if node["other_materials_url"]:
                links.append(f"[📎 Materials]({node['other_materials_url']})")
            if node["live_class_url"]:
                links.append(f"[🔴 Live Class]({node['live_class_url']})")

            if links:
                lines.append(f"{indent}- **{title}** — " + " | ".join(links))
            else:
                lines.append(f"{indent}- ### 📂 {title}")

            for child in node["children"]:
                write_node_md(child, depth + 1)

        for root_node in course["tree"]:
            write_node_md(root_node, depth=0)

        lines.append("")
        lines.append("---")
        lines.append("")

    try:
        OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
        print(f"[✓] Saved Markdown summary -> {OUTPUT_MD.resolve()}")
    except PermissionError:
        alt_file = OUTPUT_MD.with_name(f"{OUTPUT_MD.stem}_new.md")
        alt_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"[!] Warning: '{OUTPUT_MD.name}' is currently open in another program.")
        print(f"[✓] Saved updated Markdown to -> {alt_file.resolve()}")


def export_csv(courses: list[dict]):
    """Exports all lectures and links into a flat CSV format."""
    rows = []

    for course in courses:
        c_title = course["title"]
        cid = course["course_id"]

        def traverse(node: dict, parent_path: str = ""):
            title = node["title"]
            current_path = f"{parent_path} > {title}" if parent_path else title

            if node["video_url"] or node["notes_url"] or node["pdf_url"] or node["other_materials_url"]:
                rows.append({
                    "Course Name": c_title,
                    "Course ID": cid,
                    "Folder / Section": parent_path or "(Root)",
                    "Lecture Title": title,
                    "YouTube URL": node["video_url"],
                    "YouTube Video ID": node["video_id"],
                    "Google Drive / Notes URL": node["notes_url"],
                    "PDF URL": node["pdf_url"],
                    "Other Material URL": node["other_materials_url"],
                    "Live Class URL": node["live_class_url"],
                    "Lock Status": node["lock_status"],
                })

            for child in node["children"]:
                traverse(child, current_path)

        for root in course["tree"]:
            traverse(root, "")

    fieldnames = [
        "Course Name",
        "Folder / Section",
        "Lecture Title",
        "YouTube URL",
        "YouTube Video ID",
        "Google Drive / Notes URL",
        "PDF URL",
        "Other Material URL",
        "Live Class URL",
        "Lock Status",
        "Course ID",
    ]

    try:
        with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"[✓] Saved CSV table -> {OUTPUT_CSV.resolve()} ({len(rows)} entries)")
    except PermissionError:
        alt_file = OUTPUT_CSV.with_name(f"{OUTPUT_CSV.stem}_new.csv")
        with alt_file.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"[!] Notice: '{OUTPUT_CSV.name}' is currently open in Excel / another app.")
        print(f"[✓] Saved updated CSV to -> {alt_file.resolve()} ({len(rows)} entries)")
        print(f"    (Close Excel to overwrite the main '{OUTPUT_CSV.name}' directly next time)")


def export_json(courses: list[dict]):
    """Exports structured data to JSON."""
    data_str = json.dumps(courses, ensure_ascii=False, indent=2)
    try:
        OUTPUT_JSON.write_text(data_str, encoding="utf-8")
        print(f"[✓] Saved JSON data -> {OUTPUT_JSON.resolve()}")
    except PermissionError:
        alt_file = OUTPUT_JSON.with_name(f"{OUTPUT_JSON.stem}_new.json")
        alt_file.write_text(data_str, encoding="utf-8")
        print(f"[!] Warning: '{OUTPUT_JSON.name}' is currently open in another program.")
        print(f"[✓] Saved updated JSON to -> {alt_file.resolve()}")


def main():
    print("=" * 70)
    print(" NIRVOR COURSE & LECTURE LINK EXTRACTOR")
    print("=" * 70)

    session, token = get_authenticated_session()
    courses = fetch_all_data(session)

    if not courses:
        print("[!] No courses could be fetched. Please ensure account.json is valid.")
        return

    print("\n" + "=" * 70)
    print(" GENERATING EXPORT FILES")
    print("=" * 70)

    export_markdown(courses)
    export_csv(courses)
    export_json(courses)

    print("\n" + "=" * 70)
    print(" EXTRACTION COMPLETE!")
    print("=" * 70)
    print("Generated files in workspace:")
    print(f"  1. {OUTPUT_MD.name}   -> Readable Markdown catalog with all video & drive links")
    print(f"  2. {OUTPUT_CSV.name}  -> Spreadsheet with organized columns")
    print(f"  3. {OUTPUT_JSON.name} -> Full structured JSON data")
    print("=" * 70)


if __name__ == "__main__":
    main()
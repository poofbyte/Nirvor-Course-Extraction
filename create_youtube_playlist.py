"""
YouTube Course & BDSOE Playlist Creator
========================================
Automatically creates complete YouTube playlists for your Nirvor courses
and BDSOE subjects (Bangla, English, GK, Math & IQ, Guideline) using your
youtube_cookies.json.

No browser windows, no login popups — creates playlists in seconds!
"""

import hashlib
import json
import re
import sys
import time
from pathlib import Path
import requests

# Ensure UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SCRIPT_DIR = Path(__file__).resolve().parent
NIRVOR_DATA_FILE = SCRIPT_DIR / "nirvor_data.json"
BDSOE_DATA_FILE = SCRIPT_DIR / "bdsoe_full_database.json"
COOKIE_FILE = SCRIPT_DIR / "youtube_cookies.json"


def load_nirvor_courses() -> list[dict]:
    if not NIRVOR_DATA_FILE.exists():
        return []
    try:
        with open(NIRVOR_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] Warning loading {NIRVOR_DATA_FILE.name}: {e}")
        return []


def get_nirvor_course_videos(course: dict) -> list[dict]:
    """Collects all videos in hierarchical order from a Nirvor course."""
    videos = []
    seen_ids = set()

    def collect(nodes, parent_path=""):
        for node in nodes:
            title = node.get("title", "").strip()
            vid = node.get("video_id", "").strip()
            vurl = node.get("video_url", "").strip()
            path = f"{parent_path} > {title}" if parent_path else title

            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                videos.append({
                    "title": title,
                    "video_id": vid,
                    "video_url": vurl or f"https://www.youtube.com/watch?v={vid}",
                    "section": parent_path,
                })

            collect(node.get("children", []), path)

    collect(course.get("tree", []))
    return videos


def load_bdsoe_subjects() -> dict[str, list[dict]]:
    """Loads and groups BDSOE classes by subject, sorted chronologically."""
    if not BDSOE_DATA_FILE.exists():
        return {}
    try:
        with open(BDSOE_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        subjects: dict[str, list[dict]] = {}
        for item in data:
            sname = item.get("subject_name", "General").strip()
            if sname not in subjects:
                subjects[sname] = []
            
            vid = item.get("youtube_id", "").strip()
            if vid:
                subjects[sname].append({
                    "title": item.get("class_name", "").strip(),
                    "video_id": vid,
                    "video_url": item.get("youtube_url") or f"https://www.youtube.com/watch?v={vid}",
                    "class_date": item.get("class_date") or "",
                    "slide_url": item.get("slide_url") or "",
                    "total_view": item.get("total_view", 0),
                })
        
        # Sort classes chronologically (oldest date first -> Class 01 first)
        for sname in subjects:
            subjects[sname].sort(key=lambda x: x.get("class_date", ""))
            
        return subjects
    except Exception as e:
        print(f"[!] Warning loading {BDSOE_DATA_FILE.name}: {e}")
        return {}


def load_youtube_session() -> tuple[requests.Session, dict]:
    """Loads YouTube cookies from youtube_cookies.json and prepares authentication headers."""
    if not COOKIE_FILE.exists():
        print(f"\n[!] Missing {COOKIE_FILE.name} in project folder.")
        print("Please export your YouTube cookies from your browser into 'youtube_cookies.json'.")
        sys.exit(1)

    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        cookies_list = json.load(f)

    session = requests.Session()
    sapisid = None

    for c in cookies_list:
        name = c["name"]
        val = c["value"]
        domain = c.get("domain", ".youtube.com")
        session.cookies.set(name, val, domain=domain)
        if name in ["SAPISID", "__Secure-3PAPISID", "__Secure-1PAPISID"]:
            sapisid = val

    if not sapisid:
        print("[!] Warning: SAPISID cookie not found in youtube_cookies.json. Authentication may fail.")

    timestamp = str(int(time.time()))
    origin = "https://www.youtube.com"
    data_str = f"{timestamp} {sapisid or ''} {origin}"
    sha1_hash = hashlib.sha1(data_str.encode("utf-8")).hexdigest()
    auth_header = f"SAPISIDHASH {timestamp}_{sha1_hash}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": origin,
        "X-Origin": origin,
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "X-Youtube-Client-Name": "1",
        "X-Youtube-Client-Version": "2.20240101.01.00",
    }

    return session, headers


def create_youtube_playlist(session: requests.Session, headers: dict, title: str, video_ids: list[str], privacy: str = "PRIVATE") -> str | None:
    """
    Creates a YouTube playlist with the given title and all video IDs in a single operation.
    """
    url = "https://www.youtube.com/youtubei/v1/playlist/create"

    initial_vids = video_ids[:100]
    remaining_vids = video_ids[100:]

    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20240101.01.00",
                "hl": "en",
                "gl": "US"
            }
        },
        "title": title,
        "privacyStatus": privacy,
        "videoIds": initial_vids
    }

    try:
        r = session.post(url, json=payload, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            playlist_id = data.get("playlistId")
            if playlist_id:
                if remaining_vids:
                    add_remaining_videos(session, headers, playlist_id, remaining_vids)
                return playlist_id
            else:
                print(f"    [!] Error response from YouTube: {data}")
        else:
            print(f"    [!] HTTP {r.status_code} creating playlist: {r.text[:200]}")
    except Exception as e:
        print(f"    [!] Exception creating playlist: {e}")

    return None


def add_remaining_videos(session: requests.Session, headers: dict, playlist_id: str, video_ids: list[str]):
    """Appends extra videos to the playlist in batches of 50."""
    url = "https://www.youtube.com/youtubei/v1/browse/edit_playlist"
    chunk_size = 50
    for i in range(0, len(video_ids), chunk_size):
        chunk = video_ids[i:i + chunk_size]
        actions = [{"action": "ACTION_ADD_VIDEO", "addedVideoId": vid} for vid in chunk]
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20240101.01.00",
                    "hl": "en",
                    "gl": "US"
                }
            },
            "playlistId": playlist_id,
            "actions": actions
        }
        try:
            session.post(url, json=payload, headers=headers, timeout=15)
        except Exception as e:
            print(f"    [!] Error adding video chunk: {e}")


def main():
    print("=" * 75)
    print(" NIRVOR & BDSOE -> YOUTUBE PLAYLIST CREATOR (Instant Cookie Mode)")
    print("=" * 75)

    nirvor_courses = load_nirvor_courses()
    bdsoe_subjects = load_bdsoe_subjects()
    session, headers = load_youtube_session()
    print(f"[✓] Authenticated via YouTube cookies ({COOKIE_FILE.name})\n")

    menu_map = {}
    idx = 1

    # 1. Nirvor Courses
    if nirvor_courses:
        print("📁 NIRVOR COURSES:")
        for c in nirvor_courses:
            vids = get_nirvor_course_videos(c)
            key = str(idx)
            menu_map[key] = {
                "type": "nirvor",
                "title": c.get("title", f"Course {idx}").strip(),
                "videos": [v["video_id"] for v in vids],
                "count": len(vids),
            }
            print(f"  [{key}] {menu_map[key]['title']} ({len(vids)} videos)")
            idx += 1
        print(f"  [NA] All Nirvor Courses ({len(nirvor_courses)} playlists)\n")

    # 2. BDSOE Subjects
    if bdsoe_subjects:
        print("📁 BDSOE DATABASE (By Subject):")
        bd_keys = []
        for sname, classes in bdsoe_subjects.items():
            key = f"B{len(bd_keys) + 1}"
            bd_keys.append(key)
            pl_title = f"BDSOE - {sname}"
            menu_map[key.lower()] = {
                "type": "bdsoe",
                "title": pl_title,
                "videos": [c["video_id"] for c in classes],
                "count": len(classes),
            }
            print(f"  [{key}] {pl_title} ({len(classes)} classes)")
        print(f"  [BA] All BDSOE Subjects ({len(bdsoe_subjects)} playlists)\n")

    print("⚡ BATCH OPTIONS:")
    print("  [ALL] Create ALL Playlists (Both Nirvor & BDSOE)")
    print("  [Q]   Quit")
    print("-" * 75)

    choice = input("\nEnter choice (e.g. 1, 3, B1, B2, NA, BA, ALL): ").strip().lower()

    if choice == "q":
        return

    playlists_to_create = []

    if choice == "all":
        # All Nirvor + All BDSOE
        for k, item in menu_map.items():
            playlists_to_create.append((item["title"], item["videos"]))
    elif choice in ["na", "a"]:
        # All Nirvor
        for k, item in menu_map.items():
            if item["type"] == "nirvor":
                playlists_to_create.append((item["title"], item["videos"]))
    elif choice == "ba":
        # All BDSOE
        for k, item in menu_map.items():
            if item["type"] == "bdsoe":
                playlists_to_create.append((item["title"], item["videos"]))
    elif choice in menu_map:
        item = menu_map[choice]
        playlists_to_create.append((item["title"], item["videos"]))
    else:
        print("[!] Invalid selection.")
        return

    print("\n" + "=" * 75)
    print(f" CREATING {len(playlists_to_create)} PLAYLIST(S) ON YOUTUBE")
    print("=" * 75)

    success_count = 0
    for title, vids in playlists_to_create:
        print(f"\n[*] Creating playlist: '{title}'")
        print(f"    Total videos: {len(vids)}")

        if not vids:
            print("    [!] No videos found. Skipping.")
            continue

        playlist_id = create_youtube_playlist(session, headers, title, vids, privacy="PRIVATE")

        if playlist_id:
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            print(f"    [🎉 SUCCESS!] Playlist Created!")
            print(f"    Playlist ID : {playlist_id}")
            print(f"    Direct URL  : {playlist_url}")
            success_count += 1
        else:
            print(f"    [✗] Failed to create playlist for '{title}'")

    print("\n" + "=" * 75)
    print(f" COMPLETED! {success_count}/{len(playlists_to_create)} Playlists Created Successfully.")
    print(" Check your YouTube Library: https://www.youtube.com/feed/playlists")
    print("=" * 75)


if __name__ == "__main__":
    main()

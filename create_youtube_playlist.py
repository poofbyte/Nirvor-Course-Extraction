"""
YouTube Course Playlist Creator
================================
Automatically creates complete YouTube playlists for your Nirvor courses
and adds ALL videos (100% of all lectures) to your YouTube account instantly
using your youtube_cookies.json.

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
DATA_FILE = SCRIPT_DIR / "nirvor_data.json"
COOKIE_FILE = SCRIPT_DIR / "youtube_cookies.json"


def load_courses() -> list[dict]:
    if not DATA_FILE.exists():
        print(f"[!] {DATA_FILE.name} not found. Please run 'python app.py' first.")
        sys.exit(1)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_course_videos(course: dict) -> list[dict]:
    """Collects all videos in hierarchical order from a course."""
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

    # We can pass up to 100 video IDs on creation, and add any remainder via edit_playlist
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
                # If there are more than 100 videos, add the remaining in batches
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
    print("=" * 70)
    print(" NIRVOR -> YOUTUBE PLAYLIST CREATOR (Instant Cookie Mode)")
    print("=" * 70)

    courses = load_courses()
    session, headers = load_youtube_session()
    print(f"[✓] Loaded YouTube cookies from {COOKIE_FILE.name}\n")

    print("Select a course to create a full YouTube playlist for:\n")
    for i, c in enumerate(courses, start=1):
        vids = get_course_videos(c)
        print(f"  [{i}] {c.get('title')} ({len(vids)} videos)")

    print(f"  [A] All Courses (Create playlists for all {len(courses)} courses)")
    print(f"  [Q] Quit")
    print("-" * 70)

    choice = input("\nEnter choice (1-5 or A): ").strip()

    if choice.lower() == "q":
        return

    selected_courses = []
    if choice.lower() == "a":
        selected_courses = courses
    elif choice.isdigit() and 1 <= int(choice) <= len(courses):
        selected_courses = [courses[int(choice) - 1]]
    else:
        print("[!] Invalid selection.")
        return

    print("\n" + "=" * 70)
    print(" CREATING PLAYLISTS ON YOUTUBE")
    print("=" * 70)

    for c in selected_courses:
        title = c.get("title", "Course Playlist").strip()
        videos = get_course_videos(c)
        vid_ids = [v["video_id"] for v in videos]

        print(f"\n[*] Creating playlist for: {title}")
        print(f"    Total videos to include: {len(vid_ids)}")

        if not vid_ids:
            print("    [!] No videos found in this course. Skipping.")
            continue

        playlist_id = create_youtube_playlist(session, headers, title, vid_ids, privacy="PRIVATE")

        if playlist_id:
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            print(f"    [🎉 SUCCESS!] Playlist Created!")
            print(f"    Playlist ID : {playlist_id}")
            print(f"    Direct URL  : {playlist_url}")
        else:
            print(f"    [✗] Failed to create playlist for {title}")

    print("\n" + "=" * 70)
    print(" DONE! Check all your playlists at: https://www.youtube.com/feed/playlists")
    print("=" * 70)


if __name__ == "__main__":
    main()

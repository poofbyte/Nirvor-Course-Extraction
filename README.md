# 🎓 Nirvor Course & YouTube Playlist Toolkit

A high-performance Python toolkit to extract course lectures, YouTube class links, and Google Drive materials from **Nirvor (nirvor.net)**, and automatically save them into **complete YouTube playlists** on your YouTube account.

---

## ⚡ Key Features

1. **Fast Course Link Extractor (`app.py`)**:
   - **Direct REST API Access:** Queries Nirvor's internal API (`/api/v2/lecture/course/...`) directly using your session token.
   - **Extracts All Resources:** Grabs YouTube class videos, Google Drive notes/folders, lecture sheet PDFs, and live class links.
   - **Clean Output Formats:** Generates:
     - `nirvor_courses_summary.md` (Organized Markdown catalog)
     - `nirvor_links.csv` (Spreadsheet with 180+ lectures, ready for Excel/Google Sheets)
     - `nirvor_data.json` (Complete structured JSON data)
   - **Zero Disk Downloads:** Only extracts and organizes links; downloads no media files.

2. **1-Click YouTube Playlist Creator (`create_youtube_playlist.py`)**:
   - **Cookie-Based Instant API:** Uses `youtube_cookies.json` to authenticate silently with YouTube's internal API.
   - **No Browser Popups:** Creates playlists and adds all videos in seconds in the background.
   - **100% Complete Playlists:** Adds all 20, 50, 100+ videos in exact curriculum order under the course title.

---

## 📁 Project Structure

```text
├── app.py                      # Course and lecture link extractor
├── create_youtube_playlist.py  # Automated YouTube playlist creator
├── nirvor_courses_summary.md   # Generated Markdown catalog
├── nirvor_links.csv            # Generated CSV spreadsheet
├── nirvor_data.json            # Generated raw JSON data
├── account.json                # [Ignored] Nirvor session cookies
├── youtube_cookies.json        # [Ignored] YouTube session cookies
├── .gitignore                  # Keeps your credentials safe
└── README.md                   # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
Install Python (3.10+) and required dependencies:
```bash
pip install requests
```

### 2. Configuration & Authentication
Place your exported cookies in the project directory:
* **`account.json`**: Exported cookies from your logged-in browser session on `nirvor.net`.
* **`youtube_cookies.json`**: Exported cookies from your logged-in browser session on `youtube.com`.

> 🔒 **Security Note:** Both `account.json` and `youtube_cookies.json` are listed in `.gitignore` and are **never committed or pushed to Git**.

---

## 📖 Usage Guide

### Step 1: Extract All Course Links
Run:
```bash
python app.py
```
* Queries Nirvor live database.
* Generates `nirvor_courses_summary.md`, `nirvor_links.csv`, and `nirvor_data.json`.
* Re-run anytime new lectures or courses are added to automatically update your files.

### Step 2: Create YouTube Playlists
Run:
```bash
python create_youtube_playlist.py
```
* Displays an interactive menu of all your enrolled courses.
* Choose a specific course number (e.g. `3` for *Only BUP Course*) or type `A` for all courses.
* The script instantly creates the playlist(s) and adds all lecture videos directly into your YouTube library.
* Check your playlists at [youtube.com/feed/playlists](https://www.youtube.com/feed/playlists).

---

## 🛡️ License & Disclaimer
This tool is for personal study organization only. All video and lecture content belongs to the respective instructors and course providers on Nirvor.

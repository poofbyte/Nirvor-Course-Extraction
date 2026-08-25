# 🎓 Nirvor & BDSOE Course / YouTube Playlist Toolkit

A high-performance Python toolkit to extract course lectures, YouTube class links, and Google Drive materials from **Nirvor (nirvor.net)** and **BDSOE**, and automatically save them into **complete YouTube playlists** on your YouTube account.

---

## ⚡ Key Features

1. **Course Link Extractor (`app.py`)**:
   - **Direct REST API Access:** Queries Nirvor's internal API (`/api/v2/lecture/course/...`) directly using your session token.
   - **Extracts All Resources:** Grabs YouTube class videos, Google Drive notes/folders, lecture sheet PDFs, and live class links.
   - **Clean Output Formats:** Generates:
     - `nirvor_courses_summary.md` (Organized Markdown catalog)
     - `nirvor_links.csv` (Spreadsheet with 180+ lectures, ready for Excel/Google Sheets)
     - `nirvor_data.json` (Complete structured JSON data)
   - **Zero Disk Downloads:** Only extracts and organizes links; downloads no media files.

2. **1-Click YouTube Playlist Creator (`create_youtube_playlist.py`)**:
   - **Supports Both Nirvor & BDSOE:** Create playlists for Nirvor courses or BDSOE subjects (Bangla, English, GK, Math & IQ, Guideline).
   - **Cookie-Based Instant API:** Uses `youtube_cookies.json` to authenticate silently with YouTube's internal API.
   - **No Browser Popups:** Creates playlists and adds all videos in seconds in the background.
   - **100% Complete Playlists:** Adds all 20, 50, 100+ videos in exact curriculum order under the course title.

3. **BDSOE Catalog Exporter (`export_bdsoe_catalog.py`)**:
   - Generates `bdsoe_courses_summary.md` and `bdsoe_links.csv` from `bdsoe_full_database.json` with class dates, YouTube links, and Google Drive slide URLs.

---

## 📁 Project Structure

```text
├── app.py                      # Nirvor course & lecture link extractor
├── create_youtube_playlist.py  # Unified YouTube playlist creator (Nirvor & BDSOE)
├── export_bdsoe_catalog.py     # BDSOE Markdown & CSV exporter
├── bdsoe_full_database.json    # BDSOE classes database (Bangla, English, GK, Math & IQ)
├── bdsoe_courses_summary.md    # Generated BDSOE Markdown catalog
├── bdsoe_links.csv             # Generated BDSOE CSV spreadsheet
├── nirvor_courses_summary.md   # Generated Nirvor Markdown catalog
├── nirvor_links.csv            # Generated Nirvor CSV spreadsheet
├── nirvor_data.json            # Generated Nirvor raw JSON data
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

### 🎬 Create YouTube Playlists (Nirvor & BDSOE)
Run:
```bash
python create_youtube_playlist.py
```
* **Nirvor Courses:** Select `1`–`5`, or `NA` for all Nirvor courses.
* **BDSOE Subjects:**
  * `B1` — **BDSOE - Bangla** (61 classes)
  * `B2` — **BDSOE - English** (63 classes)
  * `B3` — **BDSOE - General Knowledge (GK)** (57 classes)
  * `B4` — **BDSOE - Math and IQ** (11 classes)
  * `B5` — **BDSOE - Guideline** (4 classes)
  * `BA` — **All BDSOE Subjects** (creates separate playlists for each subject)
* **Batch Option:** `ALL` to create playlists for all Nirvor and BDSOE courses at once.

---

## 🛡️ License & Disclaimer
This tool is for personal study organization only. All video and lecture content belongs to the respective instructors and course providers.

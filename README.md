# Nirvor Course & Playlist Toolkit

A fast Python tool suite for extracting course lectures, YouTube class links, and Google Drive materials from Nirvor, and automatically saving them into YouTube playlists.

## Features

1. **Course Link Extractor (`app.py`)**:
   - Queries Nirvor's internal API to fetch all enrolled courses, folders, and lectures in under 5 seconds.
   - Extracts all YouTube video URLs, Google Drive notes, and PDF materials.
   - Generates structured Markdown (`nirvor_courses_summary.md`), CSV spreadsheet (`nirvor_links.csv`), and JSON (`nirvor_data.json`).
   - Zero media downloads to the computer.

2. **YouTube Playlist Creator (`create_youtube_playlist.py`)**:
   - Uses your `youtube_cookies.json` to automatically create complete YouTube playlists for any selected course.
   - Adds 100% of all lectures/videos in exact order into your YouTube library.
   - No browser popups or manual login needed.

## Setup & Usage

### 1. Requirements
```bash
pip install requests
```

### 2. Authentication
- Place your exported Nirvor cookies in `account.json`.
- Place your exported YouTube cookies in `youtube_cookies.json`.

*(Note: Cookies and credentials are automatically ignored by `.gitignore` and never committed).*

### 3. Extract Links
```bash
python app.py
```

### 4. Create YouTube Playlists
```bash
python create_youtube_playlist.py
```
Select the course number to automatically create the playlist on your YouTube account.

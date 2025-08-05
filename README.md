# StreamDownloader
Universal Media Downloader
=========================

A simple Windows app to download audio and video from YouTube, Spotify, SoundCloud, Bandcamp, and more.  
Supports playlists, queues, multiple formats (mp3, mp4, wav, etc), and tracks which sites work or not for you.

---

How To Use
----------

1. Install Python 3.9 or newer from https://python.org/
   - When installing, make sure to check the box to "Add Python to PATH"

2. Install required Python packages.
   Open Command Prompt and run:
      pip pip install yt-dlp spotdl requests tk

3. Run the script:
      python downloader.py

4. Use the app:
   - Choose "Audio" or "Video" mode.
   - Paste a YouTube, Spotify, or other supported link.
   - Select the output format (MP3, MP4, etc).
   - Click "Queue Download".
   - Downloads are saved in the "downloads" folder next to the script.

Other Info
----------

- "View Supported Sites" shows a list of domains that have worked/failed for you.
- Playlist links will auto-queue each track/video.
- The terminal panel shows download progress and messages.

Troubleshooting
---------------

- For Spotify, make sure spotdl is installed with: pip install spotdl
- Not all sites are supported. Failed sites are shown in the "invalid sites" list.

---

Enjoy!

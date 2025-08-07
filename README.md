# StreamDownloader  
**Universal Media Downloader**

---

A user-friendly Windows app to download **audio and video** from:

- YouTube  
- Spotify  
- SoundCloud  
- Bandcamp  
- and more...

Supports **playlists**, **format selection (MP3, MP4, WAV, etc.)**, **dynamic site status tracking**, and **auto-parsing Spotify playlists**.

---

## ✅ Features

- Audio/Video downloads from many platforms  
- Multiple format choices (MP3, MP4, WAV, MKV, etc.)  
- Automatically extracts playlists (YouTube/Spotify)  
- Warns about sites that don’t work  
- Dynamic queue system  
- Embedded terminal log  
- GUI with theme-aware layout  
- Auto-generates videos from audio-only sources  
- Works offline (except for the actual downloads 😅)

---

## 🚀 How to Use

1. **Install Python 3.9+**  
   Get it from: [https://python.org](https://python.org)  
   ✅ Make sure to check **"Add Python to PATH"** during install!

2. **Install dependencies**  
   Open a terminal (Command Prompt) and run:
   ```bash
   pip install yt-dlp spotdl requests tk
   ```

4. **Run the app**  
   ```bash
   python downloader.py
   ```

---

## 🧠 Using the App

1. Launch the app (`python downloader.py`)  
2. Choose between **Audio** or **Video** mode  
3. Paste a link (YouTube, Spotify, etc.)  
4. Select desired output format  
5. Click **Queue Download**  
6. Downloads go to the `/downloads/audio` or `/downloads/video` folder

---

## 🎵 Spotify Support

- Paste any **Spotify track, album, or playlist**  
- The app uses `spotdl` to auto-download each track from YouTube  
- All songs are queued automatically with correct titles

---

## 📑 Dynamic Site List

- The app tracks which **domains work** or **fail**
- Click **“View Supported Sites”** to see the lists
- If a site fails, it’s moved to the "invalid" list

---

## 🛠️ Troubleshooting

- **Spotify not working?** Make sure you ran:  
  ```bash
  pip install spotdl
  ```

- **Site says “invalid”?**  
  You can still queue it, but it might fail — the app will warn you.

- **Black screen for SoundCloud/Bandcamp in Video Mode?**  
  That’s intended! Audio-only sites will auto-wrap audio in a black video background when using Video mode.

---

## 📂 Downloads Location

| Type   | Location                    |
|--------|-----------------------------|
| Audio  | `downloads/audio/`          |
| Video  | `downloads/video/`          |
| Temp   | `downloads/audio_temp/`     |

---

## 🔑 Keyboard Shortcuts

- Press **Delete** on a selected queue item to remove it  
- Right-click an item for context menu options

---

## 💻 Developers

All logic is in `downloader.py`  
Customizations include:

- `AUDIO_ONLY_DOMAINS` – defines domains that don’t support video  
- `ffmpeg.exe` – bundled next to the script  
- `sites.json` – stores known working/failing domains  
- Modular functions and thread-safe queue processing

---

## ❤️ Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for downloading  
- [spotdl](https://github.com/spotDL/spotify-downloader) for Spotify  
- [tkinter](https://docs.python.org/3/library/tkinter.html) for GUI  
- [FFmpeg](https://ffmpeg.org/) for processing

---

## ✅ Final Notes

- This is a local GUI app — no telemetry, no ads, no tracking.  
- You **must** supply `ffmpeg.exe` manually (due to licensing).  
- Enjoy downloading and archiving your favorite content!
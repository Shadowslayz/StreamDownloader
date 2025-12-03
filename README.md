StreamDownloader

Universal Media Downloader

A user-friendly Windows app to download audio and video from:

YouTube

Spotify

SoundCloud

Bandcamp

and more…

Supports playlists, format selection (MP3, MP4, WAV, etc.), dynamic site status tracking, and auto-parsing Spotify playlists.

✅ Features

Download audio & video from multiple platforms

Multiple output formats: MP3, MP4, WAV, MKV, M4A, etc.

Automatically extracts YouTube & Spotify playlists

Warns about unsupported/unstable sites

Dynamic queue system

Built-in terminal-style log

Theme-aware modern GUI

Auto-wraps audio-only sources into video format

Works offline (except for downloading itself 😅)

🚀 How to Install
1. Install Python 3.9+

Download from: https://python.org

⚠️ Make sure to check "Add Python to PATH" on installation.

2. Install dependencies

Open Command Prompt and run:

pip install yt-dlp spotdl requests tk

3. Place FFmpeg binaries in the app folder

Your project root directory must contain the following files:

ffmpeg.exe

ffplay.exe

ffprobe.exe

These must be placed in the same folder as downloader.py, or the app cannot process audio/video.

You can download FFmpeg from: https://ffmpeg.org/download.html

→ Extract the bin/ folder and copy those three .exe files.

4. Run the app
python downloader.py

🧠 How to Use

Start the app

Pick Audio or Video mode

Paste your link (YouTube, Spotify, etc.)

Choose your format

Click Queue Download

Files will appear in the appropriate download folder

🎵 Spotify Support

Paste Spotify track, album, or playlist links

App uses spotdl to match songs on YouTube

Automatically queues + names all tracks correctly

📑 Dynamic Site List

App tracks domains in sites.json

Good sites go to valid_sites

Failing sites move to invalid_sites

Check via: “View Supported Sites” in the UI

🛠️ Troubleshooting
Spotify not working?

Make sure spotdl is installed:

pip install spotdl

Downloads failing?

Your ffmpeg, ffplay, or ffprobe might be missing — check your root directory.

Audio-only site + Video mode = black screen?

This is intended.
App wraps audio into a black video to preserve MP4 output.

📂 Download Locations
Type	Folder
Audio	downloads/audio/
Video	downloads/video/
Temp	downloads/audio_temp/
🔑 Keyboard Shortcuts

Delete key → remove selected queue item

Right-click → context menu options

💻 Developer Notes

Core logic lives in:

downloader.py

Important components:

AUDIO_ONLY_DOMAINS → list of audio-only sites

sites.json → tracks valid/invalid domains

ffmpeg.exe, ffplay.exe, ffprobe.exe → processing binaries

Thread-safe queue system

Dynamic terminal-style log output

❤️ Credits

yt-dlp → video/audio extraction

spotdl → Spotify-to-YouTube mapping

FFmpeg → audio & video processing

Tkinter → GUI framework

✅ Final Notes

100% local app — no telemetry.

Requires ffmpeg, ffplay, and ffprobe in the root directory.

Fully open and modifiable.

Enjoy downloading & archiving your favorite media!
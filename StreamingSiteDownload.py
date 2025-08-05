import os
import re
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from urllib.parse import urlparse
from yt_dlp import YoutubeDL
import requests
import glob
import sys
import json

SITES_FILE = "sites.json"
AUDIO_ONLY_DOMAINS = ["soundcloud.com", "bandcamp.com", "open.spotify.com"]  # Add more as needed

def load_sites():
    if not os.path.exists(SITES_FILE):
        with open(SITES_FILE, "w") as f:
            json.dump({"valid_sites": [], "invalid_sites": []}, f)
    with open(SITES_FILE) as f:
        return json.load(f)

def save_sites(sites):
    with open(SITES_FILE, "w") as f:
        json.dump(sites, f, indent=2)

def get_domain(url):
    domain = urlparse(url).netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

def add_valid_site(url):
    sites = load_sites()
    domain = get_domain(url)
    if domain not in sites["valid_sites"]:
        sites["valid_sites"].append(domain)
        if domain in sites["invalid_sites"]:
            sites["invalid_sites"].remove(domain)
        save_sites(sites)

def add_invalid_site(url):
    sites = load_sites()
    domain = get_domain(url)
    if domain not in sites["invalid_sites"]:
        sites["invalid_sites"].append(domain)
        if domain in sites["valid_sites"]:
            sites["valid_sites"].remove(domain)
        save_sites(sites)

def is_invalid_domain(url):
    sites = load_sites()
    domain = get_domain(url)
    return domain in sites.get("invalid_sites", [])

class DownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Downloader")
        self.minsize(800, 500)
        self.resizable(False, False)
        self.ffmpeg_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "ffmpeg.exe")
        self.download_mode = None  # 'audio' or 'video'
        self.audio_format = tk.StringVar(value="original")
        self.video_format = tk.StringVar(value="original")
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (StartPage, DownloadPage):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)
    def show_sites_window(self):
        sites = load_sites()
        window = tk.Toplevel(self)
        window.title("Known Sites (Dynamic)")
        window.geometry("600x400")

        # Split frame
        frame = tk.Frame(window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Valid Sites (left)
        valid_frame = tk.Frame(frame)
        valid_frame.pack(side="left", fill="both", expand=True, padx=(0,5))
        tk.Label(valid_frame, text="✅ Valid Sites", font=("Helvetica", 12, "bold")).pack(anchor="n", pady=(0, 5))
        valid_list = tk.Listbox(valid_frame, width=35)
        valid_list.pack(fill="both", expand=True)
        for site in sorted(sites.get("valid_sites", [])):
            valid_list.insert(tk.END, site)

        # Invalid Sites (right)
        invalid_frame = tk.Frame(frame)
        invalid_frame.pack(side="left", fill="both", expand=True, padx=(5,0))
        tk.Label(invalid_frame, text="❌ Invalid Sites", font=("Helvetica", 12, "bold")).pack(anchor="n", pady=(0, 5))
        invalid_list = tk.Listbox(invalid_frame, width=35)
        invalid_list.pack(fill="both", expand=True)
        for site in sorted(sites.get("invalid_sites", [])):
            invalid_list.insert(tk.END, site)

        ttk.Button(window, text="Close", command=window.destroy).pack(pady=5)

    def show_frame(self, page):
        frame = self.frames[page]
        frame.tkraise()
        if page == DownloadPage:
            if self.download_mode == 'audio':
                self.selected_format = self.audio_format
            else:
                self.selected_format = self.video_format
            frame.update_format_options()

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = tk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")

        label = ttk.Label(container, text="What would you like to download?", font=("Helvetica", 16))
        label.pack(pady=20)

        

        audio_btn = ttk.Button(container, text="🎵 Music / Audio", command=lambda: self.set_mode_and_proceed(controller, 'audio'))
        video_btn = ttk.Button(container, text="🎬 Video", command=lambda: self.set_mode_and_proceed(controller, 'video'))
        sites_btn = ttk.Button(container, text="View Supported Sites", command=lambda: controller.show_sites_window())
        sites_btn.pack(pady=10)
        audio_btn.pack(pady=10)
        video_btn.pack(pady=10)

        self.container = container
        self.bind("<Configure>", self.center_container)

    def center_container(self, event=None):
        w = self.winfo_width()
        h = self.winfo_height()
        cw = self.container.winfo_reqwidth()
        ch = self.container.winfo_reqheight()
        x = (w - cw) // 2
        y = (h - ch) // 2
        self.container.place(x=x, y=y)

    def set_mode_and_proceed(self, controller, mode):
        controller.download_mode = mode
        if mode == 'audio':
            controller.selected_format = controller.audio_format
        else:
            controller.selected_format = controller.video_format
        controller.show_frame(DownloadPage)

class DownloadPage(tk.Frame):
    AUDIO_ONLY_DOMAINS = ["soundcloud.com", "bandcamp.com", ]  # Add more as needed
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.download_queue = []  # Each item will be a dict with url and format
        self.is_downloading = False
        self.terminal_visible = False
        self.current_process = None  # For killing spotdl
        # Layout
        self.sidebar = tk.Frame(self, width=200)
        self.sidebar.pack(side="left", fill="y")

        self.main = tk.Frame(self)
        self.main.pack(side="left", fill="both", expand=True)

        # Add mode label (Audio/Video)
        self.mode_label = ttk.Label(self.main, text="", font=("Helvetica", 12, "bold"))
        self.mode_label.pack(pady=(10, 5))

        

        self.terminal_container = tk.Frame(self)
        self.terminal = scrolledtext.ScrolledText(self.terminal_container, height=15, state="disabled", wrap=tk.WORD, bg="black", fg="lime")
        self.terminal.pack(fill="both", expand=True)

        # Sidebar
        self.queue_label = ttk.Label(self.sidebar, text="Queue")
        self.queue_label.pack(pady=(10, 0))
        self.queue_listbox = tk.Listbox(self.sidebar, width=30)
        self.queue_listbox.bind('<Delete>', lambda e: self.remove_selected_item())
        self.queue_listbox.bind('<Button-3>', self.show_context_menu)
        self.queue_listbox.bind('<Delete>', lambda e: self.remove_selected_item())
        self.queue_listbox.pack(pady=5, padx=5, fill="y")
        self.toggle_btn = ttk.Button(self.sidebar, text="☰ Show Terminal", command=self.toggle_terminal)
        self.toggle_btn.pack(pady=5)

        # Control Buttons
        self.clear_btn = ttk.Button(self.sidebar, text="🧹 Clear Queue", command=self.clear_queue)
        self.clear_btn.pack(pady=2)

        # Main Area
        self.format_frame = ttk.Frame(self.main)
        self.format_frame.pack(pady=5)

        

        self.format_buttons = []  # To clear old buttons

        self.url_entry = ttk.Entry(self.main, width=60)
        self.entry_style = ttk.Style()
        self.entry_style.configure("Warning.TEntry", fieldbackground="yellow")
        self.entry_style.configure("Normal.TEntry", fieldbackground="white")
        self.url_entry.configure(style="Normal.TEntry")

        self.url_entry.pack(pady=10)
        self.url_entry.bind("<KeyRelease>", self.check_invalid_domain)
        self.queue_btn = ttk.Button(self.main, text="⬇️ Queue Download", command=self.queue_download)
        self.queue_btn.pack(pady=5)

        self.current_label = ttk.Label(self.main, text="Now Downloading: None")
        self.current_label.pack(pady=10)
        self.progress_bar = ttk.Progressbar(self.main, mode='determinate')
        self.progress_bar.pack(fill="x", padx=20)

        back_btn = ttk.Button(self.main, text="⬅ Back", command=lambda: controller.show_frame(StartPage))
        back_btn.pack(pady=10)
    
    def check_invalid_domain(self, event=None):
        url = self.url_entry.get().strip()
        if not url:
            self.url_entry.configure(style="Normal.TEntry")
            return
        domain = get_domain(url)
        sites = load_sites()
        if domain in sites["invalid_sites"]:
            self.url_entry.configure(style="Warning.TEntry")
        else:
            self.url_entry.configure(style="Normal.TEntry")

    def update_format_options(self):
        # Set mode label text
        mode = self.controller.download_mode
        mode_display = "Audio" if mode == "audio" else "Video" if mode == "video" else ""
        self.mode_label.config(text=mode_display)
        # Update header with current mode
        mode = self.controller.download_mode
        mode_display = "Audio" if mode == "audio" else "Video" if mode == "video" else "None"
        for widget in self.format_frame.winfo_children():
            widget.destroy()

        self.format_dropdown = ttk.Menubutton(
            self.format_frame,
            text=f"Select Format: {self.controller.selected_format.get()}",
            direction="below"
        )
        self.format_menu = tk.Menu(self.format_dropdown, tearoff=0)
        self.format_dropdown["menu"] = self.format_menu
        self.format_dropdown.pack()

        self.format_buttons.clear()

        mode = self.controller.download_mode
        formats = [("Keep Original", "original")]
        if mode == 'audio':
            formats += [("MP3", "mp3"), ("WAV", "wav"), ("OGG", "ogg"), ("AAC", "aac"), ("FLAC", "flac"), ("M4A", "m4a")]
        elif mode == 'video':
            formats += [("MP4", "mp4"), ("MKV", "mkv"), ("WEBM", "webm"), ("AVI", "avi"), ("MOV", "mov"), ("FLV", "flv"), ("WMV", "wmv")]

        for text, value in formats:
            self.format_menu.add_radiobutton(
                label=text,
                variable=self.controller.selected_format,
                value=value,
                command=lambda val=value: [
                    self.controller.audio_format.set(val) if self.controller.download_mode == 'audio' else self.controller.video_format.set(val),
                    self.controller.selected_format.set(val),
                    self.format_dropdown.config(text=f"Select Format: {val}")
                ]
            )

    def toggle_terminal(self):
        if self.terminal_visible:
            self.terminal_container.pack_forget()
            self.toggle_btn.config(text="☰ Show Terminal")
            self.controller.update_idletasks()
            self.controller.geometry(f"{self.controller.winfo_reqwidth()}x{self.controller.winfo_reqheight()}")
        else:
            self.terminal_container.pack(side="right", fill="y")
            self.toggle_btn.config(text="❌ Hide Terminal")
            self.controller.update_idletasks()
            self.controller.geometry(f"{self.controller.winfo_reqwidth()}x{self.controller.winfo_reqheight()}")
        self.terminal_visible = not self.terminal_visible

    def log_message(self, message):
        self.terminal.configure(state="normal")
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.configure(state="disabled")
        self.terminal.see(tk.END)
    def add_to_queue(self, track_url, display=None, download_mode=None):
        mode = download_mode if download_mode else self.controller.download_mode
        self.download_queue.append({
            "url": track_url,
            "format": self.controller.selected_format.get(),
            "mode": mode
        })
        self.queue_listbox.insert(tk.END, display if display else track_url)

    def queue_download(self):

        if not self.terminal_visible:
            self.toggle_terminal()
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a URL.")
            return

        # --- DOMAIN CHECK ---
        domain = get_domain(url)
        sites = load_sites()
        if domain in sites["invalid_sites"]:
            self.url_entry.config(background="yellow")  # Highlight entry box
            self.log_message(f"⚠️ This site is flagged as invalid: {domain}")
            messagebox.showwarning("Invalid Site", f"This site ({domain}) is known to not work, but you can still queue it if you want.")
        else:
            self.url_entry.config(background="white")  # Reset if not flagged

        # ----------- SPOTIFY -----------
        if "open.spotify.com" in url:
            self.log_message(f"🔎 Parsing Spotify playlist: {url}")
            script_dir = os.path.dirname(os.path.abspath(__file__))
            save_path = os.path.join(script_dir, "spotdl_temp.spotdl")
            ffmpeg_path = os.path.join(script_dir, "ffmpeg.exe")
            import sys, subprocess, json

            try:
                cmd = [
                    sys.executable, "-m", "spotdl",
                    "save", url,
                    "--save-file", save_path,
                    "--ffmpeg", ffmpeg_path
                ]
                subprocess.run(cmd, check=True)
                with open(save_path, "r", encoding="utf-8") as f:
                    tracks = json.load(f)
                for track in tracks:
                    track_url = track.get("url")
                    name = f"Spotify: {track.get('name', '')} - {track.get('artists', [''])[0]}"
                    if track_url:
                        self.add_to_queue(track_url, name, download_mode='audio')  # Correct, does both
                self.log_message(f"✅ Added {len(tracks)} tracks from Spotify playlist to queue.")
            except Exception as e:
                self.log_message(f"❌ Spotify parsing failed: {e}")

        # ----------- YOUTUBE -----------
        elif not "open.spotify.com" in url:
            self.log_message(f"🔎 Parsing YouTube playlist: {url}")
            try:
                with YoutubeDL({'quiet': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if 'entries' in info:
                        for entry in info['entries']:
                            if entry and entry.get('webpage_url'):
                                self.add_to_queue(entry['webpage_url'], f"YouTube: {entry.get('title', '')}", download_mode=self.controller.download_mode)
                        self.log_message(f"✅ Added {len(info['entries'])} videos from YouTube playlist to queue.")
                    else:
                        self.add_to_queue(url, f"YouTube: {info.get('title', url)}", download_mode=self.controller.download_mode)
                add_valid_site(url)   # (if you have this line!)
            except Exception as e:
                self.log_message(f"❌ Failed to parse YouTube URL: {e}")
                add_invalid_site(url)   # (if you have this line!)

        # ----------- OTHER -----------
        else:
            self.add_to_queue(url, download_mode=self.controller.download_mode)

        self.url_entry.delete(0, tk.END)
        if not self.is_downloading:
            self.process_queue()
        
        #reset color
        self.url_entry.delete(0, tk.END)
        self.url_entry.configure(foreground="black")


    def download_thread(self, url, format_choice, mode=None):
        self.is_downloading = True

        # --- Detect domain ---
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # --- Handle Spotify ---
        if "open.spotify.com" in url:
            output_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "downloads", "audio")
            os.makedirs(output_dir, exist_ok=True)
            ffmpeg_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "ffmpeg.exe")

            cmd = [
                sys.executable, "-m", "spotdl",
                "--ffmpeg", ffmpeg_path,
                "--output", output_dir,
                url
            ]

            self.log_message(f"🎧 Downloading from Spotify with spotdl: {url}")
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                self.current_process = proc
                for line in proc.stdout:
                    self.log_message(line.strip())
                proc.wait()
                self.current_process = None
                if proc.returncode == 0:
                    self.log_message("✅ Spotify download complete.")
                else:
                    self.log_message("❌ Spotify download failed.")
            except Exception as e:
                self.log_message(f"❌ spotdl error: {e}")
            self.after(100, self.process_queue)
            return

        # --- Handle audio-only link in video mode: produce black screen video ---
        if (mode == "video") and (domain in AUDIO_ONLY_DOMAINS):
            audio_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "downloads", "audio_temp")
            video_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "downloads", "video")
            os.makedirs(audio_dir, exist_ok=True)
            os.makedirs(video_dir, exist_ok=True)
            audio_file = os.path.join(audio_dir, "%(title)s.%(ext)s")
            video_file = None

            def audio_hook(d):
                if d['status'] == 'finished':
                    self.log_message("✅ Finished audio download: " + d['filename'])
                    nonlocal video_file
                    audio_out = d['filename']
                    base = os.path.splitext(os.path.basename(audio_out))[0]
                    video_file = os.path.join(video_dir, base + ".mp4")
                    # Create black-screen video with ffmpeg
                    cmd = [
                        self.controller.ffmpeg_path, "-y",
                        "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=30:d=9999",
                        "-i", audio_out,
                        "-shortest",
                        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                        "-pix_fmt", "yuv420p",
                        video_file
                    ]
                    self.log_message(f"🎬 Creating black screen video: {video_file}")
                    try:
                        subprocess.run(cmd, check=True)
                        self.log_message(f"✅ Created video: {video_file}")
                    except Exception as e:
                        self.log_message(f"❌ ffmpeg error: {e}")

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_file,
                'progress_hooks': [audio_hook],
                'quiet': True,
                'ffmpeg_location': self.controller.ffmpeg_path,
            }

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                self.log_message(f"❌ Audio download error: {e}")
            self.after(100, self.process_queue)
            return

        # --- Regular downloaders ---
        try:
            if format_choice == 'original':
                self.download_original(url)
            elif mode == 'audio':
                self.download_audio(url, format_choice)
            elif mode == 'video':
                self.download_video(url, format_choice)
            else:
                self.log_message(f"⚠️ Format '{format_choice}' not implemented for mode '{mode}'. Skipping.")
        except Exception as e:
            self.log_message(f"❌ Download error: {e}")

        self.after(100, self.process_queue)





    def process_queue(self):
        if not self.download_queue:
            self.progress_bar.stop()
            self.progress_bar['value'] = 0
            self.current_label.config(text="Now Downloading: None")
            self.is_downloading = False
            return

        item = self.download_queue.pop(0)
        url = item['url']
        format_choice = item['format']
        download_mode = item.get('mode', self.controller.download_mode)  # NEW: pull mode from item

        self.queue_listbox.delete(0)
        self.current_label.config(text=f"Now Downloading: {url} ({download_mode}/{format_choice})")
        self.log_message(f"📥 Starting download: {url} as {download_mode} [{format_choice}]")
        self.progress_bar['value'] = 0
        self.is_downloading = True

        # Pass mode to the thread
        threading.Thread(target=self.download_thread, args=(url, format_choice, download_mode)).start()


        

    def download_video(self, url, format_choice):
            output_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "downloads", "video")
            os.makedirs(output_dir, exist_ok=True)

            def hook(d):
                if d['status'] == 'downloading':
                    if not hasattr(self, "_last_log") or self._last_log != d.get('filename'):
                        self._last_log = d.get('filename')
                        self.log_message(f"⬇ Downloading... {self._last_log}")
                    percent = d.get('_percent_str', '0%').strip('%')
                    try:
                        self.progress_bar['value'] = float(percent)
                    except:
                        pass
                elif d['status'] == 'finished':
                    self.log_message("✅ Finished: " + d['filename'])

            opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
                'ffmpeg_location': self.controller.ffmpeg_path,
                'progress_hooks': [hook],
                'quiet': True
            }

            if format_choice in ['mp4', 'mkv', 'webm']:
                opts['merge_output_format'] = format_choice
                opts['postprocessors'] = [{
                    'key': 'FFmpegVideoRemuxer',
                    'preferedformat': format_choice,
                }]
            elif format_choice in ['avi', 'mov', 'flv', 'wmv']:
                opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': format_choice,
                }]

            try:
                with YoutubeDL(opts) as ydl:
                    ydl.download([url])
                # If no exception, mark as valid
                print("Adding Url To valid")
                add_valid_site(url)
            except Exception as e:
                self.log_message(f"❌ Error: {e}")
                # Mark as invalid domain on any failure
                print("Adding Url To Invalid")
                add_invalid_site(url)




    def download_audio(self, url, format_choice):
        output_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "downloads", "audio")
        os.makedirs(output_dir, exist_ok=True)

        def hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').strip('%')
                try:
                    self.progress_bar['value'] = float(percent)
                except:
                    pass
            elif d['status'] == 'finished':
                self.log_message("✅ Finished: " + d['filename'])

        opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
            'ffmpeg_location': self.controller.ffmpeg_path,
            'progress_hooks': [hook],
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_choice,
                'preferredquality': '192',
            }]
        }

        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
            add_valid_site(url)
        except Exception as e:
            add_invalid_site(url)



    def remove_selected_item(self):
        selected = self.queue_listbox.curselection()
        if selected:
            index = selected[0]
            self.queue_listbox.delete(index)
            del self.download_queue[index]
            self.log_message("❌ Removed item from queue.")

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="❌ Remove from Queue", command=self.remove_selected_item)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def clear_queue(self):
        self.download_queue.clear()
        self.queue_listbox.delete(0, tk.END)
        self.log_message("🧹 Queue cleared.")

    def download_original(self, url):
        # Use audio or video folder depending on current mode
        mode = self.controller.download_mode
        folder = "audio" if mode == "audio" else "video"
        output_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "downloads", folder)
        os.makedirs(output_dir, exist_ok=True)

        def hook(d):
            if d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').strip('%')
                try:
                    self.progress_bar['value'] = float(percent)
                except:
                    pass
            elif d['status'] == 'finished':
                self.log_message("✅ Finished: " + d['filename'])

        opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
            'ffmpeg_location': self.controller.ffmpeg_path,
            'progress_hooks': [hook],
            'quiet': True
        }

        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
            
        except Exception as e:
            self.log_message(f"❌ Error: {e}")

    def download_spotify(self, url):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "downloads", "audio")
        os.makedirs(output_dir, exist_ok=True)
        ffmpeg_path = os.path.join(script_dir, "ffmpeg.exe")

        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()

        cmd = [
            sys.executable, "-m", "spotdl",
            "--ffmpeg", ffmpeg_path,
            "--output", output_dir,
            url
        ]

        try:
            self.log_message(f"🎧 Downloading from Spotify via YouTube: {url}")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                self.log_message(line.strip())
            proc.wait()
            if proc.returncode == 0:
                # Find latest mp3
                import glob
                mp3_files = glob.glob(os.path.join(output_dir, "*.mp3"))
                latest_file = max(mp3_files, key=os.path.getctime) if mp3_files else None
                if latest_file:
                    song_name = os.path.basename(latest_file)
                    self.log_message(f"✅ Downloaded: {song_name}")
                else:
                    self.log_message("✅ Spotify download complete (no .mp3 file found?)")
            else:
                self.log_message("❌ Spotify download failed.")
        except Exception as e:
            self.log_message(f"❌ Spotify Error: {e}")
        finally:
            self.progress_bar.stop()
            self.progress_bar['value'] = 0


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()

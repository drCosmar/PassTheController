#!/usr/bin/env python3

import os
import json
import platform
import socket
import logging
from datetime import datetime
import time
from pathlib import Path
from ftplib import FTP
import tkinter as tk
from tkinter import messagebox
import tkinter.simpledialog
import getpass

# Program metadata
PROGRAM_NAME = "PassTheController!"
CREATOR = "Dr.Cosmar"
ORGANIZATION = "HalfAHeart"
DESCRIPTION = (
    "A basic application for passing the SaveState slot 1 from Dolphin Emulator to or from the HaH FTP server. "
    "This facilitates in group one-player games, and allows the players to simulate \"passing the controller\", "
    "without having to be in the same room."
)
ICON_FILE = "ptc.png"
VERSION = "v0.97b"

# Set up logging
log_file = Path(__file__).parent / f"{PROGRAM_NAME}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"{PROGRAM_NAME}\n    Version: {VERSION}\n    By:{CREATOR} of {ORGANIZATION}")
logger.info(f"Description: {DESCRIPTION}")

# Hardcoded settings
FTP_HOSTS = [""] #Don't forget to populate this with at least 1 FTP address local or network.
FTP_PORT = 21
FTP_BASE_DIRECTORY = "savestates"
GAME_IDS = {
    "Legend of Zelda: Twilight Princess": "GZ2E01"
}
SLOT_SUFFIX = ".s01"
DEFAULT_CHANNELS = ["1", "2", "3", "4", "5"]

# Configuration file
CONFIG_FILE = Path.home() / f".{PROGRAM_NAME}.json"

# Global status label (defined later in create_gui)
status_label = None

def get_save_state_path(game_id):
    """Determine the save state file path based on the OS."""
    logger.debug("Determining save state path")
    system = platform.system()
    username = getpass.getuser()
    
    if system == "Linux":
        base_path = Path.home() / ".var/app/org.DolphinEmu.dolphin-emu/data/dolphin-emu/StateSaves"
    elif system == "Windows":
        base_path = Path.home() / "Documents/Dolphin Emulator/StateSaves"
    else:
        logger.error("Unsupported OS: %s", system)
        raise ValueError("Unsupported OS. Only Linux and Windows are supported.")
    
    save_file_name = f"{game_id}{SLOT_SUFFIX}"
    path = base_path / save_file_name
    logger.debug("Save state path: %s", path)
    return path

def load_config():
    """Load FTP credentials, game ID, and channel from config file or prompt user."""
    logger.debug("Loading config from %s", CONFIG_FILE)
    default_config = {
        "ftp_user": "",
        "ftp_pass": "",
        "game_id": list(GAME_IDS.values())[0],
        "channel": DEFAULT_CHANNELS[0]
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                for key, value in default_config.items():
                    config.setdefault(key, value)
                logger.info("Config loaded: ftp_user=%s, game_id=%s, channel=%s", 
                           config["ftp_user"], config["game_id"], config["channel"])
                return config
        except Exception as e:
            logger.error("Failed to load config: %s", e)
            raise
    
    logger.info("No config file found, prompting for credentials")
    config = default_config.copy()
    root = tk.Tk()
    root.withdraw()
    config["ftp_user"] = tk.simpledialog.askstring(
        "FTP Login", "Enter FTP username:", initialvalue="ftpuser"
    ) or ""
    config["ftp_pass"] = tk.simpledialog.askstring(
        "FTP Login", "Enter FTP password:", show="*"
    ) or ""
    root.destroy()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        logger.info("Config saved: ftp_user=%s, game_id=%s, channel=%s", 
                   config["ftp_user"], config["game_id"], config["channel"])
    except Exception as e:
        logger.error("Failed to save config: %s", e)
        raise
    
    return config

def update_credentials():
    """Prompt user to update FTP credentials."""
    logger.debug("Updating FTP credentials")
    config = load_config()
    root = tk.Tk()
    root.withdraw()
    config["ftp_user"] = tk.simpledialog.askstring(
        "Update FTP Login", "Enter FTP username:", initialvalue=config["ftp_user"]
    ) or config["ftp_user"]
    config["ftp_pass"] = tk.simpledialog.askstring(
        "Update FTP Login", "Enter FTP password:", show="*", initialvalue=config["ftp_pass"]
    ) or config["ftp_pass"]
    root.destroy()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        logger.info("FTP credentials updated: ftp_user=%s", config["ftp_user"])
        messagebox.showinfo("Success", "FTP login information updated.")
    except Exception as e:
        logger.error("Failed to update config: %s", e)
        messagebox.showerror("Error", f"Failed to update credentials: {e}")

def update_game_selection(root):
    """Update selected game via dropdown menu."""
    logger.debug("Updating game selection")
    config = load_config()
    game_menu = tk.Menu(root, tearoff=0)
    for game_name, game_id in GAME_IDS.items():
        game_menu.add_command(label=game_name, command=lambda gid=game_id: set_game_id(gid))
    game_menu.post(root.winfo_pointerx(), root.winfo_pointery())

def set_game_id(game_id):
    """Set and save the selected game ID."""
    config = load_config()
    config["game_id"] = game_id
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        logger.info("Game selection updated: %s", game_id)
        messagebox.showinfo("Success", f"Game set to {next(k for k, v in GAME_IDS.items() if v == game_id)}")
    except Exception as e:
        logger.error("Failed to update game selection: %s", e)
        messagebox.showerror("Error", f"Failed to update game: {e}")

def get_ftp_channels(ftp):
    """Scan FTP savestates directory for existing channels."""
    try:
        ftp.cwd(FTP_BASE_DIRECTORY)
        channels = [d for d in ftp.nlst() if d.isdigit()]
        logger.debug("Found channels: %s", channels)
        return channels if channels else DEFAULT_CHANNELS
    except Exception as e:
        logger.debug("Failed to scan channels, using defaults: %s", e)
        return DEFAULT_CHANNELS

def update_channel_selection(root):
    """Update selected channel via dropdown menu."""
    logger.debug("Updating channel selection")
    config = load_config()
    ftp, _ = connect_ftp()
    channels = get_ftp_channels(ftp)
    ftp.quit()
    
    channel_menu = tk.Menu(root, tearoff=0)
    for channel in channels:
        channel_menu.add_command(label=f"Channel {channel}", command=lambda ch=channel: set_channel(ch))
    channel_menu.add_separator()
    channel_menu.add_command(label="Add Channel...", command=add_channel)
    channel_menu.post(root.winfo_pointerx(), root.winfo_pointery())

def set_channel(channel):
    """Set and save the selected channel."""
    config = load_config()
    config["channel"] = channel
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        logger.info("Channel selection updated: %s", channel)
        messagebox.showinfo("Success", f"Channel set to {channel}")
    except Exception as e:
        logger.error("Failed to update channel: %s", e)
        messagebox.showerror("Error", f"Failed to update channel: {e}")

def add_channel():
    """Prompt user to add a new channel."""
    logger.debug("Adding new channel")
    config = load_config()
    root = tk.Tk()
    root.withdraw()
    new_channel = tk.simpledialog.askstring(
        "Add Channel", "Enter new channel number (e.g., 6):", initialvalue="6"
    )
    root.destroy()
    
    if not new_channel or not new_channel.isdigit():
        logger.error("Invalid channel number: %s", new_channel)
        messagebox.showerror("Error", "Please enter a valid number.")
        return
    
    ftp, host = connect_ftp()
    try:
        ftp.cwd(FTP_BASE_DIRECTORY)
        ftp.mkd(new_channel)
        logger.debug("Created new channel directory: %s", new_channel)
    except Exception as e:
        if "550" not in str(e):
            logger.error("Failed to create channel %s: %s", new_channel, e)
            ftp.quit()
            messagebox.showerror("Error", f"Failed to create channel: {e}")
            return
    
    config["channel"] = new_channel
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        logger.info("New channel added and selected: %s", new_channel)
        messagebox.showinfo("Success", f"Channel {new_channel} added and selected.")
    except Exception as e:
        logger.error("Failed to save new channel: %s", e)
        messagebox.showerror("Error", f"Failed to save channel: {e}")
    finally:
        ftp.quit()

def connect_ftp():
    """Try connecting to FTP hosts in order with status feedback."""
    global status_label
    logger.debug("Attempting FTP connection")
    config = load_config()
    if not config["ftp_user"] or not config["ftp_pass"]:
        logger.error("FTP username or password not set")
        raise ValueError("FTP username or password not set. Please update via File > Login Info.")
    
    status_label.config(text="Connecting to FTP server... (up to 2 min)")
    status_label.update_idletasks()  # Force GUI update
    
    for host in FTP_HOSTS:
        logger.debug("Connecting to %s:%d", host, FTP_PORT)
        try:
            ftp = FTP()
            ftp.connect(host=host, port=FTP_PORT, timeout=120)
            ftp.login(user=config["ftp_user"], passwd=config["ftp_pass"])
            logger.info("Connected to %s", host)
            status_label.config(text="")
            return ftp, host
        except (socket.gaierror, socket.timeout, ConnectionRefusedError) as e:
            logger.warning("Failed to connect to %s: %s", host, e)
            continue
    logger.error("Could not connect to any FTP host")
    status_label.config(text="")
    raise ConnectionError("Could not connect to any FTP host")

def get_ftp_file_date(ftp, filename):
    """Get modification date of a file on the FTP server in UTC."""
    try:
        response = ftp.sendcmd(f"MDTM {filename}")
        if response.startswith("213"):
            ftp_date_str = response[4:].strip()
            ftp_date = datetime.strptime(ftp_date_str, "%Y%m%d%H%M%S")
            logger.debug("FTP file date for %s (MDTM, UTC): %s", filename, ftp_date)
            return ftp_date
    except Exception as e:
        logger.debug("MDTM failed for %s: %s", filename, e)
    
    try:
        lines = []
        ftp.dir(filename, lines.append)
        if lines:
            parts = lines[0].split()
            if len(parts) >= 8:
                date_str = " ".join(parts[4:7])
                ftp_date = datetime.strptime(date_str, "%b %d %H:%M")
                current_year = datetime.now().year
                ftp_date = ftp_date.replace(year=current_year)
                if ftp_date > datetime.now():
                    ftp_date = ftp_date.replace(year=current_year - 1)
                ftp_date = datetime.utcfromtimestamp(ftp_date.timestamp())
                logger.debug("FTP file date for %s (dir, UTC): %s", filename, ftp_date)
                return ftp_date
        logger.debug("No date available for %s in directory listing", filename)
        return None
    except Exception as e:
        logger.debug("Failed to get FTP file date for %s via dir: %s", filename, e)
        return None

def upload_file():
    """Upload the save state file to the FTP server if local is newer."""
    global status_label
    logger.debug("Starting upload")
    try:
        config = load_config()
        local_path = get_save_state_path(config["game_id"])
        logger.debug("Checking if file exists: %s", local_path)
        if not local_path.exists():
            logger.error("Save state file not found: %s", local_path)
            messagebox.showerror("Error", f"Save state file not found at {local_path}")
            return
        
        ftp, host = connect_ftp()
        user_dir = f"{FTP_BASE_DIRECTORY}/{config['channel']}"
        save_file_name = f"{config['game_id']}{SLOT_SUFFIX}"
        
        try:
            ftp.cwd(user_dir)
        except:
            logger.debug("Creating directory: %s", user_dir)
            ftp.mkd(user_dir)
            ftp.cwd(user_dir)
        
        local_date = datetime.utcfromtimestamp(os.path.getmtime(local_path))
        ftp_date = get_ftp_file_date(ftp, save_file_name)
        logger.debug("Local file date (UTC): %s, FTP file date (UTC): %s", local_date, ftp_date)
        
        if ftp_date is None or local_date > ftp_date:
            logger.debug("Uploading file: %s", save_file_name)
            with open(local_path, 'rb') as f:
                ftp.storbinary(f"STOR {save_file_name}", f)
            ftp.quit()
            logger.info("Upload successful to %s: %s", host, save_file_name)
            messagebox.showinfo("Success", f"Save state uploaded to {host}")
        else:
            logger.info("Upload skipped: Local file is not newer (%s <= %s)", local_date, ftp_date)
            ftp.quit()
            messagebox.showinfo("Skipped", "Upload skipped: Local save state is not newer than the server.")
    
    except Exception as e:
        logger.error("Upload failed: %s", e)
        status_label.config(text="")
        messagebox.showerror("Error", f"Upload failed: {e}")

def download_file():
    """Download the save state file from the FTP server if server is newer."""
    global status_label
    logger.debug("Starting download")
    try:
        config = load_config()
        local_path = get_save_state_path(config["game_id"])
        logger.debug("Ensuring directory exists: %s", local_path.parent)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        ftp, host = connect_ftp()
        user_dir = f"{FTP_BASE_DIRECTORY}/{config['channel']}"
        save_file_name = f"{config['game_id']}{SLOT_SUFFIX}"
        
        ftp.cwd(user_dir)
        
        ftp_date = get_ftp_file_date(ftp, save_file_name)
        local_date = datetime.utcfromtimestamp(os.path.getmtime(local_path)) if local_path.exists() else None
        logger.debug("Local file date (UTC): %s, FTP file date (UTC): %s", local_date, ftp_date)
        
        if ftp_date is None:
            logger.info("Download skipped: No file on server")
            ftp.quit()
            messagebox.showinfo("Skipped", "Download skipped: No save state on server.")
            return
        elif local_date is None or ftp_date > local_date:
            logger.debug("Downloading file: %s", save_file_name)
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f"RETR {save_file_name}", f.write)
            ftp.quit()
            logger.info("Download successful from %s: %s", host, save_file_name)
            messagebox.showinfo("Success", f"Save state downloaded from {host}")
        else:
            logger.info("Download skipped: Server file is not newer (%s <= %s)", local_date, ftp_date)
            ftp.quit()
            messagebox.showinfo("Skipped", "Download skipped: Server save state is not newer than local.")
    
    except Exception as e:
        logger.error("Download failed: %s", e)
        status_label.config(text="")
        messagebox.showerror("Error", f"Download failed: {e}")

def create_gui():
    """Create the GUI with upload/download buttons, menu, and status label."""
    global status_label
    logger.debug("Creating GUI")
    root = tk.Tk()
    root.title(f"{PROGRAM_NAME} {VERSION}")
    root.geometry("300x180")  # Increased height for status label
    
    # Set window icon (Windows)
    try:
        root.iconbitmap("icon/ptc64x64.ico")
    except Exception as e:
        logger.warning("Failed to set window icon: %s", e)
    
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Login Info...", command=update_credentials)
    filemenu.add_command(label="Game...", command=lambda: update_game_selection(filemenu))
    filemenu.add_command(label="Channel...", command=lambda: update_channel_selection(filemenu))
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)
    
    upload_button = tk.Button(root, text="Upload Save State", command=upload_file, width=20)
    upload_button.pack(pady=10)
    
    download_button = tk.Button(root, text="Download Save State", command=download_file, width=20)
    download_button.pack(pady=10)
    
    # Add status label
    status_label = tk.Label(root, text="", wraplength=280, justify="center")
    status_label.pack(pady=5)
    
    logger.info("GUI created, starting main loop")
    root.mainloop()

if __name__ == "__main__":
    logger.info("Starting %s", PROGRAM_NAME)
    create_gui()
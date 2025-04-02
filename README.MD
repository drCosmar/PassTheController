# PassTheController!
Version: v0.97b  
Author: Dr.Cosmar  
Organization: HalfAHeart  

A simple application for sharing Dolphin Emulator SaveState slot 1 via an FTP server. Perfect for group play of single-player games, letting players "pass the controller" remotely.

## Description
PassTheController! syncs save states between your local Dolphin Emulator folder and an FTP server. It compares file dates (UTC) to upload only newer local saves or download newer server saves, preventing progress loss. Built with Python and Tkinter, it supports Windows and Linux.

## Features
- Upload/download SaveState slot 1 (GZ2E01.s01 for Zelda: Twilight Princess).
- FTP connection with active mode (port 21).
- GUI with status feedback (up to 2-minute timeout).
- Configurable game ID and channel via menus.
- Logging to PassTheController.log.

## Prerequisites
- Python 3.10+ (for building from source).
- Dolphin Emulator installed (save state path: ~/Documents/Dolphin Emulator/StateSaves/ on Windows, ~/.var/app/org.DolphinEmu.dolphin-emu/data/dolphin-emu/StateSaves/ on Linux).
- An FTP server (e.g., vsftpd) with port 21 open.

## Setup Instructions
1. Clone the Repo:
   git clone https://github.com/drCosmar/PassTheController.git
   cd PassTheController

2. Configure FTP Hosts:
   - Open source/PassTheController.py in a text editor.
   - Find the FTP_HOSTS list (initially empty):
     FTP_HOSTS = []
   - Add your FTP server addresses:
     - For online access: Use your public FTP server (e.g., "yourserver.ddns.net").
     - For LAN access: Use your server’s local IP (e.g., "192.168.1.100").
     - Example:
       FTP_HOSTS = ["yourserver.ddns.net", "192.168.1.100"]
   - Save the file.

3. Install Dependencies:
   pip install pyinstaller

4. Build the Executable:
   - Windows (Option 1 - Manual):
     cd source
     pyinstaller --onefile --noconsole --icon=icons/ptc64x64.ico --add-data "icons/ptc64x64.ico;." --name=PassTheController PassTheController.py
   - Windows (Option 2 - Batch Script):
     - Double-click build_and_package.bat (at repo root).
     - Approve the admin prompt.
     - Builds, installs to C:\Program Files\PassTheController\, creates a Desktop shortcut, and packages into PassTheController.zip.
   - Linux:
     cd source
     pyinstaller --onefile --icon=icons/ptc64x64.ico --add-data "icons/ptc64x64.ico:." --name=PassTheController PassTheController.py
   - Output: source/dist/PassTheController (or .exe on Windows).

5. Run It:
   - If built manually:
     copy source/dist/PassTheController.exe .
     Double-click PassTheController.exe (Windows) or run ./PassTheController (Linux).
   - If using build_and_package.bat:
     Use the Desktop shortcut or C:\Program Files\PassTheController\PassTheController.exe.
   - First run: Enter your FTP username and password (saved to ~/.PassTheController!.json).

6. FTP Server Setup:
   - Ensure port 21 is forwarded on your router to your server’s LAN IP.
   - Configure vsftpd for active mode:
     sudo nano /etc/vsftpd.conf
     # Set: pasv_enable=NO
     sudo systemctl restart vsftpd
   - Place save states in savestates/<channel>/ (e.g., savestates/1/GZ2E01.s01).

## Usage
- Upload Save State: Sends local GZ2E01.s01 to the FTP server if newer.
- Download Save State: Pulls GZ2E01.s01 from the FTP server if newer.
- File > Login Info: Update FTP credentials.
- File > Game: Change game ID (currently only GZ2E01).
- File > Channel: Switch or add channels (e.g., 1, 2).

## Notes
- Save state path: ~/Documents/Dolphin Emulator/StateSaves/GZ2E01.s01 (Windows) or equivalent (Linux).
- Check PassTheController.log for errors.
- Active mode requires your client firewall to allow inbound connections (ports 1024–65535).
- Windows install requires admin rights (handled by build_and_package.bat).

## License
TBD by Dr.Cosmar.

## Contributing
Fork, modify, and submit a pull request. Issues welcome!
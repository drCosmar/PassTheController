@echo off
echo Building and packaging PassTheController v0.97b...

:: Check for admin rights and elevate if needed
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Requesting admin privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c %~f0' -Verb RunAs"
    exit /b
)

:: Build the executable
cd C:\Users\Deikt\PassTheController\source
pyinstaller --onefile --noconsole --icon=icons\ptc64x64.ico --add-data "icons\ptc64x64.ico;." --name=PassTheController PassTheController.py

:: Create and populate Program Files folder
echo Installing to C:\Program Files\PassTheController...
if not exist "C:\Program Files\PassTheController" mkdir "C:\Program Files\PassTheController"
copy dist\PassTheController.exe "C:\Program Files\PassTheController\"
copy icons\ptc64x64.ico "C:\Program Files\PassTheController\"

:: Create Desktop shortcut
echo Creating Desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('$env:USERPROFILE\Desktop\PassTheController.lnk'); $Shortcut.TargetPath = 'C:\Program Files\PassTheController\PassTheController.exe'; $Shortcut.IconLocation = 'C:\Program Files\PassTheController\ptc64x64.ico'; $Shortcut.Description = 'PassTheController v0.97b'; $Shortcut.Save()"

:: Create README and log
cd C:\Program Files\PassTheController
echo PassTheController! v0.97b by Dr.Cosmar, HalfAHeart > README.txt
echo A basic application for passing the SaveState slot 1 from Dolphin Emulator to or from the HaH FTP server. This facilitates in group one-player games, and allows the players to simulate "passing the controller", without having to be in the same room. >> README.txt
echo Instructions: >> README.txt
echo 1. Extract this zip folder or run build_and_package.bat to install. >> README.txt
echo 2. Double-click PassTheController.exe or use the Desktop shortcut. >> README.txt
echo 3. Enter FTP username "ftpuser" and password "super9two" (ask Dr.Cosmar). >> README.txt
echo 4. Upload or Download your save state. >> README.txt
echo PassTheController Log > PassTheController.log
echo --- >> PassTheController.log
echo Log cleared for new user. >> PassTheController.log

:: Zip the folder
echo Creating PassTheController.zip...
powershell -Command "Compress-Archive -Path 'C:\Program Files\PassTheController\PassTheController.exe','C:\Program Files\PassTheController\README.txt','C:\Program Files\PassTheController\PassTheController.log','C:\Program Files\PassTheController\ptc64x64.ico' -DestinationPath 'C:\Users\Deikt\PassTheController\PassTheController.zip' -Force"

echo Done! PassTheController.zip is ready in C:\Users\Deikt\PassTheController
echo Shortcut created on Desktop.
pause
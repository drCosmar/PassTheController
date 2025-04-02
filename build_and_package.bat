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

:: Create Desktop shortcut with error checking
echo Creating Desktop shortcut...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\PassTheController.lnk
set TARGET_PATH=C:\Program Files\PassTheController\PassTheController.exe
set ICON_PATH=C:\Program Files\PassTheController\ptc64x64.ico

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%TARGET_PATH%'; $Shortcut.IconLocation = '%ICON_PATH%'; $Shortcut.Description = 'PassTheController v0.97b'; $Shortcut.Save()" 2>shortcut_error.log

if %ERRORLEVEL% neq 0 (
    echo PowerShell shortcut creation failed. See shortcut_error.log for details.
    echo Falling back to VBScript method...
    echo Set oWS = WScript.CreateObject("WScript.Shell") > create_shortcut.vbs
    echo sLinkFile = "%SHORTCUT_PATH%" >> create_shortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> create_shortcut.vbs
    echo oLink.TargetPath = "%TARGET_PATH%" >> create_shortcut.vbs
    echo oLink.IconLocation = "%ICON_PATH%" >> create_shortcut.vbs
    echo oLink.Description = "PassTheController v0.97b" >> create_shortcut.vbs
    echo oLink.Save >> create_shortcut.vbs
    cscript //nologo create_shortcut.vbs
    del create_shortcut.vbs
    if exist "%SHORTCUT_PATH%" (
        echo Shortcut created successfully via VBScript.
    ) else (
        echo Failed to create shortcut. Check paths and permissions.
    )
) else (
    echo Shortcut created successfully via PowerShell.
)

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
if exist "%SHORTCUT_PATH%" (
    echo Shortcut created on Desktop.
) else (
    echo Shortcut creation failed - see shortcut_error.log or run manually.
)
pause
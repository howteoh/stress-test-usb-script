@echo off
setlocal EnableDelayedExpansion

set drive=%1
if "%drive:~-1%" == "\" set drive=%drive:~0,-1%
echo 正在重置磁碟機 %drive%

cd /d "%drive%\"
if errorlevel 1 (
    echo 無法切換到磁碟機 %drive%
    exit /b 1
)

:: 設定目標資料夾名稱
set "targetfolder=rtklog_usb"

:: 檢查目標資料夾是否存在
if exist "%targetfolder%" (
    echo Clearing files in %targetfolder%...

    :: 刪除所有檔案
    for /r "%targetfolder%" %%f in (*) do (
        echo Deleting file "%%~f"
        del /q /f "%%~f"
    )

    :: 刪除所有子資料夾
    for /d %%D in ("%targetfolder%\*") do (
        echo Deleting directory "%%~D"
        rmdir /s /q "%%~D"
    )

    echo All files and folders inside %targetfolder% have been deleted.
) else (
    echo The folder %targetfolder% does not exist.
)

:: 刪除檔案
echo Searching for files to delete...
for %%f in (
    "*CltvYoutubeNetflixHdmiPower*"
    "*bugreport*"
    "install.img"
    "*vmlinux.bin*"
    "*BOOTEX.LOG*"
    "*bluecore.video_ab.pkg*"
    "*tzfw*"
    "*dvrboot.rescue.exe.bin*"
    "*logbuf.log*"
) do (
    if exist "%%f" (
        echo Deleting file "%%f"
        del /q /f "%%f"
    )
)

:: 刪除資料夾
echo Searching for directories to delete...
for %%d in (
    "Android"
    "Alarms"
    "Audiobooks"
    "DCIM"
    "Documents"
    "Download"
    "Movies"
    "Music"
    "Notifications"
    "Pictures"
    "Podcasts"
    "Ringtones"
    "LOST.DIR"
    "Recordings"
) do (
    if exist "%targetfolder%\%%d" (
        echo Deleting directory %targetfolder%\%%d
        rmdir /s /q "%targetfolder%\%%d"
    )
)

echo All specified files and directories have been deleted.

REM 在這裡添加你的 USB 重置邏輯

@echo off
setlocal EnableDelayedExpansion

set drive=%1
if "%drive:~-1%" == "\" set drive=%drive:~0,-1%
echo 正在處理磁碟機 %drive%

cd /d "%drive%\"
if errorlevel 1 (
    echo 無法切換到磁碟機 %drive%
    exit /b 1
)

REM 在這裡添加你的檔案重命名邏輯

echo Searching for files containing 'install' in the name...
for %%f in (*install*) do (
    if exist "%%f" (
        echo Renaming "%%f" to "install.img"
        ren "%%f" "install.img"
    )
)

echo Searching for files containing 'dvrboot.rescue.exe.bin' in the name...
for %%f in (*dvrboot.rescue.exe*) do (
    if exist "%%f" (
            echo Renaming "%%f" to "dvrboot.rescue.exe.bin"
            ren "%%f" "dvrboot.rescue.exe.bin"
    )
)

echo Searching for files containing 'vmlinux.bin' in the name...
for %%f in (*vmlinux*) do (
    if exist "%%f" (
            echo Renaming "%%f" to "vmlinux.bin"
            ren "%%f" "vmlinux.bin"
    )
)

echo Searching for files containing 'bluecore.video_ab.pkg' in the name...
for %%f in (*bluecore.video*) do (
    if exist "%%f" (
            echo Renaming "%%f" to "bluecore.video_ab.pkg"
            ren "%%f" "bluecore.video_ab.pkg"
    )
)

echo Searching for files containing 'tzfw.pkg' in the name...
for %%f in (*tzfw*) do (
    if exist "%%f" (
            echo Renaming "%%f" to "tzfw.pkg"
            ren "%%f" "tzfw.pkg"
    )
)
echo All specified files have been renamed.
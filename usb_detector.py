import usb.core
import usb.util
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import logging
import win32api
import win32file
import os
import wmi

# Add logging configuration at the start of program
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 在檔案開頭添加批次檔內容作為常量
FILE_RENAME_BAT = '''@echo off
setlocal EnableDelayedExpansion

set drive=%1
if "%drive:~-1%" == "\\" set drive=%drive:~0,-1%
echo Processing drive %drive%

cd /d "%drive%\\"
if errorlevel 1 (
    echo Cannot switch to drive %drive%
    exit /b 1
)

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
'''

USB_RESET_BAT = '''@echo off
setlocal EnableDelayedExpansion

set drive=%1
if "%drive:~-1%" == "\\" set drive=%drive:~0,-1%
echo Resetting drive %drive%

cd /d "%drive%\\"
if errorlevel 1 (
    echo Cannot switch to drive %drive%
    exit /b 1
)

set "targetfolder=rtklog_usb"

if exist "%targetfolder%" (
    echo Clearing files in %targetfolder%...

    for /r "%targetfolder%" %%f in (*) do (
        echo Deleting file "%%~f"
        del /q /f "%%~f"
    )

    for /d %%D in ("%targetfolder%\\*") do (
        echo Deleting directory "%%~D"
        rmdir /s /q "%%~D"
    )

    echo All files and folders inside %targetfolder% have been deleted.
) else (
    echo The folder %targetfolder% does not exist.
)

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
    if exist "%%d" (
        echo Deleting directory %%d
        rmdir /s /q "%%d"
    )
)

echo All specified files and directories have been deleted.
'''

class USBDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stress Test USB Script ੯•́ʔ̋ ͙͛*͛ ͙͛*͛ ͙͛̋و")
        self.root.geometry("380x360")
        
        # Set window to fixed size
        self.root.resizable(False, False)

        # 延遲初始化 WMI
        self._wmi = None
        
        # Create main frame
        self.frame = ttk.Frame(root, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Create USB list with multiple selection support
        self.usb_listbox = tk.Listbox(self.frame, width=50, height=10, selectmode=tk.MULTIPLE)
        self.usb_listbox.grid(row=0, column=0, pady=5)

        # Create buttons frame
        self.buttons_frame = ttk.Frame(self.frame)
        self.buttons_frame.grid(row=1, column=0, pady=5)

        # Add checkbox for showing all devices
        self.show_all_devices = tk.BooleanVar(value=False)
        self.show_all_checkbox = ttk.Checkbutton(
            self.buttons_frame,
            text="Show All Drives",
            variable=self.show_all_devices,
            command=self.refresh_usb_list
        )
        self.show_all_checkbox.grid(row=0, column=0, padx=5)

        # Create refresh and select all buttons
        self.refresh_button = ttk.Button(self.buttons_frame, text="Refresh USB List", command=self.refresh_usb_list)
        self.refresh_button.grid(row=0, column=1, padx=5)

        # Add state tracking for select all button
        self.is_all_selected = False  # 初始化選擇狀態
        self.select_all_button = ttk.Button(self.buttons_frame, text="Select All", command=self.toggle_select_all)
        self.select_all_button.grid(row=0, column=2, padx=5)

        # Create options frame for radio buttons
        self.options_frame = ttk.LabelFrame(self.frame, text="Execute Options", padding="5")
        self.options_frame.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))

        # Create radio button variable with default value
        self.selected_action = tk.StringVar(value="rename")

        # Create radio buttons for different actions
        self.rename_radio = ttk.Radiobutton(
            self.options_frame, 
            text="Execute File_rename", 
            value="rename", 
            variable=self.selected_action
        )
        self.rename_radio.grid(row=0, column=0, padx=5, sticky=tk.W)

        self.reset_radio = ttk.Radiobutton(
            self.options_frame, 
            text="Execute USB_reset", 
            value="reset", 
            variable=self.selected_action
        )
        self.reset_radio.grid(row=1, column=0, padx=5, sticky=tk.W)

        # Create execute button
        self.execute_button = ttk.Button(self.frame, text="Execute Selected Program", command=self.execute_program)
        self.execute_button.grid(row=3, column=0, pady=5)

        # Add creator label at bottom right
        self.creator_label = ttk.Label(
            self.frame, 
            text="Created by HowTeoh", 
            font=("Arial", 8, "italic"),
            foreground="gray"
        )
        self.creator_label.grid(
            row=4,           # 在執行按鈕下方
            column=0, 
            pady=(0, 5),     # 上方不留空間，下方留 5 像素
            sticky=tk.E      # 靠右對齊
        )

        # Initialize USB list
        self.refresh_usb_list()

    @property
    def wmi(self):
        # 延遲載入 WMI
        if self._wmi is None:
            self._wmi = wmi.WMI()
        return self._wmi

    def get_volume_id(self, drive_letter):
        try:
            logger.debug(f"Attempting to get drive {drive_letter} information")
            
            query = f"SELECT * FROM Win32_LogicalDisk WHERE DeviceID = '{drive_letter}'"
            disk_info = self.wmi.query(query)[0]
            
            if disk_info.VolumeSerialNumber:
                serial = disk_info.VolumeSerialNumber
                volume_name = disk_info.VolumeName or "Unnamed"  # Display "Unnamed" if no name exists
                
                logger.debug(f"""
                    Drive: {drive_letter}
                    Volume Name: {volume_name}
                    Serial: {serial}
                    File System: {disk_info.FileSystem}
                """)
                
                return serial, volume_name
            else:
                return "No Serial", "Unnamed"
            
        except Exception as e:
            logger.error(f"Error getting drive {drive_letter} information: {str(e)}")
            return f"Error: {str(e)}", "Error"

    def refresh_usb_list(self):
        self.usb_listbox.delete(0, tk.END)
        self.usb_devices = []

        try:
            # 使用列表推導式優化
            logical_disks = [
                disk for disk in self.wmi.Win32_LogicalDisk()
                if disk.DriveType in [2, 3]  # 只獲取需要的磁碟類型
            ]
            
            found_target_device = False
            show_all = self.show_all_devices.get()  # 避免重複獲取
            
            for disk in logical_disks:
                try:
                    drive_letter = disk.DeviceID
                    drive_type = disk.DriveType
                    
                    volume_serial, volume_name = self.get_volume_id(drive_letter)
                    volume_serial = volume_serial.replace("-", "") if volume_serial else ""
                    
                    if volume_serial == "AAAAAAAA" or show_all:
                        found_target_device = True
                        device_type = "USB Drive" if drive_type == 2 else "Fixed Drive"
                        device_info = f"{device_type} {drive_letter} ({volume_name})"
                        
                        if volume_serial != "AAAAAAAA":
                            device_info += f" - {volume_serial}"
                        
                        self.usb_devices.append({
                            'drive_letter': drive_letter,
                            'drive_type': drive_type,
                            'volume_serial': volume_serial,
                            'volume_name': volume_name
                        })
                        self.usb_listbox.insert(tk.END, device_info)
                        
                except Exception as e:
                    logger.error(f"Error processing drive {drive_letter}: {str(e)}")
                    continue

            if not found_target_device:
                self.usb_listbox.insert(tk.END, "No device found")

        except Exception as e:
            logger.exception("Error detecting devices")
            messagebox.showerror("Error", f"Error detecting devices: {str(e)}")

    def execute_program(self):
        selections = self.usb_listbox.curselection()
        if not selections:
            messagebox.showwarning("Warning", "Please select at least one USB device")
            return

        action = self.selected_action.get()
        if action == "rename":
            batch_content = FILE_RENAME_BAT
            operation_name = "File Rename"
        else:  # action == "reset"
            batch_content = USB_RESET_BAT
            operation_name = "USB Reset"

        success_count = 0
        error_count = 0
        error_messages = []

        for selection in selections:
            selected_device = self.usb_devices[selection]
            drive_letter = selected_device['drive_letter']

            try:
                # 創建臨時批次檔
                temp_bat = os.path.join(os.environ['TEMP'], f'usb_operation_{os.getpid()}.bat')
                with open(temp_bat, 'w', encoding='utf-8') as f:
                    f.write(batch_content)

                try:
                    # 執行批次檔
                    process = subprocess.Popen(
                        [temp_bat, drive_letter],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True
                    )
                    
                    stdout, stderr = process.communicate()
                    output = stdout.decode('utf-8', errors='ignore')
                    logger.debug(f"Batch file output for drive {drive_letter}:\n{output}")
                    
                    if process.returncode == 0:
                        success_count += 1
                        logger.debug(f"Successfully executed {operation_name} on drive {drive_letter}")
                    else:
                        error_count += 1
                        error_msg = stderr.decode('utf-8', errors='ignore')
                        error_messages.append(f"Drive {drive_letter}: {error_msg}")
                        logger.error(f"Failed to execute {operation_name} on drive {drive_letter}: {error_msg}")
                
                finally:
                    # 清理臨時檔案
                    try:
                        os.remove(temp_bat)
                    except:
                        pass
                    
            except Exception as e:
                error_count += 1
                error_messages.append(f"Drive {drive_letter}: {str(e)}")
                logger.error(f"Error executing {operation_name} on drive {drive_letter}: {str(e)}")

        # Show execution summary
        if error_count == 0:
            messagebox.showinfo("Success", f"Successfully executed {operation_name} on {success_count} device(s)")
        else:
            error_summary = "\n".join(error_messages)
            messagebox.showwarning(
                "Execution Result", 
                f"Success: {success_count} device(s)\n"
                f"Failed: {error_count} device(s)\n\n"
                f"Error Details:\n{error_summary}"
            )

    def toggle_select_all(self):
        """Toggle between select all and deselect all"""
        if self.is_all_selected:
            # If currently all selected, deselect all
            self.usb_listbox.selection_clear(0, tk.END)
            self.select_all_button.configure(text="Select All")
        else:
            # If not all selected, select all
            for i in range(self.usb_listbox.size()):
                self.usb_listbox.selection_set(i)
            self.select_all_button.configure(text="Deselect All")
        
        # Toggle the state
        self.is_all_selected = not self.is_all_selected

def main():
    # 直接啟動主程式，不進行圖示轉換
    root = tk.Tk()
    app = USBDetectorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
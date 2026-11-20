#!/usr/bin/env python3
import subprocess
import time
import os
from pathlib import Path

OUT_DIR = Path("docs/recordings")

def run():
    print("--- Preparing MainActivity for Flow 2 ---")
    subprocess.run("adb shell am start -S -n com.example.loss/.ui.main.MainActivity", shell=True)
    time.sleep(2.0)
    
    mp4_device = "/sdcard/flow2.mp4"
    mp4_local = "/tmp/flow2.mp4"
    gif_out = OUT_DIR / "flow2_submission.gif"
    
    print("--- Starting screenrecord (8s) ---")
    proc = subprocess.Popen(["adb", "shell", "screenrecord", "--time-limit", "8", "--bit-rate", "6000000", mp4_device])
    
    time.sleep(1.0)
    # Tap "+ подать объявление"
    subprocess.run("adb shell input tap 540 803", shell=True)
    time.sleep(1.5)
    # Tap radio "Я потерял вещь"
    subprocess.run("adb shell input tap 783 938", shell=True)
    time.sleep(1.2)
    # Tap Description edittext
    subprocess.run("adb shell input tap 540 1439", shell=True)
    time.sleep(0.5)
    subprocess.run("adb shell input text 'Logitech_Wireless_Mouse'", shell=True)
    time.sleep(0.8)
    # Hide keyboard
    subprocess.run("adb shell input keyevent 4", shell=True)
    time.sleep(1.5)
    # Tap back
    subprocess.run("adb shell input tap 94 168", shell=True)
    
    proc.wait()
    print("--- Screenrecord finished. Pulling MP4 ---")
    subprocess.run(f"adb pull {mp4_device} {mp4_local}", shell=True)
    
    print("--- Converting MP4 to GIF (1080x2400) ---")
    ffmpeg_cmd = (
        f"ffmpeg -y -i '{mp4_local}' "
        f"-vf \"fps=12,scale=1080:2400:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer\" "
        f"'{gif_out}'"
    )
    subprocess.run(ffmpeg_cmd, shell=True, check=True)
    print(f"Flow 2 complete! Size: {gif_out.stat().st_size} bytes")

if __name__ == '__main__':
    run()

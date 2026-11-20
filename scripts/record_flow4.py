#!/usr/bin/env python3
import subprocess
import time
from pathlib import Path

OUT_DIR = Path("docs/recordings")

def run():
    print("--- Preparing MainActivity for Flow 4 ---")
    subprocess.run("adb shell am start -S -n com.example.loss/.ui.main.MainActivity", shell=True)
    time.sleep(2.0)
    
    mp4_device = "/sdcard/flow4.mp4"
    mp4_local = "/tmp/flow4.mp4"
    gif_out = OUT_DIR / "flow4_profile.gif"
    
    print("--- Starting screenrecord (9s) ---")
    proc = subprocess.Popen(["adb", "shell", "screenrecord", "--time-limit", "9", "--bit-rate", "6000000", mp4_device])
    
    time.sleep(1.0)
    # Tap "👤 Профиль" (894, 149)
    subprocess.run("adb shell input tap 894 149", shell=True)
    time.sleep(1.8)
    # Tap first card in profile (iPhone 13) at (500, 1500)
    subprocess.run("adb shell input tap 500 1500", shell=True)
    time.sleep(1.5)
    # Scroll down to reveal author PIN code block
    subprocess.run("adb shell input swipe 500 1800 500 1200 300", shell=True)
    time.sleep(2.5)
    # Tap back
    subprocess.run("adb shell input tap 100 168", shell=True)
    
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
    print(f"Flow 4 complete! Size: {gif_out.stat().st_size} bytes")

if __name__ == '__main__':
    run()

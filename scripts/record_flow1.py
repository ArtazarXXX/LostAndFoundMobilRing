#!/usr/bin/env python3
import subprocess
import time
import os
from pathlib import Path

OUT_DIR = Path("docs/recordings")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def run():
    print("--- Preparing MainActivity for Flow 1 ---")
    subprocess.run("adb shell am start -S -n com.example.loss/.ui.main.MainActivity", shell=True)
    time.sleep(2.0)
    
    mp4_device = "/sdcard/flow1.mp4"
    mp4_local = "/tmp/flow1.mp4"
    gif_out = OUT_DIR / "flow1_main_feed.gif"
    
    print("--- Starting screenrecord (8s) ---")
    proc = subprocess.Popen(["adb", "shell", "screenrecord", "--time-limit", "8", "--bit-rate", "6000000", mp4_device])
    
    time.sleep(1.0)
    # Scroll down smoothly
    subprocess.run("adb shell input swipe 500 1600 500 1050 400", shell=True)
    time.sleep(1.5)
    # Tap tab "Пропажи" (783, 302)
    subprocess.run("adb shell input tap 783 302", shell=True)
    time.sleep(1.5)
    # Tap chip "👟 Сменка" (312, 584)
    subprocess.run("adb shell input tap 312 584", shell=True)
    time.sleep(1.5)
    # Tap chip "Все" (107, 584)
    subprocess.run("adb shell input tap 107 584", shell=True)
    time.sleep(0.8)
    # Tap tab "Находки" (296, 302)
    subprocess.run("adb shell input tap 296 302", shell=True)
    
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
    print(f"Flow 1 complete! Size: {gif_out.stat().st_size} bytes")

if __name__ == '__main__':
    run()

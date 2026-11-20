#!/usr/bin/env python3
import subprocess
import time
from pathlib import Path

OUT_DIR = Path("docs/recordings")

def run():
    print("--- Preparing MainActivity for Flow 5 ---")
    subprocess.run("adb shell am start -S -n com.example.loss/.ui.main.MainActivity", shell=True)
    time.sleep(2.0)
    
    mp4_device = "/sdcard/flow5.mp4"
    mp4_local = "/tmp/flow5.mp4"
    gif_out = OUT_DIR / "flow5_chat.gif"
    
    print("--- Starting screenrecord (10s) ---")
    proc = subprocess.Popen(["adb", "shell", "screenrecord", "--time-limit", "10", "--bit-rate", "6000000", mp4_device])
    
    time.sleep(1.0)
    # Tap first card
    subprocess.run("adb shell input tap 500 1300", shell=True)
    time.sleep(1.5)
    # Scroll down to btnChat
    subprocess.run("adb shell input swipe 500 1800 500 1200 300", shell=True)
    time.sleep(1.0)
    # Tap btnChat (540, 2029)
    subprocess.run("adb shell input tap 540 2029", shell=True)
    time.sleep(1.5)
    # Tap message input (375, 2242)
    subprocess.run("adb shell input tap 375 2242", shell=True)
    time.sleep(0.5)
    # Type message
    subprocess.run("adb shell input text 'Budu%su%skabineta%sna%speremene!'", shell=True)
    time.sleep(1.0)
    # Tap Send button (894, 2242)
    subprocess.run("adb shell input tap 894 2242", shell=True)
    time.sleep(2.0)
    # Tap back
    subprocess.run("adb shell input tap 94 206", shell=True)
    
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
    print(f"Flow 5 complete! Size: {gif_out.stat().st_size} bytes")

if __name__ == '__main__':
    run()

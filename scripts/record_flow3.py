#!/usr/bin/env python3
import subprocess
import time
import sqlite3
from pathlib import Path

OUT_DIR = Path("docs/recordings")

def run():
    print("--- Resetting item 7 to accept in DB ---")
    conn = sqlite3.connect('backend/maindb.db')
    c = conn.cursor()
    c.execute("UPDATE items SET status = 'accept' WHERE id = 7")
    conn.commit()
    conn.close()

    print("--- Preparing MainActivity for Flow 3 ---")
    subprocess.run("adb shell am start -S -n com.example.loss/.ui.main.MainActivity", shell=True)
    time.sleep(2.0)
    
    # Swipe past the first item so item 7 (pencil case) is in view
    subprocess.run("adb shell input swipe 500 2000 500 600 300", shell=True)
    time.sleep(1.0)
    
    mp4_device = "/sdcard/flow3.mp4"
    mp4_local = "/tmp/flow3.mp4"
    gif_out = OUT_DIR / "flow3_safe_handover.gif"
    
    print("--- Starting screenrecord (11s) ---")
    proc = subprocess.Popen(["adb", "shell", "screenrecord", "--time-limit", "11", "--bit-rate", "6000000", mp4_device])
    
    time.sleep(1.0)
    # Tap item 7 (center at 500, 1000)
    subprocess.run("adb shell input tap 500 1000", shell=True)
    time.sleep(1.5)
    # Scroll down to reveal Handover block
    subprocess.run("adb shell input swipe 500 1800 500 1200 300", shell=True)
    time.sleep(1.2)
    # Tap "Ввести проверочный код от автора" (540, 1779)
    subprocess.run("adb shell input tap 540 1779", shell=True)
    time.sleep(1.2)
    # Input 5812
    subprocess.run("adb shell input text '5812'", shell=True)
    time.sleep(1.0)
    # Tap "Подтвердить" (829, 1406)
    subprocess.run("adb shell input tap 829 1406", shell=True)
    time.sleep(1.5)
    # Tap "Отлично" in success dialog (872, 1332)
    subprocess.run("adb shell input tap 872 1332", shell=True)
    time.sleep(1.5)
    
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
    print(f"Flow 3 complete! Size: {gif_out.stat().st_size} bytes")

if __name__ == '__main__':
    run()

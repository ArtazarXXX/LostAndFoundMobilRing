#!/usr/bin/env python3
import subprocess
import time
import os
from pathlib import Path

OUT_DIR = Path("docs/recordings")
FRAMES_DIR = OUT_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

def adb(cmd):
    if isinstance(cmd, str):
        return subprocess.run(f"adb {cmd}", shell=True, capture_output=True, text=True)
    return subprocess.run(["adb"] + cmd, capture_output=True, text=True)

def tap(x, y):
    adb(f"shell input tap {x} {y}")
    time.sleep(1.0)

def swipe(x1, y1, x2, y2, duration=300):
    adb(f"shell input swipe {x1} {y1} {x2} {y2} {duration}")
    time.sleep(1.2)

def keyevent(code):
    adb(f"shell input keyevent {code}")
    time.sleep(0.8)

def input_text(txt):
    adb(f"shell input text '{txt}'")
    time.sleep(0.8)

def capture(name):
    target = FRAMES_DIR / f"{name}.png"
    cmd = f"adb exec-out screencap -p > '{target}'"
    subprocess.run(cmd, shell=True)
    time.sleep(0.5)
    print(f"Captured: {target}")
    return target

def compile_gif(frame_names, durations, output_gif_name):
    """
    frame_names: list of frame base names
    durations: list of float durations in seconds for each frame
    output_gif_name: name of output GIF
    """
    concat_txt = FRAMES_DIR / f"concat_{output_gif_name}.txt"
    with open(concat_txt, "w") as f:
        for name, dur in zip(frame_names, durations):
            p = FRAMES_DIR / f"{name}.png"
            f.write(f"file '{p.resolve()}'\n")
            f.write(f"duration {dur}\n")
        # repeat last frame to avoid ffmpeg dropping it
        last_p = FRAMES_DIR / f"{frame_names[-1]}.png"
        f.write(f"file '{last_p.resolve()}'\n")

    out_gif = OUT_DIR / output_gif_name
    ffmpeg_cmd = (
        f"ffmpeg -y -f concat -safe 0 -i '{concat_txt}' "
        f"-vf \"fps=10,scale=1080:2400:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer\" "
        f"'{out_gif}'"
    )
    subprocess.run(ffmpeg_cmd, shell=True, check=True)
    print(f"Compiled GIF: {out_gif} ({out_gif.stat().st_size} bytes)")

def reset_to_main():
    adb("shell am start -n com.example.loss/.ui.main.MainActivity")
    time.sleep(1.5)

def run_all():
    print("=== STARTING CAPTURES ===")
    
    # -------------------------------------------------------------
    # FLOW 1: Main Feed & Tabs & Filter Chips (for Slide 5 & 6)
    # -------------------------------------------------------------
    print("\n--- Flow 1: Main Feed & Categories ---")
    reset_to_main()
    capture("f1_1_found_feed")
    swipe(500, 1800, 500, 900, 350)
    capture("f1_2_found_scrolled")
    tap(750, 260) # tap "Пропажи" tab
    capture("f1_3_lost_tab")
    tap(300, 480) # tap "Сменка"
    capture("f1_4_filter_clothes")
    tap(85, 480)  # tap "Все"
    tap(250, 260) # tap "Находки"
    time.sleep(1)

    compile_gif(
        ["f1_1_found_feed", "f1_2_found_scrolled", "f1_3_lost_tab", "f1_4_filter_clothes"],
        [2.2, 2.2, 2.2, 2.5],
        "flow1_main_feed.gif"
    )

    # -------------------------------------------------------------
    # FLOW 2: Submission Form (for Slide 6 / 7)
    # -------------------------------------------------------------
    print("\n--- Flow 2: Submission Form ---")
    reset_to_main()
    tap(320, 660) # tap "+ подать объявление"
    capture("f2_1_empty_form")
    tap(600, 790) # tap radio "Я потерял вещь"
    capture("f2_2_radio_lost")
    # tap description
    tap(400, 1200)
    input_text("Беспроводная_мышь_Logitech")
    keyevent(4) # hide keyboard
    # tap place
    tap(400, 1450)
    input_text("Кабинет_204")
    keyevent(4) # hide keyboard
    capture("f2_3_filled_form")
    keyevent(4) # back to main
    time.sleep(1)

    compile_gif(
        ["f2_1_empty_form", "f2_2_radio_lost", "f2_3_filled_form"],
        [2.0, 2.0, 3.0],
        "flow2_submission.gif"
    )

    # -------------------------------------------------------------
    # FLOW 3: Safe Handover / PIN Verification (for Slide 8 - Innovation)
    # -------------------------------------------------------------
    print("\n--- Flow 3: Safe Handover (PIN) ---")
    reset_to_main()
    # open item (pencil case or umbrella)
    swipe(500, 1800, 500, 1200, 300)
    tap(500, 1500) # open item card
    time.sleep(1)
    capture("f3_1_item_card")
    # scroll down to see handover card
    swipe(500, 1800, 500, 1200, 300)
    capture("f3_2_handover_block")
    # tap "Ввести проверочный код от автора"
    tap(500, 1780)
    capture("f3_3_dialog_prompt")
    # input 4-digit code (e.g. 5812)
    input_text("5812")
    capture("f3_4_dialog_code")
    # tap "Подтвердить"
    tap(780, 1410)
    time.sleep(1.5)
    capture("f3_5_success_modal")
    # tap "Отлично"
    keyevent(4)
    time.sleep(0.5)
    capture("f3_6_status_returned")
    keyevent(4) # back to main
    time.sleep(1)

    compile_gif(
        ["f3_1_item_card", "f3_2_handover_block", "f3_3_dialog_prompt", "f3_4_dialog_code", "f3_5_success_modal", "f3_6_status_returned"],
        [2.0, 2.0, 2.0, 2.0, 2.5, 2.5],
        "flow3_safe_handover.gif"
    )

    # -------------------------------------------------------------
    # FLOW 4: Profile & Anti-Self-Return Protection (for Slide 9)
    # -------------------------------------------------------------
    print("\n--- Flow 4: Profile & Anti-Self-Return ---")
    reset_to_main()
    tap(900, 130) # tap "👤 Профиль"
    capture("f4_1_profile_counters")
    swipe(500, 1800, 500, 1000, 300)
    capture("f4_2_my_items")
    # tap MacBook (user's item)
    tap(500, 1900)
    capture("f4_3_author_view_code")
    keyevent(4)
    keyevent(4)
    time.sleep(1)

    compile_gif(
        ["f4_1_profile_counters", "f4_2_my_items", "f4_3_author_view_code"],
        [2.5, 2.5, 3.0],
        "flow4_profile.gif"
    )

    # -------------------------------------------------------------
    # FLOW 5: In-App P2P Chat (for Slide 10)
    # -------------------------------------------------------------
    print("\n--- Flow 5: In-App P2P Chat ---")
    reset_to_main()
    # open first item (headphones)
    tap(500, 1200)
    time.sleep(1)
    # scroll down and tap "💬 Написать автору"
    swipe(500, 1800, 500, 1200, 300)
    tap(500, 2150)
    time.sleep(1)
    capture("f5_1_chat_dialogue")
    # tap input field
    tap(400, 2300)
    input_text("Здравствуйте!_Зайду_после_4_урока.")
    keyevent(4) # hide keyboard
    capture("f5_2_chat_typed")
    # tap Send button
    tap(1000, 2300)
    time.sleep(1)
    capture("f5_3_chat_sent")
    keyevent(4)
    keyevent(4)
    time.sleep(1)

    compile_gif(
        ["f5_1_chat_dialogue", "f5_2_chat_typed", "f5_3_chat_sent"],
        [2.5, 2.0, 3.0],
        "flow5_chat.gif"
    )

    print("\n=== ALL FLOWS CAPTURED AND COMPILED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run_all()

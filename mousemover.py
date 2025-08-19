import pyautogui
import random
import time
import keyboard  # pip install keyboard

screen_width, screen_height = pyautogui.size()

print("Press ESC to stop.")

while True:
    if keyboard.is_pressed('esc'):
        print("Script stopped by user.")
        break

    x = random.randint(0, screen_width - 1)
    y = random.randint(0, screen_height - 1)
    pyautogui.moveTo(x, y, duration=0.5)
    pyautogui.click()
    time.sleep(random.uniform(0.5, 2))

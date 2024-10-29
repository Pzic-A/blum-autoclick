import math
import os
import random
import sys
import time

import cv2
import keyboard
import mss
import numpy as np
import pygetwindow as gw
import win32api
import win32con


def resource_path(relative_path):
    """ Get image files if the application is opened via .exe """
    try:
        base_path = sys._MEIPASS
        return str(os.path.join(base_path, relative_path))
    except Exception:
        return relative_path


class Logger:
    def __init__(self, prefix=None):
        self.prefix = prefix

    def log(self, data: str):
        if self.prefix:
            print(f"{self.prefix} {data}")
        else:
            print(data)

    def input(self, text: str):
        if self.prefix:
            return input(f"{self.prefix} {text}")
        else:
            return input(text)


class AutoClicker:
    def __init__(self, window_title, target_colors_hex, nearby_colors_hex, logger, percentages: float,
                 is_continue: bool):
        self.window_title = window_title
        self.target_colors_hex = target_colors_hex
        self.nearby_colors_hex = nearby_colors_hex
        self.logger = logger
        self.running = False
        self.clicked_points = []
        self.iteration_count = 0

        self.percentage_click = percentages
        self.is_continue = is_continue

        self.target_hsvs = [self.hex_to_hsv(color) for color in self.target_colors_hex]
        self.nearby_hsvs = [self.hex_to_hsv(color) for color in self.nearby_colors_hex]

        self.templates_plays = [
            cv2.cvtColor(cv2.imread(img, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2GRAY) for img in CLICK_IMAGES
        ]  # images to click on
        self.template_lobby = cv2.cvtColor(cv2.imread(LOBBY_IMAGE, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2GRAY)

    @staticmethod
    def hex_to_hsv(hex_color):
        hex_color = hex_color.lstrip('#')
        h_len = len(hex_color)
        rgb = tuple(int(hex_color[i:i + h_len // 3], 16) for i in range(0, h_len, h_len // 3))
        rgb_normalized = np.array([[rgb]], dtype=np.uint8)
        hsv = cv2.cvtColor(rgb_normalized, cv2.COLOR_RGB2HSV)
        return hsv[0][0]

    @staticmethod
    def click_at(x, y):
        win32api.SetCursorPos((x, y))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

    def toggle_script(self):
        self.running = not self.running
        r_text = "on" if self.running else "off"
        self.logger.log(f'Status changed: {r_text}')

    def is_near_color(self, hsv_img, center, target_hsvs, radius=8):
        x, y = center
        height, width = hsv_img.shape[:2]
        for i in range(max(0, x - radius), min(width, x + radius + 1)):
            for j in range(max(0, y - radius), min(height, y + radius + 1)):
                distance = math.sqrt((x - i) ** 2 + (y - j) ** 2)
                if distance <= radius:
                    pixel_hsv = hsv_img[j, i]
                    for target_hsv in target_hsvs:
                        if np.allclose(pixel_hsv, target_hsv, atol=[1, 50, 50]):
                            return True
        return False

    def is_lobby_screen(self, screen):
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)

        result = cv2.matchTemplate(screen_gray, self.template_lobby, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        if max_val >= 0.6:
            return True
        
        return False

    def scroll_down(self, monitor):
        time.sleep(0.5)
        # Calculate the center of the screen based on the monitor dimensions
        center_x = monitor["left"] + monitor["width"] // 2
        center_y = monitor["top"] + monitor["height"] // 2
        # Move the mouse to the center of the screen
        win32api.SetCursorPos((center_x, center_y))
        # Simulate scrolling down
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -140, 0)  # Scroll down
        time.sleep(0.5)  # Wait for the scroll action to take effect

    def random_wait(self, min_seconds=5, max_seconds=10):
        """
        Sleep for a random duration between min_seconds and max_seconds.

        Args:
            min_seconds (int): Minimum number of seconds to wait.
            max_seconds (int): Maximum number of seconds to wait.
        """
        wait_time = random.uniform(min_seconds, max_seconds)
        print(f"Wait for {wait_time:.2f} seconds.")
        time.sleep(wait_time)

    def find_and_click_image(self, template_gray, screen, monitor):
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGRA2GRAY)

        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.6:
            self.random_wait()
            template_height, template_width = template_gray.shape
            center_x = max_loc[0] + template_width // 2 + monitor["left"]
            center_y = max_loc[1] + template_height // 2 + monitor["top"]
            self.click_at(center_x, center_y)
            return True
        else:
            is_lobby_screen = self.is_lobby_screen(screen, )
            # print(f"is_lobby_screen : {is_lobby_screen}")
            if is_lobby_screen:
                self.scroll_down(monitor)

        return False

    def click_color_areas(self):
        windows = gw.getWindowsWithTitle(self.window_title)
        if not windows:
            self.logger.log(
                f"No window found with title: {self.window_title}. Open the Blum web application and restart the script")
            return
        # print(windows[0])
        window = windows[0]
        for w in windows:
            if w.left > 0:
                window = w
                break
        
        # print(window)
        if window.isMinimized:
            window.restore() # Restore the window if it is minimized.
        window.activate()

        # Load the target image for template matching
        target_image = cv2.imread(DOGS_IMAGE, cv2.IMREAD_COLOR)
        target_height, target_width = target_image.shape[:2]

        with mss.mss() as sct:
            grave_key_code = 41
            keyboard.add_hotkey(grave_key_code, self.toggle_script)

            while True:
                if self.running:
                    monitor = {
                        "top": window.top,
                        "left": window.left,
                        "width": window.width,
                        "height": window.height
                    }
                    img = np.array(sct.grab(monitor))
                    img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

                    for target_hsv in self.target_hsvs:
                        lower_bound = np.array([max(0, target_hsv[0] - 1), 30, 30])
                        upper_bound = np.array([min(179, target_hsv[0] + 1), 255, 255])
                        mask = cv2.inRange(hsv, lower_bound, upper_bound)
                        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                        for contour in reversed(contours):
                            if random.random() >= self.percentage_click:
                                continue

                            if cv2.contourArea(contour) < 8:
                                continue

                            M = cv2.moments(contour)
                            if M["m00"] == 0:
                                continue
                            cX = int(M["m10"] / M["m00"]) + monitor["left"]
                            cY = int(M["m01"] / M["m00"]) + monitor["top"]

                            if not self.is_near_color(hsv, (cX - monitor["left"], cY - monitor["top"]),
                                                      self.nearby_hsvs):
                                continue

                            if any(math.sqrt((cX - px) ** 2 + (cY - py) ** 2) < 35 for px, py in self.clicked_points):
                                continue
                            cY += 7
                            self.click_at(cX, cY)
                            self.logger.log(f'Clicked at: {cX} {cY}')
                            self.clicked_points.append((cX, cY))
                    enabled_dogs = False
                    if enabled_dogs:
                        # Prepare scaled templates only once
                        scale_factors = np.linspace(1, 2, 5)  # Adjust number of scales as needed
                        resized_targets = {scale: cv2.resize(target_image, (int(target_width * scale), int(target_height * scale))) for scale in scale_factors}
                        threshold = 0.7  # Adjust threshold if needed

                        for scale, resized_target in resized_targets.items():
                            result = cv2.matchTemplate(img_bgr, resized_target, cv2.TM_CCOEFF_NORMED)
                            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                            if max_val >= threshold:
                                click_x = max_loc[0] + resized_target.shape[1] // 2 + monitor["left"]
                                click_y = max_loc[1] + resized_target.shape[0] // 2 + monitor["top"]

                                # Adjust `click_y` downward based on scale
                                downward_offset = int((scale - 1.0) * target_height * 0.1)
                                click_y += downward_offset

                                self.click_at(click_x, click_y)
                                self.logger.log(f'Clicked on template at: {click_x}, {click_y}, scale: {scale:.2f}')
                                self.clicked_points.append((click_x, click_y))
                                break  # Stop after the first successful match

                    time.sleep(0.222)
                    self.iteration_count += 1
                    if self.iteration_count >= 5:
                        self.clicked_points.clear()
                        if self.is_continue:
                            for tp in self.templates_plays:
                                self.find_and_click_image(tp, img, monitor)
                        self.iteration_count = 0


if __name__ == "__main__":
    logger = Logger("[Blum auto bot...]")
    logger.log("Welcome to the free script - autoclicker for the game Blum")
    CLICK_IMAGES = [resource_path("media\\lobby-play.png"), resource_path("media\\continue-play.png")]
    LOBBY_IMAGE = resource_path("media\\farming-lobby.png")
    DOGS_IMAGE = resource_path("media\\dogs.png")

    PERCENTAGES = {
        "1": 0.13,  # 100
        "2": 0.17,  # 150
        "3": 0.235,  # 175
        "4": 1,
    }

    # request the desired number of points
    answer = None
    while answer is None:
        points_key = logger.input(
            "Specify the desired number of points | 1 -> 90-110 | 2 -> 140-160 | 3 -> 170-180 | 4 -> MAX: ")
        answer = PERCENTAGES.get(points_key, None)
        if answer is None:
            logger.log("Invalid value")
    percentages = answer

    # ask whether to click 'Play'
    answer = None
    answs = {
        "1": True,
        "0": False
    }
    while answer is None:
        points_key = logger.input("Does the bot continue games automatically? | 1 - yes / 0 - no: ")
        answer = answs.get(points_key, None)
        if answer is None:
            logger.log("Invalid value")
    is_continue = answer

    logger.log('After starting the mini-game, press the "`" key on the keyboard')
    # target_colors_hex = ["#c9e100", "#bae70e", "#da7d3f"]
    # nearby_colors_hex = ["#abff61", "#87ff27", "#60402d"]
    target_colors_hex = ["#da7d3f", "#e47d37", "#e27a34", "#e37a33"]
    nearby_colors_hex = ["#c25f27", "#60402d", "#c6642f", "#c46229"]
    auto_clicker = AutoClicker("TelegramDesktop", target_colors_hex, nearby_colors_hex, logger, percentages=percentages,
                               is_continue=is_continue)
    try:
        auto_clicker.click_color_areas()
    except Exception as e:
        logger.log(f"An error occurred: {e}")
    for i in reversed(range(5)):
        i += 1
        print(f"The script will terminate in {i} seconds")
        time.sleep(1)
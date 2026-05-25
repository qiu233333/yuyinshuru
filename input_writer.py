from __future__ import annotations

import time

import keyboard
import pyperclip


class InputWriter:
    def __init__(self, auto_paste: bool = True, paste_delay_seconds: float = 0.2) -> None:
        self.auto_paste = auto_paste
        self.paste_delay_seconds = paste_delay_seconds

    def write(self, text: str) -> None:
        clean_text = text.strip()
        if not clean_text:
            return

        pyperclip.copy(clean_text)

        if self.auto_paste:
            self._wait_for_hotkey_release()
            time.sleep(self.paste_delay_seconds)
            keyboard.press_and_release("ctrl+v")

    @staticmethod
    def _wait_for_hotkey_release(timeout_seconds: float = 2.0) -> None:
        deadline = time.monotonic() + timeout_seconds
        watched_keys = ("ctrl", "alt", "space")

        while time.monotonic() < deadline:
            if not any(keyboard.is_pressed(key) for key in watched_keys):
                return
            time.sleep(0.03)

from __future__ import annotations

import sys
import threading
import time

import keyboard

from config import ConfigError, Settings, load_config_values, load_settings
from input_writer import InputWriter
from recorder import AudioRecorder
from settings_window import show_settings_window
from transcriber import Transcriber
from text_polisher import TextPolisher, TextPolisherError


class VoiceInputApp:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.recorder = AudioRecorder(output_dir=settings.audio_output_dir)
        self.transcriber = Transcriber(
            app_id=settings.baidu_app_id,
            api_key=settings.baidu_api_key,
            secret_key=settings.baidu_secret_key,
        )
        self.text_polisher = TextPolisher(
            api_key=settings.deepseek_api_key,
            model=settings.deepseek_model,
        )
        self.input_writer = InputWriter(
            auto_paste=settings.auto_paste,
            paste_delay_seconds=settings.paste_delay_seconds,
        )
        self._state_lock = threading.Lock()
        self._processing = False
        self._hotkey_handle: int | None = None

    def run(self) -> None:
        self._hotkey_handle = keyboard.add_hotkey(
            self.settings.hotkey,
            self.toggle_recording,
            suppress=False,
            trigger_on_release=False,
        )

        print("Voice input assistant is running.")
        print(f"Hotkey: {self.settings.hotkey}")
        print("Press the hotkey once to start recording, then again to stop.")
        print("Press Ctrl+C in this console to exit.")

        try:
            while True:
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        if self._hotkey_handle is not None:
            keyboard.remove_hotkey(self._hotkey_handle)
            self._hotkey_handle = None

        if self.recorder.is_recording:
            try:
                path = self.recorder.stop()
                print(f"Recording stopped and saved to: {path}")
            except Exception as exc:
                print(f"Could not stop active recording cleanly: {exc}", file=sys.stderr)

    def toggle_recording(self) -> None:
        with self._state_lock:
            if self._processing:
                print("Still processing the previous recording. Please wait.")
                return

            if not self.recorder.is_recording:
                self._start_recording()
                return

            self._processing = True

        worker = threading.Thread(target=self._stop_and_transcribe, daemon=True)
        worker.start()

    def _start_recording(self) -> None:
        try:
            self.recorder.start()
        except Exception as exc:
            print(f"Could not start recording: {exc}", file=sys.stderr)
            return

        print("Recording started...")

    def _stop_and_transcribe(self) -> None:
        try:
            audio_path = self.recorder.stop()
            print(f"Recording saved to: {audio_path}")

            status = self.recorder.last_status
            if status:
                print(f"Audio device warning: {status}")

            print("Transcribing with Baidu ASR...")
            raw_text = self.transcriber.transcribe(audio_path)
            if not raw_text:
                print("No text was recognized.")
                return

            print(f"Raw text: {raw_text}")
            print("Polishing with DeepSeek...")
            text = self._polish_text(raw_text)
            print("Copying text to clipboard and pasting...")
            self.input_writer.write(text)
            print(f"Text copied{' and pasted' if self.settings.auto_paste else ''}:")
            print(text)
        except Exception as exc:
            print(f"Processing failed: {exc}", file=sys.stderr)
        finally:
            with self._state_lock:
                self._processing = False

    def _polish_text(self, raw_text: str) -> str:
        try:
            polished_text = self.text_polisher.polish(raw_text)
        except TextPolisherError as exc:
            print(
                f"DeepSeek polishing failed, using Baidu raw text: {exc}",
                file=sys.stderr,
            )
            return raw_text

        return polished_text or raw_text


def main() -> int:
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"Configuration needs setup: {exc}")
        try:
            initial_values = load_config_values()
        except ConfigError:
            initial_values = {}

        if not show_settings_window(initial_values):
            print("Configuration was not saved. Exiting.", file=sys.stderr)
            return 2

        try:
            settings = load_settings()
        except ConfigError as reload_exc:
            print(f"Configuration error: {reload_exc}", file=sys.stderr)
            return 2

    try:
        VoiceInputApp(settings).run()
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

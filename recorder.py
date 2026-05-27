from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np
import sounddevice as sd
from scipy.io import wavfile


AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1


class RecorderError(RuntimeError):
    """Raised when recording cannot start or stop cleanly."""


class AudioRecorder:
    def __init__(self, output_dir: Path) -> None:
        self.sample_rate = AUDIO_SAMPLE_RATE
        self.channels = AUDIO_CHANNELS
        self.output_dir = output_dir
        self.device_index: int | None = None
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._last_status: str | None = None
        self._lock = Lock()

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._stream is not None

    @property
    def last_status(self) -> str | None:
        with self._lock:
            return self._last_status

    def start(self) -> None:
        with self._lock:
            if self._stream is not None:
                raise RecorderError("Recording is already running.")

            self.output_dir.mkdir(parents=True, exist_ok=True)
            self._frames = []
            self._last_status = None
            self.device_index = _find_input_device_index()
            self._stream = sd.InputStream(
                device=self.device_index,
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=self._audio_callback,
            )

        try:
            self._stream.start()
        except Exception:
            with self._lock:
                self._stream = None
                self._frames = []
            raise

    def stop(self) -> Path:
        with self._lock:
            stream = self._stream
            if stream is None:
                raise RecorderError("Recording is not running.")
            self._stream = None

        stream.stop()
        stream.close()

        with self._lock:
            frames = self._frames
            self._frames = []

        if not frames:
            raise RecorderError("No audio frames were captured.")

        audio = np.concatenate(frames, axis=0)
        audio = np.clip(audio.reshape(-1), -1.0, 1.0)
        pcm16 = (audio * np.iinfo(np.int16).max).astype(np.int16)

        output_path = self._next_output_path()
        wavfile.write(output_path, self.sample_rate, pcm16)
        return output_path

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict[str, Any],
        status: sd.CallbackFlags,
    ) -> None:
        del frames, time_info

        if status:
            with self._lock:
                self._last_status = str(status)

        with self._lock:
            self._frames.append(indata.copy())

    def _next_output_path(self) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = self.output_dir / f"recording_{timestamp}.wav"
        if not base_path.exists():
            return base_path

        counter = 1
        while True:
            candidate = self.output_dir / f"recording_{timestamp}_{counter}.wav"
            if not candidate.exists():
                return candidate
            counter += 1


def _find_input_device_index() -> int:
    try:
        default_input = sd.query_devices(kind="input")
        default_index = _device_index_from_info(default_input)
        if default_index is not None:
            return default_index
    except Exception:
        pass

    devices = sd.query_devices()
    input_devices: list[tuple[int, str]] = []
    for index, device in enumerate(devices):
        if int(device.get("max_input_channels", 0)) > 0:
            input_devices.append((index, str(device.get("name", "Unknown device"))))

    if input_devices:
        return input_devices[0][0]

    raise RecorderError(
        "No microphone input device was found. Please connect or enable a microphone "
        "and set it as the default Windows input device."
    )


def _device_index_from_info(device_info: Any) -> int | None:
    index = device_info.get("index") if isinstance(device_info, dict) else None
    if isinstance(index, int) and index >= 0:
        return index

    return None

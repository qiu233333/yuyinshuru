from __future__ import annotations

from pathlib import Path
from typing import Any

from aip import AipSpeech


BAIDU_ASR_SAMPLE_RATE = 16000
BAIDU_ASR_DEV_PID = 1537


class TranscriptionError(RuntimeError):
    """Raised when Baidu speech recognition fails."""


class Transcriber:
    def __init__(self, app_id: str, api_key: str, secret_key: str) -> None:
        self._client = AipSpeech(app_id, api_key, secret_key)

    def transcribe(self, audio_path: str | Path) -> str:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        audio_data = path.read_bytes()
        response = self._client.asr(
            audio_data,
            "wav",
            BAIDU_ASR_SAMPLE_RATE,
            {"dev_pid": BAIDU_ASR_DEV_PID},
        )

        return _extract_text(response)


def _extract_text(response: Any) -> str:
    if not isinstance(response, dict):
        raise TranscriptionError(f"Unexpected Baidu response: {response!r}")

    err_no = response.get("err_no")
    if err_no not in (0, "0"):
        err_msg = response.get("err_msg", "unknown error")
        raise TranscriptionError(
            f"Baidu speech recognition failed: err_no={err_no}, err_msg={err_msg}"
        )

    result = response.get("result")
    if not isinstance(result, list) or not result:
        raise TranscriptionError("Baidu speech recognition returned no result text.")

    first_result = result[0]
    if not isinstance(first_result, str):
        raise TranscriptionError(f"Unexpected Baidu result text: {first_result!r}")

    return first_result.strip()

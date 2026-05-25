from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from dotenv import dotenv_values


APP_NAME = "VoiceInputAssistant"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"

REQUIRED_API_KEYS = (
    "BAIDU_APP_ID",
    "BAIDU_API_KEY",
    "BAIDU_SECRET_KEY",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_MODEL",
)


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    baidu_app_id: str
    baidu_api_key: str
    baidu_secret_key: str
    deepseek_api_key: str
    deepseek_model: str
    hotkey: str
    audio_output_dir: Path
    auto_paste: bool
    paste_delay_seconds: float


def get_user_config_path() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME / "config.json"

    return Path.home() / "AppData" / "Roaming" / APP_NAME / "config.json"


def load_settings(env_path: str | Path | None = None) -> Settings:
    values = load_config_values(env_path=env_path)
    missing = get_missing_api_keys(values)
    if missing:
        joined = ", ".join(missing)
        raise ConfigError(f"Missing API configuration: {joined}")

    output_dir = Path(_get_str(values, "AUDIO_OUTPUT_DIR", "recordings")).expanduser()
    if not output_dir.is_absolute():
        output_dir = Path.cwd() / output_dir

    return Settings(
        baidu_app_id=_get_required_str(values, "BAIDU_APP_ID"),
        baidu_api_key=_get_required_str(values, "BAIDU_API_KEY"),
        baidu_secret_key=_get_required_str(values, "BAIDU_SECRET_KEY"),
        deepseek_api_key=_get_required_str(values, "DEEPSEEK_API_KEY"),
        deepseek_model=_get_required_str(values, "DEEPSEEK_MODEL"),
        hotkey=_get_str(values, "HOTKEY", "ctrl+alt+space"),
        audio_output_dir=output_dir,
        auto_paste=_get_bool(values, "AUTO_PASTE", True),
        paste_delay_seconds=_get_float(values, "PASTE_DELAY_SECONDS", 0.2),
    )


def load_config_values(env_path: str | Path | None = None) -> dict[str, str]:
    values: dict[str, str] = {
        "DEEPSEEK_MODEL": DEFAULT_DEEPSEEK_MODEL,
        "HOTKEY": "ctrl+alt+space",
        "AUDIO_OUTPUT_DIR": "recordings",
        "AUTO_PASTE": "true",
        "PASTE_DELAY_SECONDS": "0.2",
    }

    values.update(_read_dotenv_values(env_path))
    values.update(_read_environment_values())
    values.update(_read_user_config_values())
    return values


def save_user_config(values: Mapping[str, str]) -> Path:
    config_path = get_user_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_data = {
        "BAIDU_APP_ID": _clean_value(values.get("BAIDU_APP_ID")),
        "BAIDU_API_KEY": _clean_value(values.get("BAIDU_API_KEY")),
        "BAIDU_SECRET_KEY": _clean_value(values.get("BAIDU_SECRET_KEY")),
        "DEEPSEEK_API_KEY": _clean_value(values.get("DEEPSEEK_API_KEY")),
        "DEEPSEEK_MODEL": _clean_value(
            values.get("DEEPSEEK_MODEL"), DEFAULT_DEEPSEEK_MODEL
        ),
    }

    config_path.write_text(
        json.dumps(config_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config_path


def get_missing_api_keys(values: Mapping[str, Any]) -> list[str]:
    return [
        key
        for key in REQUIRED_API_KEYS
        if not _has_real_config_value(key, values.get(key))
    ]


def _read_dotenv_values(env_path: str | Path | None) -> dict[str, str]:
    path = Path(env_path) if env_path is not None else Path.cwd() / ".env"
    if not path.exists():
        return {}

    return {
        key: value.strip()
        for key, value in dotenv_values(path).items()
        if value is not None and value.strip()
    }


def _read_environment_values() -> dict[str, str]:
    keys = (
        *REQUIRED_API_KEYS,
        "HOTKEY",
        "AUDIO_OUTPUT_DIR",
        "AUTO_PASTE",
        "PASTE_DELAY_SECONDS",
    )
    return {
        key: value.strip()
        for key in keys
        if (value := os.getenv(key)) is not None and value.strip()
    }


def _read_user_config_values() -> dict[str, str]:
    config_path = get_user_config_path()
    if not config_path.exists():
        return {}

    try:
        raw_data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid config file: {config_path}") from exc

    if not isinstance(raw_data, dict):
        raise ConfigError(f"Config file must contain a JSON object: {config_path}")

    return {
        str(key): str(value).strip()
        for key, value in raw_data.items()
        if value is not None and str(value).strip()
    }


def _get_required_str(values: Mapping[str, Any], name: str) -> str:
    value = _clean_value(values.get(name))
    if not _has_real_config_value(name, value):
        raise ConfigError(f"{name} must not be empty.")
    return value


def _get_str(values: Mapping[str, Any], name: str, default: str) -> str:
    return _clean_value(values.get(name), default)


def _get_float(values: Mapping[str, Any], name: str, default: float) -> float:
    raw_value = _clean_value(values.get(name), str(default))

    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number.") from exc

    if value < 0:
        raise ConfigError(f"{name} must be 0 or greater.")

    return value


def _get_bool(values: Mapping[str, Any], name: str, default: bool) -> bool:
    raw_value = _clean_value(values.get(name), "true" if default else "false")
    normalized = raw_value.lower()

    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise ConfigError(f"{name} must be true or false.")


def _clean_value(value: Any, default: str = "") -> str:
    if value is None:
        return default
    cleaned = str(value).strip()
    return cleaned if cleaned else default


def _has_real_config_value(name: str, value: Any) -> bool:
    cleaned = _clean_value(value)
    if not cleaned:
        return False
    if name == "DEEPSEEK_MODEL":
        return True

    lowered = cleaned.lower()
    placeholder_fragments = ("your-", "sk-your-", "placeholder", "你的")
    return not any(fragment in lowered for fragment in placeholder_fragments)

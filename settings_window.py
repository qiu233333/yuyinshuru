from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Mapping

from config import DEFAULT_DEEPSEEK_MODEL, get_missing_api_keys, save_user_config


FIELD_DEFINITIONS = (
    ("BAIDU_APP_ID", "百度 App ID", False),
    ("BAIDU_API_KEY", "百度 API Key", True),
    ("BAIDU_SECRET_KEY", "百度 Secret Key", True),
    ("DEEPSEEK_API_KEY", "DeepSeek API Key", True),
    ("DEEPSEEK_MODEL", "DeepSeek Model", False),
)


def show_settings_window(initial_values: Mapping[str, str] | None = None) -> bool:
    values = dict(initial_values or {})
    saved = False

    root = tk.Tk()
    root.title("语音输入助手 - API 配置")
    root.resizable(False, False)

    entries: dict[str, tk.Entry] = {}

    intro = tk.Label(
        root,
        text="首次启动需要填写百度语音识别和 DeepSeek API 配置。",
        anchor="w",
        justify="left",
    )
    intro.grid(row=0, column=0, columnspan=2, padx=18, pady=(16, 8), sticky="w")

    for row, (key, label, is_secret) in enumerate(FIELD_DEFINITIONS, start=1):
        tk.Label(root, text=label).grid(
            row=row, column=0, padx=(18, 10), pady=6, sticky="e"
        )

        entry = tk.Entry(root, width=46, show="*" if is_secret else "")
        entry.grid(row=row, column=1, padx=(0, 18), pady=6, sticky="w")
        entry.insert(0, values.get(key, ""))
        entries[key] = entry

    if not entries["DEEPSEEK_MODEL"].get().strip():
        entries["DEEPSEEK_MODEL"].insert(0, DEFAULT_DEEPSEEK_MODEL)

    def on_save() -> None:
        nonlocal saved

        config_values = {key: entry.get().strip() for key, entry in entries.items()}
        missing = get_missing_api_keys(config_values)
        if missing:
            messagebox.showerror(
                "配置不完整",
                "请填写以下配置：\n" + "\n".join(missing),
                parent=root,
            )
            return

        try:
            config_path = save_user_config(config_values)
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc), parent=root)
            return

        saved = True
        messagebox.showinfo(
            "保存成功",
            f"配置已保存到：\n{config_path}",
            parent=root,
        )
        root.destroy()

    def on_cancel() -> None:
        root.destroy()

    button_frame = tk.Frame(root)
    button_frame.grid(row=len(FIELD_DEFINITIONS) + 1, column=0, columnspan=2, pady=16)

    tk.Button(button_frame, text="保存", width=12, command=on_save).pack(
        side="left", padx=6
    )
    tk.Button(button_frame, text="取消", width=12, command=on_cancel).pack(
        side="left", padx=6
    )

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.bind("<Return>", lambda _event: on_save())
    _center_window(root)
    root.mainloop()

    return saved


def _center_window(root: tk.Tk) -> None:
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 3
    root.geometry(f"{width}x{height}+{x}+{y}")

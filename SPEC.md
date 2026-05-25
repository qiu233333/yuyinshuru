# 语音输入助手 MVP

目标：做一个 Windows 桌面语音输入助手。

核心功能：
1. 按 Ctrl+Alt+Space 开始录音。
2. 再按 Ctrl+Alt+Space 停止录音。
3. 把录音保存为 wav。
4. 调用 OpenAI Speech-to-Text API 转文字。
5. 把识别结果复制到剪贴板。
6. 自动粘贴到当前光标位置。
7. 支持中文普通话。
8. API Key 从 .env 读取，不能写死在代码里。

技术栈：
- Python 3.11+
- openai
- sounddevice
- scipy 或 soundfile
- pyperclip
- keyboard
- python-dotenv

项目结构：
- main.py
- recorder.py
- transcriber.py
- input_writer.py
- config.py
- requirements.txt
- README.md

不要做复杂 UI，先做命令行 MVP。
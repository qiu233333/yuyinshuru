# 语音输入助手 MVP

一个 Windows 命令行版语音输入助手：按 `Ctrl+Alt+Space` 开始录音，再按一次停止录音，程序会保存 16000 Hz、16bit、单声道 WAV，调用百度短语音识别转文字，再用 DeepSeek 自动整理中文标点、断句和明显错别字，最后复制并粘贴到当前输入框。

## 功能

- 全局热键 `Ctrl+Alt+Space` 开始/停止录音
- 录音保存为 `recordings/*.wav`
- 百度语音识别 SDK `baidu-aip`
- 百度普通话输入法模型 `dev_pid=1537`
- DeepSeek OpenAI 兼容接口润色文本
- DeepSeek 失败或 5 秒超时时自动回退百度原始识别文本
- 首次启动时自动弹出 API 配置窗口
- 自动复制识别结果到剪贴板
- 默认自动发送 `Ctrl+V` 粘贴到当前窗口

## 申请百度语音识别 API

1. 打开 [百度智能云语音技术](https://ai.baidu.com/ai-doc/index/SPEECH)。
2. 登录百度账号，进入控制台并完成必要的实名认证。
3. 在语音技术相关页面创建应用，开通“短语音识别标准版 API”。
4. 创建完成后，在应用详情里找到 `AppID`、`API Key`、`Secret Key`。
5. 本项目使用短语音识别，适合 60 秒以内的语音输入。

百度短语音识别要求音频为 16bit 位深单声道，采样率支持 16000 或 8000；本项目固定保存为 16000 Hz WAV。

## 申请 DeepSeek API

1. 打开 [DeepSeek Platform](https://platform.deepseek.com/)。
2. 登录后创建 API Key。
3. 本项目使用 OpenAI SDK 兼容模式，请求地址固定为 `https://api.deepseek.com`。
4. 默认模型为 `deepseek-v4-flash`，可在设置窗口或 `.env` 中修改 `DEEPSEEK_MODEL`。

## 普通用户首次配置

如果你使用打包后的 exe，第一次打开时如果没有检测到 API 配置，会自动弹出“语音输入助手 - API 配置”窗口。

需要填写：

- `BAIDU_APP_ID`
- `BAIDU_API_KEY`
- `BAIDU_SECRET_KEY`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL`，默认 `deepseek-v4-flash`

点击“保存”后，配置会保存到当前 Windows 用户目录：

```text
%APPDATA%\VoiceInputAssistant\config.json
```

以后再次打开程序会优先读取这个 `config.json`，不会要求重复填写。

## Windows 安装

请先安装 Python 3.11 或更高版本，并确认勾选了 “Add python.exe to PATH”。

先检查 Python 是否可用：

```powershell
python --version
```

如果提示找不到 `python`，或者 `py --version` 提示 `No installed Python found!`，说明系统还没有安装可用的 Python。请先从 [Python Windows 下载页](https://www.python.org/downloads/windows/) 安装 Python 3.11+，安装第一页一定勾选 “Add python.exe to PATH”。安装完成后关闭并重新打开 PowerShell。

然后创建并激活虚拟环境：

```powershell
cd F:\project\yuyinshuru
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果 PowerShell 阻止激活虚拟环境，可以先运行：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

如果激活时报“无法将 `.\.venv\Scripts\Activate.ps1` 识别为 cmdlet”，通常是 `.venv` 没有成功创建。运行下面命令检查：

```powershell
Test-Path .\.venv\Scripts\Activate.ps1
```

如果返回 `False`，重新确认 `python --version` 正常，然后再运行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 开发者配置

开发运行时也支持 `.env`。如果同时存在 `%APPDATA%\VoiceInputAssistant\config.json` 和项目里的 `.env`，程序会优先读取 `config.json`。

复制示例环境文件：

```powershell
copy .env.example .env
notepad .env
```

填写百度和 DeepSeek 配置：

```dotenv
BAIDU_APP_ID=your-baidu-app-id
BAIDU_API_KEY=your-baidu-api-key
BAIDU_SECRET_KEY=your-baidu-secret-key

DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-v4-flash
```

可选项：

```dotenv
HOTKEY=ctrl+alt+space
AUDIO_OUTPUT_DIR=recordings
AUTO_PASTE=true
PASTE_DELAY_SECONDS=0.2
```

不要把真实 API Key 写进 `.env.example` 或提交到 git。`.env` 已经在 `.gitignore` 中。

## 运行

```powershell
python main.py
```

运行后：

1. 将光标放到你想输入文字的位置。
2. 按 `Ctrl+Alt+Space` 开始录音。
3. 再按 `Ctrl+Alt+Space` 停止录音。
4. 程序保存 WAV 后调用百度识别。
5. 程序调用 DeepSeek 加标点和断句；失败则使用百度原始文本。
6. 最终文本会复制到剪贴板并自动粘贴。
7. 在终端按 `Ctrl+C` 退出程序。

## 注意事项

- 需要可用的麦克风设备。
- 百度短语音识别适合短音频，请尽量控制在 60 秒以内。
- 如果目标程序以管理员权限运行，而本程序不是管理员权限，自动粘贴可能失败；这种情况下请用同样权限启动终端。
- `keyboard` 是全局热键库，部分安全软件可能会提示拦截。
- 录音文件保存在 `recordings` 目录，该目录已加入 `.gitignore`。

## 项目结构

```text
main.py           # 热键监听和整体流程
recorder.py       # 麦克风录音并保存 16k/16bit/mono WAV
transcriber.py    # 百度短语音识别
text_polisher.py  # DeepSeek 标点和断句整理
input_writer.py   # 剪贴板和自动粘贴
config.py         # config.json / .env 配置读取和校验
settings_window.py # 首次启动 API 配置窗口
requirements.txt
.env.example
.gitignore
```

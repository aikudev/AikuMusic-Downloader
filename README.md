<div align="center">

# 🎵 AikuMusic Downloader

### A clean, lightweight Telegram audio bot

Search YouTube • Convert supported audio to MP3 • Send results straight to chat

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-89F336?style=for-the-badge)](LICENSE)

[**Join AikuCheats on Telegram →**](https://t.me/aikucheats)

</div>

---

## ✨ Features

| Feature | Details |
|:--|:--|
| 🔎 YouTube search | Search a track and choose from up to five results |
| 🎧 MP3 output | YouTube audio is converted to MP3 at 192 kbps |
| 🔗 Direct links | Accepts supported YouTube and Spotify URLs |
| 🧹 Temporary files | Download files are removed after delivery |
| ⚡ Async bot | Download work runs outside the Telegram event loop |
| 🛡️ Safer configuration | Bot token is read from `.env`, not source code |
| 📬 Private delivery | Sends audio only to the requesting chat; no archive/channel copy |
| 👥 Community | Includes a one-tap AikuCheats Telegram button |

> **Important:** Spotify links are processed by spotDL, which generally matches Spotify metadata to audio from other sources. Results and availability can vary. This project does not bypass DRM or guarantee that every Spotify link can be processed.

## 📋 Requirements

- Python **3.10 or newer**
- FFmpeg installed and available in your terminal (`ffmpeg -version`)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Internet access

## 🚀 Installation

### 1. Get the source

Clone the repository after uploading this folder to GitHub:

```bash
git clone https://github.com/aikudev/AikuMusic-Downloader.git
cd AikuMusic-Downloader
```

Or download the repository ZIP from GitHub and extract it.

### 2. Install FFmpeg

**Termux (Android):**

```bash
pkg update
pkg install python ffmpeg git
```

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg git
```

**Windows:**

Install Python from [python.org](https://www.python.org/downloads/) and FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html). Ensure both are available on `PATH`.

Check FFmpeg:

```bash
ffmpeg -version
```

### 3. Create a virtual environment (recommended)

**Linux / macOS / Termux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install Python packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If spotDL installation fails on your platform, check its current installation documentation before pinning or downgrading dependencies.

### 5. Create your Telegram bot token

1. Open [@BotFather](https://t.me/BotFather) in Telegram.
2. Create a bot using `/newbot`, or use an existing bot.
3. Copy the token BotFather provides.
4. Make a local environment file:

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder:

```dotenv
TELEGRAM_BOT_TOKEN=your_new_token_here
```

**Never upload `.env` or paste your real token into public issues, screenshots, or source files.** If a token has been exposed, revoke it with BotFather and generate a new one.

### 6. Run the bot

```bash
python main.py
```

You should see a log message indicating that AikuMusic Downloader is running. Open your bot in Telegram and send `/start`.

## 🤖 Commands

| Command | Purpose |
|:--|:--|
| `/start` | Show the welcome menu and AikuCheats button |
| `/help` | Show help |
| `/search song name` | Search YouTube and choose a result |
| `/ssearch SPOTIFY_URL` | Process a Spotify track, album, or playlist URL |
| Send a YouTube URL | Download audio as MP3 |
| Send a Spotify URL | Process the Spotify link with spotDL |

Example:

```text
/search The Weeknd Blinding Lights
```

Tap one of the result buttons to start processing.

## 📁 Project structure

```text
AikuMusic-Downloader/
├── main.py           # Bot handlers and download logic
├── requirements.txt  # Python dependencies
├── .env.example      # Safe token template
├── .gitignore        # Keeps secrets and local files out of Git
├── LICENSE           # MIT license
└── README.md         # Project documentation
```

## 🧰 Troubleshooting

**`Missing TELEGRAM_BOT_TOKEN`**

- Make sure `.env` exists in the project directory.
- Check that the variable is spelled `TELEGRAM_BOT_TOKEN`.
- Ensure the token is on one line and has no surrounding quotes unless needed.

**`ffmpeg not found`**

- Install FFmpeg for your OS.
- Run `ffmpeg -version` and confirm it works in the same terminal used to launch Python.

**`spotdl` command failed**

- Spotify link processing depends on spotDL and the source services it uses.
- Upgrade packages with `pip install --upgrade spotdl yt-dlp`.
- Try a single-track Spotify URL first; albums and playlists may take longer.
- Read the latest spotDL documentation if its command-line options have changed.

**YouTube extraction fails**

- Upgrade yt-dlp: `python -m pip install -U yt-dlp`
- Some videos may be private, age-restricted, region-restricted, or unavailable.

**Telegram rejects a file**

- Telegram upload limits can vary by account, API method, and platform. Try a shorter track or check the current Telegram Bot API limits.

## 🔐 Security notes

- Keep your real `.env` file private.
- Do not commit bot tokens, session files, or personal data.
- Rotate any token that has been exposed.
- This bot does not forward audio to a private channel and does not require a channel ID.

## ⚖️ Responsible use

Use this project only for audio you own, have permission to download, or that is otherwise legally available for downloading. Respect copyright, platform terms, and local law. You are responsible for how you use the software.

## 💚 Community

Questions, updates, and AikuCheats community:

<div align="center">

[![Join Telegram](https://img.shields.io/badge/Join%20AikuCheats-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/aikucheats)

**Made by AikuCheats**

</div>

---

<div align="center">
<sub>MIT licensed • Contributions and bug reports are welcome</sub>
</div>

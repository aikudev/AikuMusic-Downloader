#!/usr/bin/env python3
"""AikuMusic Downloader — Telegram music search and download bot.

Use only for content you own, have permission to download, or that is otherwise
legally available for downloading in your jurisdiction.
"""
import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
MAX_RESULTS = 5
MAX_CONCURRENT_DOWNLOADS = 2
DOWNLOAD_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("aikumusic")


def is_supported_url(text: str) -> bool:
    try:
        host = (urlparse(text.strip()).hostname or "").lower()
    except ValueError:
        return False
    return (
        host == "youtu.be"
        or host.endswith("youtube.com")
        or host == "spotify.com"
        or host.endswith(".spotify.com")
    )


def download_youtube(url: str, output_dir: str) -> str:
    """Download the best available audio and convert it to MP3 with FFmpeg."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(title).80s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        expected = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
    if os.path.isfile(expected):
        return expected
    found = list(Path(output_dir).glob("*.mp3"))
    if found:
        return str(found[0])
    raise RuntimeError("yt-dlp did not produce an MP3 file.")


def _run_spotdl(url_or_query: str, output_dir: str) -> str:
    """Download Spotify-linked audio through spotDL (requires FFmpeg)."""
    import subprocess
    template = os.path.join(output_dir, "{artist} - {title}.{output-ext}")
    cmd = [
        "spotdl", "download", url_or_query,
        "--output", template,
        "--format", "mp3",
        "--bitrate", "192k",
        "--no-cache",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode:
        detail = (result.stderr or result.stdout or "Unknown spotDL error").strip()
        raise RuntimeError(f"spotDL failed: {detail[:350]}")
    files = sorted(Path(output_dir).glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        # Some spotDL versions append an output extension differently.
        files = sorted(Path(output_dir).glob("**/*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise RuntimeError("spotDL completed but no MP3 was found.")
    return str(files[0])


def download_spotify(url: str, output_dir: str) -> str:
    return _run_spotdl(url, output_dir)


def search_youtube(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    opts = {"quiet": True, "no_warnings": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
    items = []
    for entry in (data or {}).get("entries") or []:
        if not entry:
            continue
        video_id = entry.get("id")
        if not video_id:
            continue
        items.append({
            "source": "youtube",
            "id": video_id,
            "title": (entry.get("title") or "Untitled")[:90],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "duration": entry.get("duration"),
        })
    return items


def search_spotify(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """Search Spotify using spotDL's supported search flow where possible."""
    # Spotify's search interfaces can change; spotDL's public search syntax
    # supports track names as well as Spotify URLs.
    # Return a query item so the user can still download by title.
    return [{
        "source": "spotify",
        "url": query,
        "title": query[:90],
        "artist": "",
        "duration": None,
    }]


def fmt_duration(seconds) -> str:
    if seconds is None:
        return ""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return ""
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def results_keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for index, item in enumerate(items):
        label = f"{index + 1}. {item['title'][:48]}"
        duration = fmt_duration(item.get("duration"))
        if duration:
            label += f" [{duration}]"
        rows.append([InlineKeyboardButton(label[:64], callback_data=f"dl:{index}")])
    return InlineKeyboardMarkup(rows)


async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str):
    title = Path(file_path).stem[:64]
    with open(file_path, "rb") as audio:
        await update.effective_chat.send_audio(audio=audio, title=title)


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return
    url = message.text.strip()
    if not is_supported_url(url):
        await message.reply_text(
            "Send a YouTube/YouTube Music or Spotify link, or use /search to find a YouTube track."
        )
        return

    workdir = tempfile.mkdtemp(prefix="aikumusic_")
    status = await message.reply_text("⏳ Preparing your audio…")
    try:
        async with DOWNLOAD_SEMAPHORE:
            if "spotify.com" in (urlparse(url).hostname or "").lower():
                path = await asyncio.to_thread(download_spotify, url, workdir)
            else:
                path = await asyncio.to_thread(download_youtube, url, workdir)
            await send_audio(update, context, path)
        await status.delete()
    except Exception as exc:
        log.exception("Direct-link download failed")
        await status.edit_text(f"❌ Could not download that link: {str(exc)[:700]}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        await update.effective_message.reply_text("Usage: /search song name")
        return
    status = await update.effective_message.reply_text(f"🔎 Searching YouTube for: {query[:150]}")
    try:
        items = await asyncio.to_thread(search_youtube, query, MAX_RESULTS)
        if not items:
            await status.edit_text("No results found. Try a different search.")
            return
        context.user_data["search_items"] = items
        await status.edit_text("Choose a result:", reply_markup=results_keyboard(items))
    except Exception as exc:
        log.exception("YouTube search failed")
        await status.edit_text(f"❌ Search failed: {str(exc)[:500]}")


async def ssearch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).strip()
    if not query:
        await update.effective_message.reply_text(
            "Usage: /ssearch Spotify track/album/playlist URL\n"
            "For title-based searches, use /search (YouTube results)."
        )
        return
    if not is_supported_url(query) or "spotify.com" not in (urlparse(query).hostname or "").lower():
        await update.effective_message.reply_text("Please provide a valid Spotify URL.")
        return
    workdir = tempfile.mkdtemp(prefix="aikumusic_")
    status = await update.effective_message.reply_text("⏳ Processing Spotify link…")
    try:
        async with DOWNLOAD_SEMAPHORE:
            path = await asyncio.to_thread(download_spotify, query, workdir)
            await send_audio(update, context, path)
        await status.delete()
    except Exception as exc:
        log.exception("Spotify download failed")
        await status.edit_text(f"❌ Spotify processing failed: {str(exc)[:700]}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


async def result_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        index = int((query.data or "").split(":", 1)[1])
    except (IndexError, ValueError):
        return
    items = context.user_data.get("search_items", [])
    if index < 0 or index >= len(items):
        await query.edit_message_text("That result expired. Run /search again.")
        return

    item = items[index]
    status = await query.edit_message_text(f"⏳ Downloading: {item['title'][:70]}")
    workdir = tempfile.mkdtemp(prefix="aikumusic_")
    try:
        async with DOWNLOAD_SEMAPHORE:
            path = await asyncio.to_thread(download_youtube, item["url"], workdir)
            with open(path, "rb") as audio:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=audio,
                    title=Path(path).stem[:64],
                )
        await status.delete()
    except Exception as exc:
        log.exception("Selected download failed")
        await status.edit_text(f"❌ Download failed: {str(exc)[:700]}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("Join AikuCheats Telegram", url="https://t.me/aikucheats")
    ]])
    await update.effective_message.reply_text(
        "🎵 AikuMusic Downloader\n\n"
        "Download audio from supported YouTube links or process Spotify links "
        "through spotDL. Search YouTube tracks with /search.\n\n"
        "Commands:\n"
        "/start — Show this menu\n"
        "/help — Show this menu\n"
        "/search song name — Search YouTube\n"
        "/ssearch Spotify_URL — Process a Spotify link\n\n"
        "Use only for content you own, have permission to download, or that is "
        "otherwise legally available. Availability depends on the source and its terms.",
        reply_markup=keyboard,
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.error("Unhandled Telegram error", exc_info=context.error)


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "Missing TELEGRAM_BOT_TOKEN. Copy .env.example to .env and add your bot token."
        )
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("ssearch", ssearch_cmd))
    app.add_handler(CallbackQueryHandler(result_callback, pattern=r"^dl:\d+$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_error_handler(error_handler)
    log.info("AikuMusic Downloader is running.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

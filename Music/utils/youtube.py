"""
HellMusic V3 - YouTube Handler
Modern YouTube integration with API support and cookie fix
"""

import asyncio
import os
import re
import time
from typing import Union, Optional

import aiohttp
import requests
import yt_dlp
from lyricsgenius import Genius
from pyrogram.types import CallbackQuery
from py_yt import VideosSearch

from config import Config
from Music.core.clients import hellbot
from Music.core.logger import LOGS
from Music.helpers.strings import TEXTS


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR_API_URL = None
FALLBACK_API_URL = "https://shrutibots.site"


async def load_api_url():
    """Load API URL from remote source"""
    global YOUR_API_URL
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://pastebin.com/raw/rLsBhAQa",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    YOUR_API_URL = content.strip()
                    LOGS.info("✅ YouTube API URL loaded successfully")
                else:
                    YOUR_API_URL = FALLBACK_API_URL
                    LOGS.info("⚠️ Using fallback YouTube API URL")
    except Exception as e:
        YOUR_API_URL = FALLBACK_API_URL
        LOGS.warning(f"⚠️ API load failed, using fallback: {e}")


# Initialize API URL
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(load_api_url())
    else:
        loop.run_until_complete(load_api_url())
except RuntimeError:
    pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Download Functions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def download_song(link: str) -> Optional[str]:
    """
    Download audio from YouTube using API
    
    Args:
        link: YouTube URL or video ID
    
    Returns:
        str: Downloaded file path or None
    """
    global YOUR_API_URL
    
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            YOUR_API_URL = FALLBACK_API_URL
    
    # Extract video ID
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    
    if not video_id or len(video_id) < 3:
        return None
    
    # Setup download directory
    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    
    # Return if already downloaded
    if os.path.exists(file_path):
        LOGS.info(f"📁 File already exists: {video_id}.mp3")
        return file_path
    
    try:
        async with aiohttp.ClientSession() as session:
            # Request download token
            params = {"url": video_id, "type": "audio"}
            
            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    LOGS.error(f"❌ Download request failed: {response.status}")
                    return None
                
                data = await response.json()
                download_token = data.get("download_token")
                
                if not download_token:
                    LOGS.error("❌ No download token received")
                    return None
                
                # Stream and save file
                stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=audio"
                
                async with session.get(
                    stream_url,
                    headers={"X-Download-Token": download_token},
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as file_response:
                    if file_response.status != 200:
                        LOGS.error(f"❌ Stream request failed: {file_response.status}")
                        return None
                    
                    with open(file_path, "wb") as f:
                        async for chunk in file_response.content.iter_chunked(16384):
                            f.write(chunk)
                    
                    LOGS.info(f"✅ Downloaded audio: {video_id}.mp3")
                    return file_path
    
    except Exception as e:
        LOGS.error(f"❌ Download error: {e}")
        return None


async def download_video(link: str) -> Optional[str]:
    """
    Download video from YouTube using API
    
    Args:
        link: YouTube URL or video ID
    
    Returns:
        str: Downloaded file path or None
    """
    global YOUR_API_URL
    
    if not YOUR_API_URL:
        await load_api_url()
        if not YOUR_API_URL:
            YOUR_API_URL = FALLBACK_API_URL
    
    # Extract video ID
    video_id = link.split('v=')[-1].split('&')[0] if 'v=' in link else link
    
    if not video_id or len(video_id) < 3:
        return None
    
    # Setup download directory
    DOWNLOAD_DIR = "downloads"
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    
    # Return if already downloaded
    if os.path.exists(file_path):
        LOGS.info(f"📁 File already exists: {video_id}.mp4")
        return file_path
    
    try:
        async with aiohttp.ClientSession() as session:
            # Request download token
            params = {"url": video_id, "type": "video"}
            
            async with session.get(
                f"{YOUR_API_URL}/download",
                params=params,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    LOGS.error(f"❌ Download request failed: {response.status}")
                    return None
                
                data = await response.json()
                download_token = data.get("download_token")
                
                if not download_token:
                    LOGS.error("❌ No download token received")
                    return None
                
                # Stream and save file
                stream_url = f"{YOUR_API_URL}/stream/{video_id}?type=video"
                
                async with session.get(
                    stream_url,
                    headers={"X-Download-Token": download_token},
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as file_response:
                    if file_response.status != 200:
                        LOGS.error(f"❌ Stream request failed: {file_response.status}")
                        return None
                    
                    with open(file_path, "wb") as f:
                        async for chunk in file_response.content.iter_chunked(16384):
                            f.write(chunk)
                    
                    LOGS.info(f"✅ Downloaded video: {video_id}.mp4")
                    return file_path
    
    except Exception as e:
        LOGS.error(f"❌ Download error: {e}")
        return None


async def shell_cmd(cmd: str) -> str:
    """Execute shell command asynchronously"""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    out, errorz = await proc.communicate()
    
    if errorz:
        error_text = errorz.decode("utf-8").lower()
        if "unavailable videos are hidden" in error_text:
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    
    return out.decode("utf-8")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Main YouTube Class
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class YouTube:
    """Advanced YouTube handler for HellMusic V3"""
    
    def __init__(self):
        # Base URLs
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        
        # Regex patterns
        self.regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/|youtube\.com\/playlist\?list=)"
        
        # YT-DLP Options (fallback)
        self.audio_opts = {
            "format": "bestaudio[ext=m4a]",
            "quiet": True,
            "no_warnings": True,
        }
        
        self.video_opts = {
            "format": "best[height<=720]",
            "addmetadata": True,
            "key": "FFmpegMetadata",
            "prefer_ffmpeg": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
            ],
            "outtmpl": "downloads/%(id)s.mp4",
            "quiet": True,
            "no_warnings": True,
        }
        
        self.yt_opts_audio = {
            "format": "bestaudio/best",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
        }
        
        self.yt_opts_video = {
            "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
        }
        
        self.yt_playlist_opts = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
        }
        
        # Lyrics API
        self.lyrics = Config.LYRICS_API if hasattr(Config, 'LYRICS_API') else None
        
        try:
            if self.lyrics:
                self.client = Genius(self.lyrics, remove_section_headers=True)
                LOGS.info("✅ Lyrics API initialized")
            else:
                self.client = None
                LOGS.warning("⚠️ Lyrics API not configured")
        except Exception as e:
            LOGS.warning(f"⚠️ Lyrics API initialization failed: {e}")
            self.client = None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # URL Validation
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def check(self, link: str) -> bool:
        """Check if link is a valid YouTube URL"""
        return bool(re.match(self.regex, link))

    async def format_link(self, link: str, video_id: bool) -> str:
        """
        Format YouTube link
        
        Args:
            link: YouTube URL or video ID
            video_id: If True, link is video ID
        
        Returns:
            str: Formatted YouTube URL
        """
        link = link.strip()
        
        if video_id:
            link = self.base + link
        
        if "&" in link:
            link = link.split("&")[0]
        
        return link

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Video Information
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def get_data(
        self, 
        link: str, 
        video_id: bool, 
        limit: int = 1
    ) -> list:
        """
        Get video data from YouTube
        
        Args:
            link: YouTube URL or video ID
            video_id: If True, link is video ID
            limit: Number of results
        
        Returns:
            list: Video data
        """
        yt_url = await self.format_link(link, video_id)
        collection = []
        
        try:
            results = VideosSearch(yt_url, limit=limit)
            
            for result in (await results.next())["result"]:
                vid = result["id"]
                channel = result["channel"]["name"]
                channel_url = result["channel"]["link"]
                duration = result["duration"]
                published = result.get("publishedTime", "Unknown")
                thumbnail = f"https://i.ytimg.com/vi/{result['id']}/hqdefault.jpg"
                title = result["title"]
                url = result["link"]
                views = result["viewCount"]["short"]
                
                context = {
                    "id": vid,
                    "ch_link": channel_url,
                    "channel": channel,
                    "duration": duration,
                    "link": url,
                    "published": published,
                    "thumbnail": thumbnail,
                    "title": title,
                    "views": views,
                }
                
                collection.append(context)
        
        except Exception as e:
            LOGS.error(f"❌ Error getting video data: {e}")
        
        return collection[:limit]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Playlist Handling
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def get_playlist(self, link: str, limit: int = 25) -> list:
        """
        Get playlist video IDs
        
        Args:
            link: Playlist URL
            limit: Max videos to fetch
        
        Returns:
            list: Video IDs
        """
        yt_url = await self.format_link(link, False)
        
        try:
            # Using shell command for better playlist extraction
            cmd = f"yt-dlp -i --get-id --flat-playlist --playlist-end {limit} --skip-download {yt_url}"
            result = await shell_cmd(cmd)
            
            playlist = [vid.strip() for vid in result.split("\n") if vid.strip()]
            
            LOGS.info(f"✅ Extracted {len(playlist)} videos from playlist")
            return playlist
        
        except Exception as e:
            LOGS.error(f"❌ Playlist extraction error: {e}")
            
            # Fallback to yt-dlp library
            try:
                with yt_dlp.YoutubeDL(self.yt_playlist_opts) as ydl:
                    results = ydl.extract_info(yt_url, download=False)
                    playlist = [video['id'] for video in results.get('entries', [])]
                    return playlist[:limit]
            except Exception as e2:
                LOGS.error(f"❌ Playlist fallback error: {e2}")
                return []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Download Functions
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def download(
        self, 
        link: str, 
        video_id: bool, 
        video: bool = False
    ) -> Optional[str]:
        """
        Download audio/video from YouTube
        
        Args:
            link: YouTube URL or video ID
            video_id: If True, link is video ID
            video: If True, download video; else audio
        
        Returns:
            str: Downloaded file path
        """
        yt_url = await self.format_link(link, video_id)
        
        try:
            # Use API for downloading
            if video:
                file_path = await download_video(yt_url)
            else:
                file_path = await download_song(yt_url)
            
            if file_path:
                LOGS.info(f"✅ Downloaded: {file_path}")
                return file_path
            
            # Fallback to yt-dlp if API fails
            LOGS.warning("⚠️ API download failed, trying yt-dlp...")
            return await self._download_fallback(yt_url, video)
        
        except Exception as e:
            LOGS.error(f"❌ Download error: {e}")
            return await self._download_fallback(yt_url, video)

    async def _download_fallback(self, yt_url: str, video: bool = False) -> Optional[str]:
        """Fallback download using yt-dlp"""
        try:
            if video:
                dlp = yt_dlp.YoutubeDL(self.yt_opts_video)
            else:
                dlp = yt_dlp.YoutubeDL(self.yt_opts_audio)
            
            info = dlp.extract_info(yt_url, download=False)
            path = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            
            if not os.path.exists(path):
                dlp.download([yt_url])
            
            LOGS.info(f"✅ Fallback download successful: {path}")
            return path
        
        except Exception as e:
            LOGS.error(f"❌ Fallback download failed: {e}")
            return None

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Send Song/Video
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def send_song(
        self,
        message: CallbackQuery,
        rand_key: str,
        key: int,
        video: bool = False
    ) -> dict:
        """
        Download and send song/video to user
        
        Args:
            message: Callback query message
            rand_key: Random cache key
            key: Track index
            video: If True, send video; else audio
        """
        track = Config.SONG_CACHE[rand_key][key]
        
        # Notify user
        hell = await message.message.reply_text(
            "**📥 Downloading...**\n\n"
            f"**📝 Title:** `{track['title'][:50]}...`"
        )
        
        try:
            await message.message.delete()
        except Exception:
            pass
        
        try:
            # Download thumbnail
            thumb = f"downloads/{track['id']}_{time.time()}.jpg"
            os.makedirs("downloads", exist_ok=True)
            
            _thumb = requests.get(track["thumbnail"], allow_redirects=True)
            open(thumb, "wb").write(_thumb.content)
            
            # Download media
            output = None
            
            if video:
                # Download video
                output = await download_video(track["link"])
                
                if not output:
                    # Fallback to yt-dlp
                    with yt_dlp.YoutubeDL(self.video_opts) as ydl:
                        yt_file = ydl.extract_info(track["link"], download=True)
                        output = f"downloads/{yt_file['id']}.mp4"
                
                # Send video
                if output and os.path.exists(output):
                    await message.message.reply_video(
                        video=output,
                        caption=TEXTS.SONG_CAPTION.format(
                            track["title"],
                            track["link"],
                            track["views"],
                            track["duration"],
                            message.from_user.mention,
                            hellbot.app.mention,
                        ),
                        thumb=thumb,
                        supports_streaming=True,
                    )
            else:
                # Download audio
                output = await download_song(track["link"])
                
                if not output:
                    # Fallback to yt-dlp
                    with yt_dlp.YoutubeDL(self.audio_opts) as ydl:
                        yt_file = ydl.extract_info(track["link"], download=True)
                        output = ydl.prepare_filename(yt_file)
                        ydl.process_info(yt_file)
                
                # Get duration
                try:
                    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                        info = ydl.extract_info(track["link"], download=False)
                        duration = int(info.get("duration", 0))
                except Exception:
                    duration = 0
                
                # Send audio
                if output and os.path.exists(output):
                    await message.message.reply_audio(
                        audio=output,
                        caption=TEXTS.SONG_CAPTION.format(
                            track["title"],
                            track["link"],
                            track["views"],
                            track["duration"],
                            message.from_user.mention,
                            hellbot.app.mention,
                        ),
                        duration=duration,
                        performer=TEXTS.PERFORMER,
                    

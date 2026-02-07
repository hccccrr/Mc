"""
HellMusic V3 - Formatters & Utilities
Modern formatting and utility functions
"""

import datetime
import random
import re
import string
import time
from typing import Union

import aiohttp
import psutil
import pytz
from html_telegraph_poster import TelegraphPoster

from config import Config
from Music.version import __start_time__


class Formatters:
    """Advanced formatting utilities for HellMusic V3"""
    
    def __init__(self) -> None:
        self.time_zone = pytz.timezone(Config.TZ) if hasattr(Config, 'TZ') else pytz.UTC

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Validation & Checking
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def check_limit(self, check: int, config: int) -> bool:
        """
        Check if value is within limit
        
        Args:
            check: Value to check
            config: Limit value (0 means unlimited)
        
        Returns:
            bool: True if within limit
        """
        if config == 0:
            return True
        return check <= config

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Time Formatting
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def mins_to_secs(self, time_str: str) -> int:
        """
        Convert MM:SS or HH:MM:SS to seconds
        
        Args:
            time_str: Time string (e.g., "4:30" or "1:30:45")
        
        Returns:
            int: Total seconds
        """
        try:
            parts = list(map(int, time_str.split(":")))
            return sum(x * 60**i for i, x in enumerate(reversed(parts)))
        except Exception:
            return 0

    def secs_to_mins(self, seconds: int) -> str:
        """
        Convert seconds to MM:SS or HH:MM:SS format
        
        Args:
            seconds: Total seconds
        
        Returns:
            str: Formatted time string
        """
        time_str = str(datetime.timedelta(seconds=seconds))
        
        # Remove leading zeros for hours
        if time_str.startswith("0:"):
            time_str = time_str[2:]
        
        return time_str

    def get_readable_time(self, seconds: int) -> str:
        """
        Convert seconds to human-readable format
        
        Args:
            seconds: Total seconds
        
        Returns:
            str: Readable time (e.g., "2h:30m:15s")
        """
        count = 0
        time_parts = []
        time_suffixes = ["s", "m", "h", "d"]
        
        while count < 4:
            count += 1
            
            if count < 3:
                remainder, result = divmod(seconds, 60)
            else:
                remainder, result = divmod(seconds, 24)
            
            if seconds == 0 and remainder == 0:
                break
            
            time_parts.append(int(result))
            seconds = int(remainder)
        
        # Format time parts
        formatted_parts = [
            f"{time_parts[i]}{time_suffixes[i]}" 
            for i in range(len(time_parts))
        ]
        
        # Add days separately if present
        ping_time = ""
        if len(formatted_parts) == 4:
            ping_time += formatted_parts.pop() + ", "
        
        formatted_parts.reverse()
        ping_time += ":".join(formatted_parts)
        
        return ping_time

    def get_current_time(self) -> str:
        """
        Get current time in configured timezone
        
        Returns:
            str: Formatted current time
        """
        now = datetime.datetime.now(self.time_zone)
        return now.strftime("%d-%m-%Y %H:%M:%S")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Size Formatting
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def bytes_to_mb(self, size: int) -> float:
        """
        Convert bytes to megabytes
        
        Args:
            size: Size in bytes
        
        Returns:
            float: Size in MB
        """
        return round(size / (1024 * 1024), 2)

    def format_bytes(self, size: int) -> str:
        """
        Format bytes to human-readable size
        
        Args:
            size: Size in bytes
        
        Returns:
            str: Formatted size (e.g., "1.5 MB")
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # String Utilities
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def gen_key(self, prefix: str = "key", length: int = 5) -> str:
        """
        Generate random key
        
        Args:
            prefix: Key prefix
            length: Random string length
        
        Returns:
            str: Generated key
        """
        random_str = "".join(
            random.choice(string.ascii_letters + string.digits) 
            for _ in range(length)
        )
        return f"{prefix}_{random_str}"

    def truncate_text(self, text: str, max_length: int = 100) -> str:
        """
        Truncate text with ellipsis
        
        Args:
            text: Text to truncate
            max_length: Maximum length
        
        Returns:
            str: Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # List Utilities
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def group_the_list(
        self, 
        collection: list, 
        group: int = 5, 
        length: bool = False
    ) -> tuple:
        """
        Group list into chunks
        
        Args:
            collection: List to group
            group: Items per group
            length: Return length instead of groups
        
        Returns:
            tuple: (grouped_list, total_items)
        """
        grouped = [
            collection[i:i + group] 
            for i in range(0, len(collection), group)
        ]
        
        total = sum(len(g) for g in grouped)
        
        if length:
            return len(grouped), total
        
        return grouped, total

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # System Statistics
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def system_stats(self) -> dict:
        """
        Get system statistics
        
        Returns:
            dict: System stats
        """
        bot_uptime = int(time.time() - __start_time__)
        
        stats = {
            "cpu": f"{psutil.cpu_percent(interval=0.5):.1f}%",
            "core": psutil.cpu_count(logical=True),
            "disk": f"{psutil.disk_usage('/').percent:.1f}%",
            "ram": f"{psutil.virtual_memory().percent:.1f}%",
            "uptime": self.get_readable_time(bot_uptime),
        }
        
        return stats

    async def get_ram_usage(self) -> dict:
        """
        Get detailed RAM usage
        
        Returns:
            dict: RAM usage details
        """
        ram = psutil.virtual_memory()
        
        return {
            "total": self.format_bytes(ram.total),
            "available": self.format_bytes(ram.available),
            "used": self.format_bytes(ram.used),
            "percent": f"{ram.percent}%",
        }

    async def get_cpu_usage(self) -> dict:
        """
        Get detailed CPU usage
        
        Returns:
            dict: CPU usage details
        """
        return {
            "percent": f"{psutil.cpu_percent(interval=1)}%",
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
        }

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Telegraph Integration
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def convert_telegraph_url(self, url: str) -> str:
        """
        Convert telegraph URL to te.legra.ph
        
        Args:
            url: Telegraph URL
        
        Returns:
            str: Converted URL
        """
        try:
            pattern = r"(https?://)(telegra\.ph)"
            converted = re.sub(pattern, r"\1te.legra.ph", url)
            return converted
        except Exception:
            return url

    async def telegraph_paste(
        self,
        title: str,
        text: str,
        author: str = "HellMusic V3",
        author_url: str = "https://t.me/Its_HellBot",
    ) -> str:
        """
        Upload content to Telegraph
        
        Args:
            title: Post title
            text: Post content
            author: Author name
            author_url: Author URL
        
        Returns:
            str: Telegraph URL
        """
        try:
            client = TelegraphPoster(use_api=True)
            client.create_api_token(author)
            
            post = client.post(
                title=title,
                author=author,
                author_url=author_url,
                text=text,
            )
            
            return self.convert_telegraph_url(post["url"])
        except Exception as e:
            raise Exception(f"Telegraph upload failed: {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Paste Services
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    async def post_request(self, url: str, *args, **kwargs) -> Union[dict, str]:
        """
        Make async POST request
        
        Args:
            url: Request URL
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Response data (JSON or text)
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(url, *args, **kwargs) as resp:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
                return data

    async def bb_paste(self, text: str) -> Union[str, None]:
        """
        Upload text to batbin.me
        
        Args:
            text: Text to upload
        
        Returns:
            str: Paste URL or None if failed
        """
        BASE = "https://batbin.me/"
        
        try:
            resp = await self.post_request(f"{BASE}api/v2/paste", data=text)
            
            if not resp.get("success"):
                return None
            
            return BASE + resp["message"]
        except Exception:
            return None

    async def spaceb_paste(self, text: str) -> Union[str, None]:
        """
        Upload text to spaceb.in
        
        Args:
            text: Text to upload
        
        Returns:
            str: Paste URL or None if failed
        """
        BASE = "https://spaceb.in/"
        
        try:
            resp = await self.post_request(
                f"{BASE}api/v1/documents",
                data=text.encode("utf-8")
            )
            
            if "key" in resp:
                return BASE + resp["key"]
            
            return None
        except Exception:
            return None


# Global formatter instance
formatter = Formatters()

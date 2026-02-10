import platform
import time

from telethon import __version__ as telethon_version
from pytgcalls.__version__ import __version__ as pytgcalls_version

# versions dictionary
__version__ = {
    "Hell Music": "3.0.0",
    "Python": platform.python_version(),
    "Telethon": telethon_version,
    "PyTgCalls": pytgcalls_version,
}

# store start time
__start_time__ = time.time()

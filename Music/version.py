"""
HellMusic V3 - Version Information
"""

import sys
import time

import pyrogram
import pytgcalls

# Start time
__start_time__ = time.time()

# Version information
__version__ = {
    "Hell Music": "3.0.0",
    "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    "Pyrogram": pyrogram.__version__,
    "PyTgCalls": pytgcalls.__version__,
}

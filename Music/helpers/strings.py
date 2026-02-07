"""
HellMusic V3 - Text Strings
Modern text templates with enhanced formatting and emojis
"""


class TEXTS:
    """Text templates for HellMusic V3"""
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Song & Video Information
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    ABOUT_SONG = (
        "╭─────────────────────╮\n"
        "│  **🎵 Song Information**\n"
        "╰─────────────────────╯\n\n"
        "**📝 Title:** `{0}`\n"
        "**📺 Channel:** `{1}`\n"
        "**📅 Published:** `{2}`\n"
        "**👁️ Views:** `{3}`\n"
        "**⏱️ Duration:** `{4}`\n\n"
        "**🔗 Powered By:** {5}"
    )
    
    ABOUT_USER = (
        "╭─────────────────────╮\n"
        "│  **👤 Top User Info**\n"
        "╰─────────────────────╯\n\n"
        "**👤 Name:** {0}\n"
        "**🆔 User ID:** `{1}`\n"
        "**⭐ Level:** `{2}`\n"
        "**🎵 Songs Played:** `{3}`\n"
        "**📅 Member Since:** `{4}`\n\n"
        "**🔗 Powered By:** {5}"
    )
    
    SONG_CAPTION = (
        "╭─────────────────────╮\n"
        "│  **🎵 Download Info**\n"
        "╰─────────────────────╯\n\n"
        "**📝 Title:** [{0}]({1})\n"
        "**👁️ Views:** `{2}`\n"
        "**⏱️ Duration:** `{3}`\n"
        "**👤 Requested By:** {4}\n\n"
        "**🔗 Powered By:** {5}"
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Playback Status
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    PLAYING = (
        "╭─────────────────────╮\n"
        "│  **🎵 Now Playing**\n"
        "╰─────────────────────╯\n\n"
        "**🔗 Stream:** {0}\n\n"
        "**📝 Song:** `{1}`\n"
        "**⏱️ Duration:** `{2}`\n"
        "**👤 Requested By:** {3}"
    )
    
    QUEUE = (
        "╭─────────────────────╮\n"
        "│  **📋 Added to Queue**\n"
        "╰─────────────────────╯\n\n"
        "**🔢 Position:** `#{0}`\n"
        "**📝 Song:** `{1}`\n"
        "**⏱️ Duration:** `{2}`\n"
        "**👤 Queued By:** {3}"
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # User Profile
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    PROFILE = (
        "╭─────────────────────╮\n"
        "│  {0}\n"
        "│  **👤 User Profile**\n"
        "╰─────────────────────╯\n\n"
        "**👤 Name:** {1}\n"
        "**🆔 User ID:** `{2}`\n"
        "**📱 Type:** `{3}`\n"
        "**⭐ Level:** `{4}`\n"
        "**🎵 Songs Played:** `{5}`\n"
        "**📅 Member Since:** `{6}`\n\n"
        "**🔗 Powered By:** {7}"
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Statistics
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    STATS = (
        "╭─────────────────────╮\n"
        "│  **📊 Bot Statistics**\n"
        "╰─────────────────────╯\n\n"
        "**📊 Server Stats:**\n"
        "├ **👥 Total Users:** `{0}`\n"
        "├ **💬 Total Chats:** `{1}`\n"
        "├ **🚫 Gbans:** `{2}`\n"
        "├ **🔒 Blocked:** `{3}`\n"
        "├ **🎵 Songs Played:** `{4}`\n"
        "└ **🎙️ Active VC:** `{5}`\n\n"
        "**💻 System Stats:**\n"
        "├ **🖥️ CPU Cores:** `{6}`\n"
        "├ **⚡ CPU Usage:** `{7}`\n"
        "├ **💾 Disk Usage:** `{8}`\n"
        "├ **🎯 RAM Usage:** `{9}`\n"
        "└ **⏰ Uptime:** `{10}`\n\n"
        "**🔗 Powered By:** {11}"
    )
    
    SYSTEM = (
        "╭─────────────────────╮\n"
        "│  **💻 System Info**\n"
        "╰─────────────────────╯\n\n"
        "**🖥️ CPU Cores:** `{0}`\n"
        "**⚡ CPU Usage:** `{1}`\n"
        "**💾 Disk Usage:** `{2}`\n"
        "**🎯 RAM Usage:** `{3}`\n"
        "**⏰ Uptime:** `{4}`\n\n"
        "**🔗 Powered By:** {5}"
    )
    
    PING_REPLY = (
        "╭─────────────────────╮\n"
        "│  **🏓 Pong!**\n"
        "╰─────────────────────╯\n\n"
        "**⚡ Speed:** `{0} ms`\n"
        "**⏰ Uptime:** `{1}`\n"
        "**🎙️ VC Ping:** `{2} ms`"
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Startup & Source
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    BOOTED = (
        "╭─────────────────────╮\n"
        "│  **#START**\n"
        "│  **🎵 {0} is Alive!**\n"
        "╰─────────────────────╯\n\n"
        "**📦 Version Info:**\n"
        "├ **🎵 HellMusic:** `{1}`\n"
        "├ **🐍 Python:** `{2}`\n"
        "├ **📡 Pyrogram:** `{3}`\n"
        "└ **📞 PyTgCalls:** `{4}`\n\n"
        "**🔗 Powered By:** {5}"
    )
    
    SOURCE = (
        "╭─────────────────────╮\n"
        "│  **📦 Source Code**\n"
        "╰─────────────────────╯\n\n"
        "**📌 Note:**\n"
        "• The source code is available on GitHub\n"
        "• All projects under The-HellBot are open-source\n"
        "• Free to use and modify to your needs\n"
        "• Anyone selling this code is a scammer\n\n"
        "**⭐ Support Us:**\n"
        "• Star the repository if you like it\n"
        "• Contact us for help with the code\n\n"
        "**🔗 Powered By:** {0}"
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Help Texts
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    HELP_ADMIN = (
        "╭─────────────────────╮\n"
        "│  **👑 Admin Commands**\n"
        "╰─────────────────────╯\n\n"
        "**🔐 Authorization:**\n"
        "• `/auth` - Authorize user\n"
        "• `/unauth` - Unauthorize user\n"
        "• `/authlist` - List authorized users\n"
        "• `/authchat` - Enable for all users\n\n"
        "**🎵 Playback Control:**\n"
        "• `/mute` - Mute the stream\n"
        "• `/unmute` - Unmute the stream\n"
        "• `/pause` - Pause playback\n"
        "• `/resume` - Resume playback\n"
        "• `/stop` `/end` - Stop playback\n"
        "• `/skip` - Skip current track\n"
        "• `/replay` - Replay from start\n\n"
        "**⚙️ Advanced:**\n"
        "• `/loop [0-10]` - Loop track (0 to disable)\n"
        "• `/seek [seconds]` - Seek position\n"
        "• `/clean` - Clear queue when bugged\n"
    )
    
    HELP_USER = (
        "╭─────────────────────╮\n"
        "│  **👥 User Commands**\n"
        "╰─────────────────────╯\n\n"
        "**🎵 Play Music:**\n"
        "• `/play` - Play audio track\n"
        "• `/vplay` - Play video track\n"
        "• `/fplay` - Force play audio\n"
        "• `/fvplay` - Force play video\n\n"
        "**❤️ Favorites:**\n"
        "• `/favs` `/myfavs` - Show favorites\n"
        "• `/delfavs` - Delete favorites\n\n"
        "**ℹ️ Information:**\n"
        "• `/current` `/playing` - Now playing\n"
        "• `/queue` `/q` - View queue\n"
        "• `/song` - Download song\n"
        "• `/lyrics` - Get lyrics\n"
        "• `/profile` `/me` - Your profile\n"
    )
    
    HELP_SUDO = (
        "╭─────────────────────╮\n"
        "│  **⭐ Sudo Commands**\n"
        "╰─────────────────────╯\n\n"
        "**📊 Management:**\n"
        "• `/active` - Active voice chats\n"
        "• `/autoend` - Auto-end toggle\n"
        "• `/stats` - Full statistics\n"
        "• `/logs` - Get bot logs\n\n"
        "**🚫 Moderation:**\n"
        "• `/block` `/unblock` - Block user\n"
        "• `/blocklist` - Blocked users\n"
        "• `/gban` `/ungban` - Global ban\n"
        "• `/gbanlist` - Gbanned users\n\n"
        "**⚙️ System:**\n"
        "• `/restart` - Restart bot\n"
        "• `/sudolist` - Sudo users\n"
    )
    
    HELP_OTHERS = (
        "╭─────────────────────╮\n"
        "│  **📚 Other Commands**\n"
        "╰─────────────────────╯\n\n"
        "**ℹ️ General:**\n"
        "• `/start` - Check if alive\n"
        "• `/ping` - Check ping\n"
        "• `/help` - Show help menu\n"
        "• `/sysinfo` - System info\n"
        "• `/leaderboard` - Top users\n"
    )
    
    HELP_OWNERS = (
        "╭─────────────────────╮\n"
        "│  **🔱 Owner Commands**\n"
        "╰─────────────────────╯\n\n"
        "**💻 Execution:**\n"
        "• `/eval` `/run` - Python script\n"
        "• `/exec` `/sh` - Bash script\n\n"
        "**⚙️ Config:**\n"
        "• `/getvar` - Get config var\n\n"
        "**👑 Sudo Management:**\n"
        "• `/addsudo` - Add sudo user\n"
        "• `/rmsudo` - Remove sudo user\n"
    )
    
    HELP_GC = (
        "**❓ Need Help?**\n\n"
        "Get the complete help menu in your PM.\n"
        "Click the button below to get started!"
    )
    
    HELP_PM = (
        "╭─────────────────────╮\n"
        "│  **⚙️ Help Menu**\n"
        "╰─────────────────────╯\n\n"
        "**📌 Information:**\n"
        "• Commands are categorized by user type\n"
        "• Use buttons below to navigate\n"
        "• Contact us if you need assistance\n\n"
        "**🔗 Powered By:** {0}"
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Start Messages
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    START_GC = (
        "**🎵 HellMusic is Online!**\n\n"
        "Ready to play some awesome music?\n"
        "Use `/help` to see all commands!"
    )
    
    START_PM = (
        "╭─────────────────────╮\n"
        "│  **👋 Welcome!**\n"
        "╰─────────────────────╯\n\n"
        "**Hey** {0}**!**\n\n"
        "I'm **{1}**, an advanced music bot that can play music in Voice Chats with high quality streaming!\n\n"
        "**✨ Features:**\n"
        "• High-quality audio streaming\n"
        "• Video playback support\n"
        "• Queue management\n"
        "• Favorites system\n"
        "• Advanced controls\n\n"
        "Add me to your group and enjoy unlimited music!\n\n"
        "**🔗 Powered By:** @{2}"
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Miscellaneous
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    PERFORMER = "HellMusic V3"
    
    # Error messages
    ERROR_GENERIC = (
        "**❌ An Error Occurred**\n\n"
        "```{0}```\n\n"
        "Please try again later or contact support."
    )
    
    ERROR_NO_VC = (
        "**❌ No Active Voice Chat**\n\n"
        "Please start a voice chat first!"
    )
    
    ERROR_NO_PERMISSION = (
        "**❌ Insufficient Permissions**\n\n"
        "You don't have permission to use this command."
    )
    
    # Success messages
    SUCCESS_GENERIC = (
        "**✅ Success**\n\n"
        "{0}"
    )
    
    # Loading messages
    LOADING = "**⏳ Processing...**\n\nPlease wait..."
    SEARCHING = "**🔍 Searching...**\n\n`{0}`"
    DOWNLOADING = "**📥 Downloading...**\n\n`{0}`"
    PROCESSING = "**⚙️ Processing...**\n\n`{0}`"

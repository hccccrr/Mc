"""
HellMusic V3 - Button Manager
Modern inline keyboard buttons with enhanced design
"""

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class MakeButtons:
    """Advanced button creation system for HellMusic V3"""
    
    def __init__(self):
        self.ikb = InlineKeyboardButton

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Basic Navigation Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def close_markup(self):
        """Simple close button"""
        buttons = [[self.ikb("✖️ Close", callback_data="close")]]
        return InlineKeyboardMarkup(buttons)

    def back_close_markup(self, back_data: str):
        """Back and close buttons"""
        buttons = [
            [
                self.ikb("◀️ Back", callback_data=back_data),
                self.ikb("✖️ Close", callback_data="close"),
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Queue Management Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def queue_markup(self, count: int, page: int):
        """Queue navigation buttons"""
        if count > 1:
            buttons = [
                [
                    self.ikb("⏮️ Prev", callback_data=f"queue|prev|{page}"),
                    self.ikb("🎵 Playlist", callback_data=f"queue|list|{page}"),
                    self.ikb("⏭️ Next", callback_data=f"queue|next|{page}"),
                ],
                [
                    self.ikb("🔄 Shuffle", callback_data=f"queue|shuffle|{page}"),
                    self.ikb("✖️ Close", callback_data="close"),
                ],
            ]
        else:
            buttons = [
                [
                    self.ikb("🎵 Playlist", callback_data=f"queue|list|{page}"),
                    self.ikb("✖️ Close", callback_data="close"),
                ]
            ]
        return InlineKeyboardMarkup(buttons)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Favorites Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def playfavs_markup(self, user_id: int):
        """Play favorites selection"""
        buttons = [
            [
                self.ikb("🎵 Audio", callback_data=f"favsplay|audio|{user_id}"),
                self.ikb("🎬 Video", callback_data=f"favsplay|video|{user_id}"),
            ],
            [
                self.ikb("✖️ Close", callback_data=f"favsplay|close|{user_id}"),
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    async def favorite_markup(
        self, 
        collection: list, 
        user_id: int, 
        page: int, 
        index: int, 
        db, 
        delete: bool = False
    ):
        """Favorites list with delete options"""
        btns = []
        txt = ""
        d = 1 if delete else 0
        
        # Navigation buttons
        if len(collection) > 1:
            nav_btns = [
                [
                    self.ikb("❤️ Play All", callback_data=f"myfavs|play|{user_id}|0|0"),
                ],
                [
                    self.ikb("⏮️", callback_data=f"myfavs|prev|{user_id}|{page}|{d}"),
                    self.ikb("📊 Stats", callback_data=f"myfavs|stats|{user_id}|{page}|{d}"),
                    self.ikb("⏭️", callback_data=f"myfavs|next|{user_id}|{page}|{d}"),
                ],
                [
                    self.ikb("✖️ Close", callback_data=f"myfavs|close|{user_id}|{page}|{d}"),
                ]
            ]
        else:
            nav_btns = [
                [
                    self.ikb("❤️ Play All", callback_data=f"myfavs|play|{user_id}|0|0"),
                ],
                [
                    self.ikb("✖️ Close", callback_data=f"myfavs|close|{user_id}|{page}|{d}"),
                ],
            ]
        
        # Build favorites list
        try:
            for track in collection[page]:
                index += 1
                favs = await db.get_favorite(user_id, str(track))
                txt += f"**{index:02d}.** {favs['title']}\n"
                txt += f"     ⏱️ {favs['duration']} • 📅 {favs['add_date']}\n\n"
                btns.append(
                    self.ikb(
                        text=f"{index:02d}", 
                        callback_data=f"delfavs|{track}|{user_id}"
                    )
                )
        except:
            page = 0
            for track in collection[page]:
                index += 1
                favs = await db.get_favorite(user_id, track)
                txt += f"**{index:02d}.** {favs['title']}\n"
                txt += f"     ⏱️ {favs['duration']} • 📅 {favs['add_date']}\n\n"
                btns.append(
                    self.ikb(
                        text=f"{index:02d}", 
                        callback_data=f"delfavs|{track}|{user_id}"
                    )
                )

        # Add delete buttons if enabled
        if delete:
            # Group delete buttons in rows of 5
            btn_rows = [btns[i:i+5] for i in range(0, len(btns), 5)]
            btn_rows.append([
                self.ikb("🗑️ Delete All", callback_data=f"delfavs|all|{user_id}")
            ])
            buttons = btn_rows + nav_btns
        else:
            buttons = nav_btns

        return InlineKeyboardMarkup(buttons), txt

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Active VC Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def active_vc_markup(self, count: int, page: int):
        """Active voice chat navigation"""
        if count > 1:
            buttons = [
                [
                    self.ikb("⏮️", callback_data=f"activevc|prev|{page}"),
                    self.ikb("📊 Statistics", callback_data="activevc|stats"),
                    self.ikb("⏭️", callback_data=f"activevc|next|{page}"),
                ],
                [
                    self.ikb("✖️ Close", callback_data="close")
                ]
            ]
        else:
            buttons = [
                [
                    self.ikb("📊 Statistics", callback_data="activevc|stats"),
                    self.ikb("✖️ Close", callback_data="close")
                ]
            ]
        return InlineKeyboardMarkup(buttons)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Auth Users Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def authusers_markup(self, count: int, page: int, rand_key: str):
        """Authorized users navigation"""
        if count > 1:
            buttons = [
                [
                    self.ikb("⏮️", callback_data=f"authus|prev|{page}|{rand_key}"),
                    self.ikb("👥 Users", callback_data=f"authus|list|{page}|{rand_key}"),
                    self.ikb("⏭️", callback_data=f"authus|next|{page}|{rand_key}"),
                ],
                [
                    self.ikb("✖️ Close", callback_data=f"authus|close|{page}|{rand_key}")
                ]
            ]
        else:
            buttons = [
                [
                    self.ikb("👥 Users", callback_data=f"authus|list|{page}|{rand_key}"),
                    self.ikb("✖️ Close", callback_data=f"authus|close|{page}|{rand_key}")
                ]
            ]
        return InlineKeyboardMarkup(buttons)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Player Control Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def player_markup(self, chat_id: int, video_id: str, username: str):
        """Main player interface"""
        if video_id == "telegram":
            buttons = [
                [
                    self.ikb("🎛️ Controls", callback_data=f"controls|{video_id}|{chat_id}"),
                    self.ikb("✖️ Close", callback_data="close"),
                ]
            ]
        else:
            buttons = [
                [
                    self.ikb("ℹ️ Info", url=f"https://t.me/{username}?start=song_{video_id}"),
                ],
                [
                    self.ikb("❤️ Favorite", callback_data=f"add_favorite|{video_id}"),
                    self.ikb("🎛️ Controls", callback_data=f"controls|{video_id}|{chat_id}"),
                    self.ikb("📊 Stats", callback_data=f"stats|{video_id}|{chat_id}"),
                ],
                [
                    self.ikb("✖️ Close", callback_data="close"),
                ],
            ]
        return InlineKeyboardMarkup(buttons)

    def controls_markup(self, video_id: str, chat_id: int):
        """Advanced playback controls"""
        buttons = [
            [
                self.ikb("⏪", callback_data=f"ctrl|bseek|{chat_id}"),
                self.ikb("⏯️", callback_data=f"ctrl|play|{chat_id}"),
                self.ikb("⏩", callback_data=f"ctrl|fseek|{chat_id}"),
            ],
            [
                self.ikb("⏹️ Stop", callback_data=f"ctrl|end|{chat_id}"),
                self.ikb("🔁 Replay", callback_data=f"ctrl|replay|{chat_id}"),
                self.ikb("🔂 Loop", callback_data=f"ctrl|loop|{chat_id}"),
            ],
            [
                self.ikb("🔇 Mute", callback_data=f"ctrl|mute|{chat_id}"),
                self.ikb("🔊 Unmute", callback_data=f"ctrl|unmute|{chat_id}"),
                self.ikb("⏭️ Skip", callback_data=f"ctrl|skip|{chat_id}"),
            ],
            [
                self.ikb("🎵 Player", callback_data=f"player|{video_id}|{chat_id}"),
                self.ikb("✖️ Close", callback_data="close"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Download & Song Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def song_markup(self, rand_key: str, url: str, key: str):
        """Song download options"""
        buttons = [
            [
                self.ikb("🎬 YouTube", url=url),
            ],
            [
                self.ikb("🎵 Audio", callback_data=f"song_dl|adl|{key}|{rand_key}"),
                self.ikb("🎬 Video", callback_data=f"song_dl|vdl|{key}|{rand_key}"),
            ],
            [
                self.ikb("⏮️ Prev", callback_data=f"song_dl|prev|{key}|{rand_key}"),
                self.ikb("⏭️ Next", callback_data=f"song_dl|next|{key}|{rand_key}"),
            ],
            [
                self.ikb("✖️ Close", callback_data=f"song_dl|close|{key}|{rand_key}"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    def song_details_markup(self, url: str, ch_url: str):
        """Song details and channel link"""
        buttons = [
            [
                self.ikb("🎬 Video", url=url),
                self.ikb("📺 Channel", url=ch_url),
            ],
            [
                self.ikb("✖️ Close", callback_data="close"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Start & Help Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def start_markup(self, username: str):
        """Start in group button"""
        buttons = [
            [
                self.ikb("🎵 Start Music", url=f"https://t.me/{username}?start=start"),
                self.ikb("✖️ Close", callback_data="close"),
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    def start_pm_markup(self, username: str):
        """Start in PM buttons"""
        buttons = [
            [
                self.ikb("⚙️ Help", callback_data="help|back"),
                self.ikb("🔗 Source", callback_data="source"),
            ],
            [
                self.ikb("➕ Add To Group", url=f"https://t.me/{username}?startgroup=true"),
            ],
            [
                self.ikb("✖️ Close", callback_data="close"),
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    def help_gc_markup(self, username: str):
        """Help in group - redirect to PM"""
        buttons = [
            [
                self.ikb("❓ Get Help", url=f"https://t.me/{username}?start=help"),
                self.ikb("✖️ Close", callback_data="close"),
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    def help_pm_markup(self):
        """Help menu in PM"""
        buttons = [
            [
                self.ikb("👑 Admins", callback_data="help|admin"),
                self.ikb("👥 Users", callback_data="help|user"),
            ],
            [
                self.ikb("⭐ Sudos", callback_data="help|sudo"),
                self.ikb("📚 Others", callback_data="help|others"),
            ],
            [
                self.ikb("🔱 Owner", callback_data="help|owner"),
            ],
            [
                self.ikb("◀️ Back", callback_data="help|start"),
                self.ikb("✖️ Close", callback_data="close"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    def help_back(self):
        """Help back button"""
        buttons = [
            [
                self.ikb("◀️ Back", callback_data="help|back"),
                self.ikb("✖️ Close", callback_data="close"),
            ]
        ]
        return InlineKeyboardMarkup(buttons)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Source & Support Buttons
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def source_markup(self):
        """Source code and support links"""
        buttons = [
            [
                self.ikb("💻 GitHub", url="https://github.com/The-HellBot"),
                self.ikb("📦 Repository", url="https://github.com/The-HellBot/Music"),
            ],
            [
                self.ikb("🌐 HellBot Network", url="https://t.me/HellBot_Networks"),
            ],
            [
                self.ikb("💬 Support", url="https://t.me/HellBot_Chats"),
                self.ikb("📢 Updates", url="https://t.me/Its_HellBot"),
            ],
            [
                self.ikb("◀️ Back", callback_data="help|start"),
                self.ikb("✖️ Close", callback_data="close"),
            ]
        ]
        return InlineKeyboardMarkup(buttons)


# Global buttons instance
Buttons = MakeButtons()

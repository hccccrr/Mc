from telethon import Button


class MakeButtons:
    def __init__(self):
        # Telethon uses Button class directly
        pass

    def close_markup(self):
        """Close button"""
        buttons = [[Button.inline("🗑", data="close")]]
        return buttons

    def queue_markup(self, count: int, page: int):
        """Queue navigation buttons"""
        if count != 1:
            buttons = [
                [
                    Button.inline("⪨", data=f"queue|prev|{page}"),
                    Button.inline("🗑", data="close"),
                    Button.inline("⪩", data=f"queue|next|{page}"),
                ]
            ]
        else:
            buttons = [
                [
                    Button.inline("🗑", data="close"),
                ]
            ]
        return buttons

    def playfavs_markup(self, user_id: int):
        """Play favorites buttons"""
        buttons = [
            [
                Button.inline("Audio", data=f"favsplay|audio|{user_id}"),
                Button.inline("Video", data=f"favsplay|video|{user_id}"),
            ],
            [
                Button.inline("🗑", data=f"favsplay|close|{user_id}"),
            ]
        ]
        return buttons

    async def favorite_markup(
        self, collection: list, user_id: int, page: int, index: int, db, delete: bool
    ):
        """Favorites list with navigation"""
        btns = []
        txt = ""
        d = 0 if delete == True else 1
        
        if len(collection) != 1:
            nav_btns = [
                [
                    Button.inline("Play Favorites ❤️", data=f"myfavs|play|{user_id}|0|0"),
                ],
                [
                    Button.inline("⪨", data=f"myfavs|prev|{user_id}|{page}|{d}"),
                    Button.inline("🗑", data=f"myfavs|close|{user_id}|{page}|{d}"),
                    Button.inline("⪩", data=f"myfavs|next|{user_id}|{page}|{d}"),
                ]
            ]
        else:
            nav_btns = [
                [
                    Button.inline("Play Favorites ❤️", data=f"myfavs|play|{user_id}|0|0"),
                ],
                [
                    Button.inline("🗑", data=f"myfavs|close|{user_id}|{page}|{d}"),
                ],
            ]
        
        try:
            for track in collection[page]:
                index += 1
                favs = await db.get_favorite(user_id, str(track))
                txt += f"**{'0' if index < 10 else ''}{index}:** {favs['title']}\n"
                txt += f"    **Duration:** {favs['duration']}\n"
                txt += f"    **Since:** {favs['add_date']}\n\n"
                btns.append(Button.inline(text=f"{index}", data=f"delfavs|{track}|{user_id}"))
        except:
            page = 0
            for track in collection[page]:
                index += 1
                favs = await db.get_favorite(user_id, track)
                txt += f"**{'0' if index < 10 else ''}{index}:** {favs['title']}\n"
                txt += f"    **Duration:** {favs['duration']}\n"
                txt += f"    **Since:** {favs['add_date']}\n\n"
                btns.append(Button.inline(text=f"{index}", data=f"delfavs|{track}|{user_id}"))

        if delete:
            btns = [btns]
            btns.append([Button.inline(text="Delete All ❌", data=f"delfavs|all|{user_id}")])
            buttons = btns + nav_btns
        else:
            buttons = nav_btns

        return buttons, txt

    def active_vc_markup(self, count: int, page: int):
        """Active voice chats navigation"""
        if count != 1:
            buttons = [
                [
                    Button.inline(text="⪨", data=f"activevc|prev|{page}"),
                    Button.inline(text="🗑", data="close"),
                    Button.inline(text="⪩", data=f"activevc|next|{page}"),
                ]
            ]
        else:
            buttons = [[Button.inline(text="🗑", data="close")]]
        return buttons

    def authusers_markup(self, count: int, page: int, rand_key: str):
        """Authorized users navigation"""
        if count != 1:
            buttons = [
                [
                    Button.inline(text="⪨", data=f"authus|prev|{page}|{rand_key}"),
                    Button.inline(text="🗑", data=f"authus|close|{page}|{rand_key}"),
                    Button.inline(text="⪩", data=f"authus|next|{page}|{rand_key}"),
                ]
            ]
        else:
            buttons = [
                [
                    Button.inline(text="🗑", data=f"authus|close|{page}|{rand_key}")
                ]
            ]
        return buttons

    def player_markup(self, chat_id, video_id, username):
        """Player control buttons"""
        if video_id == "telegram":
            buttons = [
                [
                    Button.inline("🎛️", data=f"controls|{video_id}|{chat_id}"),
                    Button.inline("🗑", data="close"),
                ]
            ]
        else:
            buttons = [
                [
                    Button.url("About Song", url=f"https://t.me/{username}?start=song_{video_id}"),
                ],
                [
                    Button.inline("❤️", data=f"add_favorite|{video_id}"),
                    Button.inline("🎛️", data=f"controls|{video_id}|{chat_id}"),
                ],
                [
                    Button.inline("🗑", data="close"),
                ],
            ]
        return buttons

    def controls_markup(self, video_id, chat_id):
        """Playback controls"""
        buttons = [
            [
                Button.inline(text="⟲", data=f"ctrl|bseek|{chat_id}"),
                Button.inline(text="⦿", data=f"ctrl|play|{chat_id}"),
                Button.inline(text="⟳", data=f"ctrl|fseek|{chat_id}"),
            ],
            [
                Button.inline(text="⊡ End", data=f"ctrl|end|{chat_id}"),
                Button.inline(text="↻ Replay", data=f"ctrl|replay|{chat_id}"),
                Button.inline(text="∞ Loop", data=f"ctrl|loop|{chat_id}"),
            ],
            [
                Button.inline(text="⊠ Mute", data=f"ctrl|mute|{chat_id}"),
                Button.inline(text="⊜ Unmute", data=f"ctrl|unmute|{chat_id}"),
                Button.inline(text="⊹ Skip", data=f"ctrl|skip|{chat_id}"),
            ],
            [
                Button.inline(text="🔙", data=f"player|{video_id}|{chat_id}"),
                Button.inline(text="🗑", data="close"),
            ],
        ]
        return buttons

    def song_markup(self, rand_key, url, key):
        """Song download buttons"""
        buttons = [
            [
                Button.url(text="Visit Youtube", url=url),
            ],
            [
                Button.inline(text="Audio", data=f"song_dl|adl|{key}|{rand_key}"),
                Button.inline(text="Video", data=f"song_dl|vdl|{key}|{rand_key}"),
            ],
            [
                Button.inline(text="⪨", data=f"song_dl|prev|{key}|{rand_key}"),
                Button.inline(text="⪩", data=f"song_dl|next|{key}|{rand_key}"),
            ],
            [
                Button.inline(text="🗑", data=f"song_dl|close|{key}|{rand_key}"),
            ],
        ]
        return buttons

    def song_details_markup(self, url, ch_url):
        """Song details buttons"""
        buttons = [
            [
                Button.url(text="🎥", url=url),
                Button.url(text="📺", url=ch_url),
            ],
            [
                Button.inline(text="🗑", data="close"),
            ],
        ]
        return buttons

    def source_markup(self):
        """Source code and support buttons"""
        buttons = [
            [
                Button.url(text="Github ❤️", url="https://github.com/The-HellBot"),
                Button.url(text="Repo 📦", url="https://github.com/The-HellBot/Music"),
            ],
            [
                Button.url(text="Under HellBot Network { 🇮🇳 }", url="https://t.me/HellBot_Networks"),
            ],
            [
                Button.url(text="Support 🎙️", url="https://t.me/HellBot_Chats"),
                Button.url(text="Updates 📣", url="https://t.me/Its_HellBot"),
            ],
            [
                Button.inline(text="🔙", data="help|start"),
                Button.inline(text="🗑", data="close"),
            ]
        ]
        return buttons

    def start_markup(self, username: str):
        """Start button for groups"""
        buttons = [
            [
                Button.url(text="Start Me 🎵", url=f"https://t.me/{username}?start=start"),
                Button.inline(text="🗑", data="close"),
            ]
        ]
        return buttons

    def start_pm_markup(self, username: str):
        """Start menu buttons for PM"""
        buttons = [
            [
                Button.inline(text="Help ⚙️", data="help|back"),
                Button.inline(text="Source 📦", data="source"),
            ],
            [
                Button.url(text="Add Me To Group 👥", url=f"https://t.me/{username}?startgroup=true"),
            ],
            [
                Button.inline(text="🗑", data="close"),
            ]
        ]
        return buttons

    def help_gc_markup(self, username: str):
        """Help button for groups"""
        buttons = [
            [
                Button.url(text="Get Help ❓", url=f"https://t.me/{username}?start=help"),
                Button.inline(text="🗑", data="close"),
            ]
        ]
        return buttons

    def help_pm_markup(self):
        """Help menu buttons"""
        buttons = [
            [
                Button.inline(text="➊ Admins", data="help|admin"),
                Button.inline(text="➋ Users", data="help|user"),
            ],
            [
                Button.inline(text="➌ Sudos", data="help|sudo"),
                Button.inline(text="➍ Others", data="help|others"),
            ],
            [
                Button.inline(text="➎ Owner", data="help|owner"),
            ],
            [
                Button.inline(text="🔙", data="help|start"),
                Button.inline(text="🗑", data="close"),
            ],
        ]
        return buttons

    def help_back(self):
        """Back button for help"""
        buttons = [
            [
                Button.inline(text="🔙", data="help|back"),
                Button.inline(text="🗑", data="close"),
            ]
        ]
        return buttons


Buttons = MakeButtons()

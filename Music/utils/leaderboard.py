import asyncio
import datetime
import os
import time
import traceback

import aiofiles
from telethon.errors import FloodWaitError, PeerIdInvalidError

from config import Config
from Music.core.database import db


class Leaderboard:
    def __init__(self) -> None:
        self.file_name = "leaderboard.txt"

    def get_hrs(self) -> int:
        try:
            hrs = int(Config.LEADERBOARD_TIME.split(":")[0])
        except:
            hrs = 3
        return hrs

    def get_min(self) -> int:
        try:
            mins = int(Config.LEADERBOARD_TIME.split(":")[1])
        except:
            mins = 0
        return mins

    async def get_top_10_songs(self) -> list:
        """Get top 10 users by songs played"""
        users = await db.get_all_users()
        all_guys = []
        async for user in users:
            id = int(user["user_id"])
            songs = int(user.get("songs_played", 0))
            user_name = user["user_name"]
            context = {"id": id, "songs": songs, "user": user_name}
            all_guys.append(context)
        all_guys = sorted(all_guys, key=lambda x: x["songs"], reverse=True)
        top_10 = all_guys[:10]
        return top_10

    async def get_top_10_messages(self) -> list:
        """Get top 10 users by message count"""
        users = await db.get_all_users()
        all_guys = []
        async for user in users:
            id = int(user["user_id"])
            messages = int(user.get("messages_count", 0))
            user_name = user["user_name"]
            context = {"id": id, "messages": messages, "user": user_name}
            all_guys.append(context)
        all_guys = sorted(all_guys, key=lambda x: x["messages"], reverse=True)
        top_10 = all_guys[:10]
        return top_10

    async def generate_songs(self, bot_details: dict) -> str:
        """Generate leaderboard for songs"""
        index = 0
        top_10 = await self.get_top_10_songs()
        text = f"**🎵 Top 10 Music Lovers of {bot_details['mention']}**\n\n"
        for top in top_10:
            index += 1
            link = f"https://t.me/{bot_details['username']}?start=user_{top['id']}"
            text += f"**⤷ {'0' if index <= 9 else ''}{index}:** [{top['user']}]({link}) - **{top['songs']}** songs\n"
        text += "\n**🎧 Keep streaming! Enjoy the music!**"
        return text

    async def generate_messages(self, bot_details: dict) -> str:
        """Generate leaderboard for messages"""
        index = 0
        top_10 = await self.get_top_10_messages()
        text = f"**💬 Top 10 Active Chatters of {bot_details['mention']}**\n\n"
        for top in top_10:
            index += 1
            link = f"https://t.me/{bot_details['username']}?start=user_{top['id']}"
            text += f"**⤷ {'0' if index <= 9 else ''}{index}:** [{top['user']}]({link}) - **{top['messages']}** messages\n"
        text += "\n**💬 Keep chatting! Stay active!**"
        return text

    async def generate(self, bot_details: dict, leaderboard_type: str = "both") -> str:
        """
        Generate leaderboard text
        leaderboard_type: 'songs', 'messages', or 'both'
        """
        if leaderboard_type == "songs":
            return await self.generate_songs(bot_details)
        elif leaderboard_type == "messages":
            return await self.generate_messages(bot_details)
        else:  # both
            songs_text = await self.generate_songs(bot_details)
            messages_text = await self.generate_messages(bot_details)
            
            # Combine both leaderboards
            combined_text = f"{songs_text}\n\n{'─' * 35}\n\n{messages_text}"
            return combined_text

    async def broadcast(self, hellbot, text, buttons):
        start = time.time()
        success = failed = count = 0
        chats = await db.get_all_chats()
        async with aiofiles.open(self.file_name, mode="w") as leaderboard_log_file:
            async for chat in chats:
                try:
                    sts, msg = await self.send_message(
                        hellbot.app, buttons, int(chat["chat_id"]), text
                    )
                except Exception:
                    pass
                if msg is not None:
                    await leaderboard_log_file.write(msg)
                if sts == 1:
                    success += 1
                else:
                    failed += 1
                count += 1
                await asyncio.sleep(0.3)
        time_taken = datetime.timedelta(seconds=int(time.time() - start))
        await asyncio.sleep(3)
        to_log = f"**Leaderboard Auto Broadcast Completed in** `{time_taken}`\n\n**Total Chats:** `{count}`\n**Success:** `{success}`\n**Failed:** `{failed}`\n\n**🧡 Enjoy Streaming! Have Fun!**"
        if failed == 0:
            await hellbot.logit("leaderboard", to_log)
        else:
            await hellbot.logit("leaderboard", to_log, self.file_name)
        os.remove(self.file_name)

    async def send_message(self, hellbot, buttons, chat: int, text: str):
        """Send message to chat with error handling"""
        try:
            await hellbot.send_message(
                chat,
                text,
                buttons=buttons,
                link_preview=False,
            )
            return 1, None
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
            return await self.send_message(hellbot, buttons, chat, text)
        except PeerIdInvalidError:
            return 2, f"{chat} -:- chat id invalid\n"
        except Exception:
            return 3, f"{chat} -:- {traceback.format_exc()}\n"


leaders = Leaderboard()

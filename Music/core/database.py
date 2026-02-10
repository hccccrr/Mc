import datetime
import sys

from motor.motor_asyncio import AsyncIOMotorClient

from config import Config

from .logger import LOGS


class Database(object):
    def __init__(self):
        self.client = AsyncIOMotorClient(Config.DATABASE_URL)
        self.db = self.client["HellMusicDB"]

        # mongo db collections
        self.authchats = self.db.authchats
        self.authusers = self.db.authusers
        self.autoend = self.db.autoend
        self.blocked_users = self.db.blocked_users
        self.chats = self.db.chats
        self.favorites = self.db.favorites
        self.gban_db = self.db.gban_db
        self.songsdb = self.db.songsdb
        self.sudousers = self.db.sudousers
        self.users = self.db.users

        # local db collections
        self.active_vc = [{"chat_id": 0, "join_time": 0, "vc_type": "voice"}]
        self.inactive = {}
        self.loop = {}
        self.watcher = {}
        self.audio_effects = {}  # Store bass boost and speed settings

    # database connection #
    async def connect(self):
        try:
            self.client.admin.command("ping")
            LOGS.info("\x3e\x3e\x20\x44\x61\x74\x61\x62\x61\x73\x65\x20\x63\x6f\x6e\x6e\x65\x63\x74\x69\x6f\x6e\x20\x73\x75\x63\x63\x65\x73\x73\x66\x75\x6c\x21")
        except Exception as e:
            LOGS.error(f"\x44\x61\x74\x61\x62\x61\x73\x65\x20\x63\x6f\x6e\x6e\x65\x63\x74\x69\x6f\x6e\x20\x66\x61\x69\x6c\x65\x64\x3a\x20\x27{e}\x27")
            sys.exit()

    # users db #
    async def add_user(self, user_id: int, user_name: str):
        context = {
            "user_id": user_id,
            "user_name": user_name,
            "join_date": datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
            "songs_played": 0,
            "messages_count": 0,
            "last_msg_time": [],
            "spam_cooldown_until": None,
        }
        await self.users.insert_one(context)

    async def delete_user(self, user_id: int):
        await self.users.delete_one({"user_id": user_id})

    async def is_user_exist(self, user_id: int) -> bool:
        user = await self.users.find_one({"user_id": user_id})
        return bool(user)

    async def get_user(self, user_id: int):
        user = await self.users.find_one({"user_id": user_id})
        return user

    async def get_all_users(self):
        users = self.users.find({})
        return users

    async def total_users_count(self):
        count = await self.users.count_documents({})
        return count

    async def update_user(self, user_id: int, key: str, value):
        if key == "songs_played" or key == "messages_count":
            prev = await self.users.find_one({"user_id": user_id})
            if prev:
                value = prev.get(key, 0) + value
        await self.users.update_one({"user_id": user_id}, {"$set": {key: value}})

    # Message tracking with anti-spam #
    async def track_message(self, user_id: int, user_name: str) -> bool:
        """
        Track user messages and implement anti-spam
        Returns True if message should be counted, False if user is in cooldown
        """
        # Check if user exists
        if not await self.is_user_exist(user_id):
            await self.add_user(user_id, user_name)
        
        user = await self.get_user(user_id)
        current_time = datetime.datetime.now()
        
        # Check if user is in spam cooldown
        if user.get("spam_cooldown_until"):
            cooldown_until = user["spam_cooldown_until"]
            if isinstance(cooldown_until, str):
                cooldown_until = datetime.datetime.strptime(cooldown_until, "%Y-%m-%d %H:%M:%S")
            
            if current_time < cooldown_until:
                # User still in cooldown
                return False
            else:
                # Cooldown expired, reset
                await self.users.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "spam_cooldown_until": None,
                        "last_msg_time": []
                    }}
                )
        
        # Get last message times (keep only last 3 seconds)
        last_msg_time = user.get("last_msg_time", [])
        if isinstance(last_msg_time, list):
            # Convert string timestamps to datetime
            last_msg_time = [
                datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S.%f") 
                if isinstance(t, str) else t 
                for t in last_msg_time
            ]
        else:
            last_msg_time = []
        
        # Filter messages from last 3 seconds
        three_seconds_ago = current_time - datetime.timedelta(seconds=3)
        recent_messages = [t for t in last_msg_time if t > three_seconds_ago]
        
        # Add current message time
        recent_messages.append(current_time)
        
        # Check for spam (5+ messages in 3 seconds)
        if len(recent_messages) >= 5:
            # Apply 20 minute cooldown
            cooldown_until = current_time + datetime.timedelta(minutes=20)
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "spam_cooldown_until": cooldown_until.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_msg_time": []
                }}
            )
            return False
        
        # Update last message times
        recent_messages_str = [t.strftime("%Y-%m-%d %H:%M:%S.%f") for t in recent_messages]
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"last_msg_time": recent_messages_str}}
        )
        
        # Increment message count
        await self.update_user(user_id, "messages_count", 1)
        return True

    async def get_spam_cooldown(self, user_id: int):
        """Get remaining cooldown time for user"""
        user = await self.get_user(user_id)
        if not user or not user.get("spam_cooldown_until"):
            return None
        
        cooldown_until = user["spam_cooldown_until"]
        if isinstance(cooldown_until, str):
            cooldown_until = datetime.datetime.strptime(cooldown_until, "%Y-%m-%d %H:%M:%S")
        
        current_time = datetime.datetime.now()
        if current_time < cooldown_until:
            remaining = cooldown_until - current_time
            return remaining
        return None

    # chat db #
    async def add_chat(self, chat_id: int):
        context = {
            "chat_id": chat_id,
            "join_date": datetime.datetime.now(),
        }
        await self.chats.insert_one(context)

    async def delete_chat(self, chat_id: int):
        await self.chats.delete_one({"chat_id": chat_id})

    async def is_chat_exist(self, chat_id: int) -> bool:
        chat = await self.chats.find_one({"chat_id": chat_id})
        return bool(chat)

    async def get_chat(self, chat_id: int):
        chat = await self.chats.find_one({"chat_id": chat_id})
        return chat

    async def get_all_chats(self):
        chats = self.chats.find({})
        return chats

    async def total_chats_count(self):
        count = await self.chats.count_documents({})
        return count

    # active vc db #
    async def get_active_vc(self) -> list:
        return self.active_vc

    async def add_active_vc(self, chat_id: int, vc_type: str):
        cid = [x["chat_id"] for x in self.active_vc]
        if not chat_id in cid:
            self.active_vc.append(
                {
                    "chat_id": chat_id,
                    "join_time": datetime.datetime.now(),
                    "vc_type": vc_type,
                }
            )

    async def is_active_vc(self, chat_id: int) -> bool:
        cid = [x["chat_id"] for x in self.active_vc]
        if chat_id not in cid:
            return False
        else:
            return True

    async def remove_active_vc(self, chat_id: int):
        for x in self.active_vc:
            if x["chat_id"] == chat_id:
                self.active_vc.remove(x)

    async def total_actvc_count(self) -> int:
        count = self.active_vc
        return len(count) - 1

    # autoend db #
    async def get_autoend(self) -> bool:
        try:
            autoend = await self.autoend.find_one({"autoend": "on"})
            if autoend:
                return True
            else:
                return False
        except:
            return False

    async def set_autoend(self, autoend: bool):
        _db = await self.autoend.find_one({"autoend": "on"})
        if autoend is True:
            if _db:
                return
            await self.autoend.insert_one({"autoend": "on"})
        else:
            await self.autoend.delete_one({"autoend": "on"})

    # loop db #
    async def set_loop(self, chat_id: int, loop: int):
        self.loop[chat_id] = loop

    async def get_loop(self, chat_id: int) -> int:
        loop = self.loop.get(chat_id)
        return loop or 0

    # watcher db #
    async def set_watcher(self, chat_id: int, key: str, watch: bool):
        self.watcher[chat_id] = {key: watch}

    async def get_watcher(self, chat_id: int, key: str) -> bool:
        try:
            watch = self.watcher[chat_id][key]
        except KeyError:
            watch = False
        return watch

    # audio effects db #
    async def set_audio_effects(self, chat_id: int, bass_boost: int, speed: float):
        """Store audio effects settings for a chat"""
        self.audio_effects[chat_id] = {"bass_boost": bass_boost, "speed": speed}

    async def get_audio_effects(self, chat_id: int) -> dict:
        """Get audio effects settings for a chat"""
        return self.audio_effects.get(chat_id, {"bass_boost": 0, "speed": 1.0})

    async def reset_audio_effects(self, chat_id: int):
        """Reset audio effects to default"""
        self.audio_effects[chat_id] = {"bass_boost": 0, "speed": 1.0}

    # sudousers db #
    async def get_sudo_users(self) -> list:
        users = await self.sudousers.find_one({"sudo": "sudo"})
        if not users:
            return []
        return users["user_ids"]

    async def add_sudo(self, user_id: int) -> bool:
        users = await self.get_sudo_users()
        users.append(user_id)
        await self.sudousers.update_one(
            {"sudo": "sudo"}, {"$set": {"user_ids": users}}, upsert=True
        )
        return True

    async def remove_sudo(self, user_id: int) -> bool:
        users = await self.get_sudo_users()
        users.remove(user_id)
        await self.sudousers.update_one(
            {"sudo": "sudo"}, {"$set": {"user_ids": users}}, upsert=True
        )
        return True

    # blocked users db #
    async def get_blocked_users(self) -> list:
        users = await self.blocked_users.find_one({"blocked": "blocked"})
        if not users:
            return []
        return users["user_ids"]

    async def add_blocked_user(self, user_id: int) -> bool:
        users = await self.get_blocked_users()
        users.append(user_id)
        await self.blocked_users.update_one(
            {"blocked": "blocked"}, {"$set": {"user_ids": users}}, upsert=True
        )
        return True

    async def remove_blocked_user(self, user_id: int) -> bool:
        users = await self.get_blocked_users()
        users.remove(user_id)
        await self.blocked_users.update_one(
            {"blocked": "blocked"}, {"$set": {"user_ids": users}}, upsert=True
        )
        return True

    async def total_block_count(self) -> int:
        count = await self.get_blocked_users()
        return len(count)

    # gbanned users db #
    async def get_gbanned_users(self) -> list:
        users = await self.gban_db.find_one({"gbanned": "gbanned"})
        if not users:
            return []
        return users["user_ids"]

    async def add_gbanned_user(self, user_id: int) -> bool:
        users = await self.get_gbanned_users()
        users.append(user_id)
        await self.gban_db.update_one(
            {"gbanned": "gbanned"}, {"$set": {"user_ids": users}}, upsert=True
        )
        return True

    async def remove_gbanned_users(self, user_id: int) -> bool:
        users = await self.get_gbanned_users()
        users.remove(user_id)
        await self.gban_db.update_one(
            {"gbanned": "gbanned"}, {"$set": {"user_ids": users}}, upsert=True
        )
        return True

    async def is_gbanned_user(self, user_id: int) -> bool:
        users = await self.gban_db.find_one({"gbanned": "gbanned"})
        if users and user_id in users["user_ids"]:
            return True
        else:
            return False

    async def total_gbans_count(self) -> int:
        count = await self.get_gbanned_users()
        return len(count)

    # authusers db #
    async def add_authusers(self, chat_id: int, user_id: int, details: dict):
        await self.authusers.insert_one(
            {"chat_id": chat_id, "user_id": user_id, "details": details}
        )

    async def is_authuser(self, chat_id: int, user_id: int) -> bool:
        chat = await self.authusers.find_one({"chat_id": chat_id, "user_id": user_id})
        return bool(chat)

    async def get_authuser(self, chat_id: int, user_id: int):
        chat = await self.authusers.find_one({"chat_id": chat_id, "user_id": user_id})
        return chat["details"] if chat else {}

    async def get_all_authusers(self, chat_id: int) -> list:
        all_users = []
        users = self.authusers.find({"chat_id": chat_id})
        async for user in users:
            all_users.append(user["user_id"])
        return all_users if all_users else []

    async def remove_authuser(self, chat_id: int, user_id: int):
        await self.authusers.delete_one({"chat_id": chat_id, "user_id": user_id})

    # authchats db #
    async def get_authchats(self) -> list:
        chats = await self.authchats.find_one({"authchats": "authchats"})
        if not chats:
            return []
        return chats["chat_ids"]

    async def add_authchat(self, chat_id: int) -> bool:
        chats = await self.get_authchats()
        chats.append(chat_id)
        await self.authchats.update_one(
            {"authchats": "authchats"}, {"$set": {"chat_ids": chats}}, upsert=True
        )
        return True

    async def remove_authchat(self, chat_id: int) -> bool:
        chats = await self.get_authchats()
        chats.remove(chat_id)
        await self.authchats.update_one(
            {"authchats": "authchats"}, {"$set": {"chat_ids": chats}}, upsert=True
        )
        return True

    async def is_authchat(self, chat_id: int) -> bool:
        chats = await self.authchats.find_one({"authchats": "authchats"})
        if chats and chat_id in chats["chat_ids"]:
            return True
        return False

    # favorites db #
    async def get_favs(self, user_id: int) -> dict:
        favs = await self.favorites.find_one({"user_id": user_id})
        return favs["tracks"] if favs else {}

    async def add_favorites(self, user_id: int, video_id: str, context: dict):
        favs = await self.get_favs(user_id)
        favs[video_id] = context
        await self.favorites.update_one(
            {"user_id": user_id}, {"$set": {"tracks": favs}}, upsert=True
        )

    async def rem_favorites(self, user_id: int, video_id: str) -> bool:
        favs = await self.get_favs(user_id)
        if video_id in favs:
            del favs[video_id]
            await self.favorites.update_one(
                {"user_id": user_id}, {"$set": {"tracks": favs}}, upsert=True
            )
            return True
        return False

    async def get_all_favorites(self, user_id: int) -> list:
        favs = []
        for x in await self.get_favs(user_id):
            favs.append(x)
        return favs

    async def get_favorite(self, user_id: int, video_id: str) -> dict:
        favs = await self.get_favs(user_id)
        return favs[video_id] if video_id in favs else {}

    # songs db #
    async def total_songs_count(self) -> int:
        count = await self.songsdb.find_one({"songs": "songs"})
        if count:
            return count["count"]
        return 0

    async def update_songs_count(self, count: int):
        songs = await self.total_songs_count()
        songs = songs + count
        await self.songsdb.update_one(
            {"songs": "songs"}, {"$set": {"count": songs}}, upsert=True
        )


db = Database()
        

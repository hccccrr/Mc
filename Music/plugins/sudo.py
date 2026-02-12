import asyncio
import os
import shutil

from telethon import events
from telethon.errors import FloodWaitError

from config import Config
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import UserWrapper
from Music.core.users import user_data
from Music.helpers.broadcast import Gcast
from Music.helpers.formatters import formatter


@hellbot.app.on(events.NewMessage(pattern=r"^/autoend"))
@UserWrapper
async def auto_end_stream(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    parts = event.text.split()
    if len(parts) != 2:
        return await event.reply(
            "**Usage:**\n\n__To turn off autoend:__ `/autoend off`\n__To turn on autoend:__ `/autoend on`"
        )
    
    cmd = parts[1].lower()
    autoend = await db.get_autoend()
    
    if cmd == "on":
        if autoend:
            await event.reply("AutoEnd is already enabled.")
        else:
            await db.set_autoend(True)
            await event.reply(
                "AutoEnd Enabled! Now I will automatically end the stream after 5 minutes when the VC is empty."
            )
    elif cmd == "off":
        if autoend:
            await db.set_autoend(False)
            await event.reply("AutoEnd Disabled!")
        else:
            await event.reply("AutoEnd is already disabled.")
    else:
        await event.reply(
            "**Usage:**\n\n__To turn off autoend:__ `/autoend off`\n__To turn on autoend:__ `/autoend on`"
        )


@hellbot.app.on(events.NewMessage(pattern=r"^/(gban|block)"))
@UserWrapper
async def gban(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    replied = await event.get_reply_message() if event.is_reply else None
    parts = event.text.split()
    cmd = parts[0][1:]  # Remove /
    
    if not replied:
        if len(parts) != 2:
            return await event.reply("Reply to a user's message or give their id.")
        
        user = await hellbot.app.get_entity(parts[1])
        user_id = user.id
        mention = f"[{user.first_name}](tg://user?id={user.id})"
    else:
        user = await replied.get_sender()
        user_id = user.id
        mention = f"[{user.first_name}](tg://user?id={user.id})"
    
    if user_id == event.sender_id:
        return await event.reply(f"You can't {cmd} yourself.")
    elif user_id == hellbot.app.me.id:
        return await event.reply(f"Yo! I'm not stupid to {cmd} myself.")
    elif user_id in Config.SUDO_USERS:
        return await event.reply(f"I can't {cmd} my sudo users.")
    
    is_gbanned = await db.is_gbanned_user(user_id)
    if is_gbanned:
        return await event.reply(f"{mention} is already in {cmd} list.")
    
    if user_id not in Config.BANNED_USERS:
        Config.BANNED_USERS.add(user_id)
    
    if cmd == "gban":
        all_chats = []
        chats = await db.get_all_chats()
        async for chat in chats:
            all_chats.append(int(chat["chat_id"]))
        
        eta = formatter.get_readable_time(len(all_chats))
        hell = await event.reply(
            f"{mention} is being gbanned from by the bot. This might take around {eta}."
        )
        
        count = 0
        for chat_id in all_chats:
            try:
                await hellbot.app.edit_permissions(chat_id, user_id, view_messages=False)
                count += 1
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception:
                pass
        
        await db.add_gbanned_user(user_id)
        await event.reply(
            f"**Gbanned Successfully!**\n\n**User:** {mention}\n**Chats:** `{count} chats`"
        )
        await hell.delete()
    else:
        await db.add_blocked_user(user_id)
        await event.reply(f"**Blocked Successfully!**\n\n**User:** {mention}")


@hellbot.app.on(events.NewMessage(pattern=r"^/(ungban|unblock)"))
@UserWrapper
async def ungban(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    replied = await event.get_reply_message() if event.is_reply else None
    parts = event.text.split()
    cmd = parts[0][1:]  # Remove /
    
    if not replied:
        if len(parts) != 2:
            return await event.reply("Reply to a user's message or give their id.")
        
        user = await hellbot.app.get_entity(parts[1])
        user_id = user.id
        mention = f"[{user.first_name}](tg://user?id={user.id})"
    else:
        user = await replied.get_sender()
        user_id = user.id
        mention = f"[{user.first_name}](tg://user?id={user.id})"
    
    is_gbanned = await db.is_gbanned_user(user_id)
    if not is_gbanned:
        return await event.reply(f"{mention} is not in {cmd[2:]} list.")
    
    if user_id in Config.BANNED_USERS:
        Config.BANNED_USERS.remove(user_id)
    
    if cmd == "ungban":
        all_chats = []
        chats = await db.get_all_chats()
        async for chat in chats:
            all_chats.append(int(chat["chat_id"]))
        
        eta = formatter.get_readable_time(len(all_chats))
        hell = await event.reply(
            f"{mention} is being ungban from by the bot. This might take around {eta}."
        )
        
        count = 0
        for chat_id in all_chats:
            try:
                await hellbot.app.edit_permissions(chat_id, user_id, view_messages=True)
                count += 1
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception:
                pass
        
        await db.remove_gbanned_users(user_id)
        await event.reply(
            f"**Ungbanned Successfully!**\n\n**User:** {mention}\n**Chats:** `{count}`"
        )
        await hell.delete()
    else:
        await db.remove_blocked_user(user_id)
        await event.reply(f"**Unblocked Successfully!**\n\n**User:** {mention}")


@hellbot.app.on(events.NewMessage(pattern=r"^/(gbanlist|blocklist)"))
@UserWrapper
async def gbanned_list(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    cmd = event.text.split()[0][1:]
    
    if cmd == "gbanlist":
        users = await db.get_gbanned_users()
        if len(users) == 0:
            return await event.reply("No Gbanned Users Found!")
        hell = await event.reply("Fetching Gbanned Users...")
        msg = "**Gbanned Users:**\n\n"
    else:
        users = await db.get_blocked_users()
        if len(users) == 0:
            return await event.reply("No Blocked Users Found!")
        hell = await event.reply("Fetching Blocked Users...")
        msg = "**Blocked Users:**\n\n"
    
    count = 0
    for user_id in users:
        count += 1
        try:
            user = await hellbot.app.get_entity(user_id)
            user_name = f"[{user.first_name}](tg://user?id={user.id})"
            msg += f"{'0' if count <= 9 else ''}{count}: {user_name} `{user_id}`\n"
        except Exception:
            msg += f"{'0' if count <= 9 else ''}{count}: [User] `{user_id}`\n"
            continue
    
    if count == 0:
        return await hell.edit(f"Nobody is in {cmd}!")
    else:
        return await hell.edit(msg)


@hellbot.app.on(events.NewMessage(pattern=r"^/logs"))
@UserWrapper
async def log_(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    try:
        if os.path.exists("HellMusic.log"):
            log = open("HellMusic.log", "r")
            lines = log.readlines()
            logdata = ""
            
            try:
                parts = event.text.split()
                limit = int(parts[1]) if len(parts) > 1 else 100
            except:
                limit = 100
            
            for x in lines[-limit:]:
                logdata += x
            
            link = await formatter.bb_paste(logdata)
            return await event.reply(
                f"**Logs:** {link}",
                file="HellMusic.log"
            )
        else:
            return await event.reply("No Logs Found!")
    except Exception as e:
        await event.reply(f"**ERROR:** \n\n`{e}`")


@hellbot.app.on(events.NewMessage(pattern=r"^/restart"))
@UserWrapper
async def restart_(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    hell = await event.reply("Notifying Chats about restart....")
    active_chats = await db.get_active_vc()
    count = 0
    
    for x in active_chats:
        cid = int(x["chat_id"])
        try:
            await hellbot.app.send_message(
                cid,
                "**Bot is restarting in a minute or two.**\n\nPlease wait for a minute before using me again.",
            )
            await hellmusic.leave_vc(cid)
            count += 1
        except Exception:
            pass
    
    try:
        shutil.rmtree("cache")
        shutil.rmtree("downloads")
    except:
        pass
    
    await hell.edit(
        f"Notified **{count}** chat(s) about the restart.\n\nRestarting now..."
    )
    os.system(f"kill -9 {os.getpid()} && bash StartMusic")


@hellbot.app.on(events.NewMessage(pattern=r"^/sudolist"))
@UserWrapper
async def sudoers_list(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    text = "**⟢ God Users:**\n"
    gods = 0
    
    for x in Config.GOD_USERS:
        try:
            if x in user_data.DEVS:
                continue
            user = await hellbot.app.get_entity(x)
            user_name = f"[{user.first_name}](tg://user?id={user.id})"
            gods += 1
            text += f"{'0' if gods <= 9 else ''}{gods}: {user_name}\n"
        except Exception:
            continue
    
    sudos = 0
    for user_id in Config.SUDO_USERS:
        if user_id not in user_data.DEVS:
            if user_id in Config.GOD_USERS:
                continue
            try:
                user = await hellbot.app.get_entity(user_id)
                user_name = f"[{user.first_name}](tg://user?id={user.id})"
                if sudos == 0:
                    sudos += 1
                    text += "\n**⟢ Sudo Users:**\n"
                gods += 1
                text += f"{'0' if gods <= 9 else ''}{gods}: {user_name}\n"
            except Exception:
                continue
    
    if gods == 0:
        await event.reply("No sudo users found.")
    else:
        await event.reply(text)


@hellbot.app.on(events.NewMessage(pattern=r"^/gcast"))
async def gcast(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    if not event.is_reply:
        await event.reply("Reply to a message to brodcast it.")
    else:
        parts = event.text.split()
        if len(parts) == 1:
            await event.reply(
                "Where to gcast? \n\n"
                "**With Forward Tag:** `/gcast chats` \n- `/gcast users` \n- `/gcast all`\n\n"
                "**Without Forward Tag:** `/gcast chats copy` \n- `/gcast users copy` \n- `/gcast all copy`"
            )
            return
        
        type_text = parts[1].lower()
        if type_text == "chats":
            type = "chats"
        elif type_text == "users":
            type = "users"
        elif type_text == "all":
            type = "all"
        else:
            return await event.reply("Invalid type. Use: chats, users, or all")
        
        copy = False
        if len(parts) >= 3:
            if parts[2].lower() == "copy":
                copy = True
        
        await Gcast.broadcast(event, type, copy)
    

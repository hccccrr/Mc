import datetime

from telethon import events

from config import Config
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import AdminWrapper, check_mode
from Music.helpers.formatters import formatter
from Music.utils.pages import MakePages


@hellbot.app.on(events.NewMessage(pattern=r"^/auth$|^/auth\s"))
@check_mode
@AdminWrapper
async def auth(event):
    # Check group and banned
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    replied = await event.get_reply_message() if event.is_reply else None
    
    if not replied:
        parts = event.text.split()
        if len(parts) != 2:
            return await event.reply(
                "Reply to a user or give a user id or username"
            )
        
        all_auths = await db.get_all_authusers(event.chat_id)
        count = len(all_auths)
        if count == 30:
            return await event.reply(
                "AuthList is full! \n\nLimit of Auth Users in a chat is: `30`"
            )
        
        user = parts[1].replace("@", "")
        user = await hellbot.app.get_entity(user)
        is_auth = await db.is_authuser(event.chat_id, user.id)
        
        if not is_auth:
            sender = await event.get_sender()
            context = {
                "user_name": user.first_name,
                "auth_by_id": event.sender_id,
                "auth_by_name": sender.first_name,
                "auth_date": datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
            }
            await db.add_authusers(event.chat_id, user.id, context)
            await event.reply("Successfully Authorized user in this chat!")
        else:
            await event.reply("This user is already Authorized in this chat!")
    else:
        all_auths = await db.get_all_authusers(event.chat_id)
        count = len(all_auths)
        if count == 30:
            return await event.reply(
                "AuthList is full! \n\nLimit of Auth Users in a chat is: `30`"
            )
        
        user = await replied.get_sender()
        is_auth = await db.is_authuser(event.chat_id, user.id)
        
        if not is_auth:
            sender = await event.get_sender()
            context = {
                "user_name": user.first_name,
                "auth_by_id": event.sender_id,
                "auth_by_name": sender.first_name,
                "auth_date": datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
            }
            await db.add_authusers(event.chat_id, user.id, context)
            await event.reply("Successfully Authorized user in this chat!")
        else:
            await event.reply("This user is already Authorized in this chat!")


@hellbot.app.on(events.NewMessage(pattern=r"^/unauth$|^/unauth\s"))
@check_mode
@AdminWrapper
async def unauth(event):
    # Check group and banned
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    replied = await event.get_reply_message() if event.is_reply else None
    
    if not replied:
        parts = event.text.split()
        if len(parts) != 2:
            return await event.reply(
                "Reply to a user or give a user id or username"
            )
        
        user = parts[1].replace("@", "")
        user = await hellbot.app.get_entity(user)
        is_auth = await db.is_authuser(event.chat_id, user.id)
        
        if is_auth:
            await db.remove_authuser(event.chat_id, user.id)
            await event.reply("Removed user's Authorization in this chat!")
        else:
            await event.reply("This user was not Authorized in this chat!")
    else:
        user = await replied.get_sender()
        is_auth = await db.is_authuser(event.chat_id, user.id)
        
        if is_auth:
            await db.remove_authuser(event.chat_id, user.id)
            await event.reply("Removed user's Authorization in this chat!")
        else:
            await event.reply("This user was not Authorized in this chat!")


@hellbot.app.on(events.NewMessage(pattern=r"^/authlist"))
@check_mode
async def authusers(event):
    # Check group and banned
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    all_auths = await db.get_all_authusers(event.chat_id)
    if not all_auths:
        await event.reply("No Authorized users in this chat!")
    else:
        hell = await event.reply("Fetching Authorized users in this chat ...")
        collection = []
        for user in all_auths:
            data = await db.get_authuser(event.chat_id, user)
            user_name = data["user_name"]
            admin_id = data["auth_by_id"]
            admin_name = data["auth_by_name"]
            auth_date = data["auth_date"]
            context = {
                "auth_user": user_name,
                "admin_id": admin_id,
                "admin_name": admin_name,
                "auth_date": auth_date,
            }
            collection.append(context)
        rand_key = formatter.gen_key(f"auth{event.chat_id}", 4)
        Config.CACHE[rand_key] = collection
        await MakePages.authusers_page(hell, rand_key, 0, 0, True)


@hellbot.app.on(events.NewMessage(pattern=r"^/authchat"))
@AdminWrapper
async def settings(event):
    # Check group and banned
    if not event.is_group:
        return
    if event.sender_id in Config.BANNED_USERS:
        return
    
    is_auth = await db.is_authchat(event.chat_id)
    parts = event.text.split()
    
    if len(parts) != 2:
        return await event.reply(
            f"Current AuthChat Status: `{'On' if is_auth else 'Off'}`\n\nUsage: `/authchat on` or `/authchat off`"
        )
    
    if parts[1] == "on":
        if is_auth:
            await event.reply("AuthChat is already On!")
        else:
            await db.add_authchat(event.chat_id)
            await event.reply(
                "**Turned On AuthChat!** \n\nNow all users can use bot commands in this chat!"
            )
    elif parts[1] == "off":
        if is_auth:
            await db.remove_authchat(event.chat_id)
            await event.reply(
                "**Turned Off AuthChat!** \n\nNow only Authorized users can use bot commands in this chat!"
            )
        else:
            await event.reply("AuthChat is already Off!")
    else:
        await event.reply(
            f"Current AuthChat Status: `{'On' if is_auth else 'Off'}`\n\nUsage: `/authchat on` or `/authchat off`"
        )


@hellbot.app.on(events.CallbackQuery(pattern=b"authus"))
async def authus_cb(event):
    if event.sender_id in Config.BANNED_USERS:
        return
    
    data = event.data.decode().split("_")
    _, action, page, rand_key = data
    
    if action == "close":
        Config.CACHE.pop(rand_key)
        await event.delete()
    else:
        collection = Config.CACHE[rand_key]
        length = len(collection) - 1
        page = int(page)
        
        if page == 0 and action == "prev":
            page = length
        elif page == length and action == "next":
            page = 0
        else:
            page = page + 1 if action == "next" else page - 1
        
        index = page * 6
        await MakePages.authusers_page(event, rand_key, page, index, True)
        

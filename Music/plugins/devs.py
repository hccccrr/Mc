import asyncio
import io
import os
import re
import subprocess
import sys
import traceback
from datetime import datetime

from git import Repo, InvalidGitRepositoryError, GitCommandError
from telethon import events

from config import Config, all_vars
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.core.decorators import UserWrapper


async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {l_}" for l_ in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)


@hellbot.app.on(events.NewMessage(pattern=r"^/(eval|run)"))
async def eval_cmd(event):
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    hell = await event.reply("**Processing...**")
    parts = event.text.split(maxsplit=1)
    
    if len(parts) != 2:
        return await hell.edit("**Received empty message!**")
    
    cmd = parts[1].strip()
    reply_to = await event.get_reply_message() if event.is_reply else event

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    
    try:
        await aexec(cmd, hellbot, event)
    except Exception:
        exc = traceback.format_exc()
    
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Success"
    
    final_output = "<b>EVAL</b>: "
    final_output += f"<code>{cmd}</code>\n\n"
    final_output += "<b>OUTPUT</b>:\n"
    final_output += f"<code>{evaluation.strip()}</code> \n"
    
    if len(final_output) > 4096:
        with io.BytesIO(str.encode(final_output)) as out_file:
            out_file.name = "eval.txt"
            await reply_to.reply(cmd[:1000], file=out_file)
    else:
        await reply_to.reply(final_output, parse_mode='html')
    await hell.delete()


@hellbot.app.on(events.NewMessage(pattern=r"^/(exec|term|sh|shell)"))
async def term(event):
    if event.sender_id not in Config.GOD_USERS:
        return
    
    hell = await event.reply("**Processing...**")
    parts = event.text.split(maxsplit=1)
    
    if len(parts) != 2:
        return await hell.edit("**Received empty message!**")
    
    cmd = parts[1].strip()
    
    if "\n" in cmd:
        code = cmd.split("\n")
        output = ""
        for x in code:
            shell = re.split(""" (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", x)
            try:
                process = subprocess.Popen(
                    shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            except Exception as err:
                await hell.edit(f"**Error:** \n`{err}`")
                return
            output += f"**{code}**\n"
            output += process.stdout.read()[:-1].decode("utf-8")
            output += "\n"
    else:
        shell = re.split(""" (?=(?:[^'"]|'[^']*'|"[^"]*")*$)""", cmd)
        for a in range(len(shell)):
            shell[a] = shell[a].replace('"', "")
        try:
            process = subprocess.Popen(
                shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except Exception as err:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            errors = traceback.format_exception(exc_type, exc_obj, exc_tb)
            await hell.edit("**Error:**\n`{}`".format("".join(errors)))
            return
        output = process.stdout.read()[:-1].decode("utf-8")
    
    if str(output) == "\n":
        output = None
    
    if output:
        if len(output) > 4096:
            filename = "output.txt"
            with open(filename, "w+") as file:
                file.write(output)
            await event.reply(f"`{cmd}`", file=filename)
            os.remove(filename)
            return
        await hell.edit(f"**Output:**\n`{output}`")
    else:
        await hell.edit("**Output:**\n`No Output`")


@hellbot.app.on(events.NewMessage(pattern=r"^/(getvar|gvar|var)"))
async def varget_(event):
    if event.sender_id not in Config.GOD_USERS:
        return
    
    parts = event.text.split()
    if len(parts) != 2:
        return await event.reply("**Give a variable name to get it's value.**")
    
    check_var = parts[1]
    if check_var.upper() not in all_vars:
        return await event.reply("**Give a valid variable name to get it's value.**")
    
    output = Config.__dict__[check_var.upper()]
    if not output:
        await event.reply("**No Output Found!**")
    else:
        return await event.reply(f"**{check_var}:** `{str(output)}`")


@hellbot.app.on(events.NewMessage(pattern=r"^/addsudo"))
async def useradd(event):
    if event.sender_id not in Config.GOD_USERS:
        return
    
    if not event.is_reply:
        parts = event.text.split()
        if len(parts) != 2:
            return await event.reply(
                "**Reply to a user or give a user id to add them as sudo.**"
            )
        user = parts[1].replace("@", "")
        user = await hellbot.app.get_entity(user)
        
        if user.id in Config.SUDO_USERS:
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            return await event.reply(f"**{mention} is already a sudo user.**")
        
        added = await db.add_sudo(user.id)
        if added:
            Config.SUDO_USERS.add(user.id)
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            await event.reply(f"**{mention} is now a sudo user.**")
        else:
            await event.reply("**Failed to add sudo user.**")
        return
    
    replied = await event.get_reply_message()
    user = await replied.get_sender()
    
    if user.id in Config.SUDO_USERS:
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        return await event.reply(f"**{mention} is already a sudo user.**")
    
    added = await db.add_sudo(user.id)
    if added:
        Config.SUDO_USERS.add(user.id)
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        await event.reply(f"**{mention} is now a sudo user.**")
    else:
        await event.reply("**Failed to add sudo user.**")


@hellbot.app.on(events.NewMessage(pattern=r"^/(delsudo|rmsudo)"))
async def userdel(event):
    if event.sender_id not in Config.GOD_USERS:
        return
    
    if not event.is_reply:
        parts = event.text.split()
        if len(parts) != 2:
            return await event.reply(
                "**Reply to a user or give a user id to remove them from sudo.**"
            )
        user = parts[1].replace("@", "")
        user = await hellbot.app.get_entity(user)
        
        if user.id not in Config.SUDO_USERS:
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            return await event.reply(f"**{mention} is not a sudo user.**")
        
        removed = await db.remove_sudo(user.id)
        if removed:
            Config.SUDO_USERS.remove(user.id)
            mention = f"[{user.first_name}](tg://user?id={user.id})"
            await event.reply(f"**{mention} is no longer a sudo user.**")
            return
        await event.reply("**Failed to remove sudo user.**")
        return
    
    replied = await event.get_reply_message()
    user_id = replied.sender_id
    user = await replied.get_sender()
    
    if user_id not in Config.SUDO_USERS:
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        return await event.reply(f"**{mention} is not a sudo user.**")
    
    removed = await db.remove_sudo(user_id)
    if removed:
        Config.SUDO_USERS.remove(user_id)
        mention = f"[{user.first_name}](tg://user?id={user.id})"
        await event.reply(f"**{mention} is no longer a sudo user.**")
        return
    await event.reply("**Failed to remove sudo user.**")


@hellbot.app.on(events.NewMessage(pattern=r"^/(update|gitpull)"))
@UserWrapper
async def update_(event):
    """Update the bot from git repository"""
    if event.sender_id not in Config.SUDO_USERS:
        return
    
    # Check if on Heroku
    if "DYNO" in os.environ:
        return await event.reply(
            "**Heroku Update:**\n"
            "Please use Heroku dashboard or CLI to update your bot on Heroku."
        )
    
    response = await event.reply("**Checking for updates...**")
    
    try:
        repo = Repo()
    except GitCommandError:
        return await response.edit(
            "**Git Error:**\n"
            "Git command failed. Make sure git is installed properly."
        )
    except InvalidGitRepositoryError:
        return await response.edit(
            "**Invalid Repository:**\n"
            "The directory is not a valid git repository."
        )
    
    # Fetch updates
    upstream_branch = Config.UPSTREAM_BRANCH if hasattr(Config, 'UPSTREAM_BRANCH') else "main"
    to_exc = f"git fetch origin {upstream_branch} &> /dev/null"
    os.system(to_exc)
    await asyncio.sleep(3)
    
    # Check for updates
    verification = ""
    REPO_URL = repo.remotes.origin.url.split(".git")[0]
    
    for checks in repo.iter_commits(f"HEAD..origin/{upstream_branch}"):
        verification = str(checks.count())
    
    if verification == "":
        return await response.edit(f"**Bot is up-to-date with** `{upstream_branch}`")
    
    # Pull updates
    os.system("git stash push -m 'Stashing local changes' -- .env .env.backup")
    os.system(f"git pull origin {upstream_branch}")
    
    # Notify active chats
    try:
        active_chats = await db.get_active_vc()
        for x in active_chats:
            cid = int(x["chat_id"])
            try:
                await hellbot.app.send_message(
                    cid,
                    f"**{hellbot.app.me.username} is updating...**\n\nBot will be back in a minute.",
                )
                await hellmusic.leave_vc(cid)
            except:
                pass
    except:
        pass
    
    # Restart
    await asyncio.sleep(2)
    os.system("pip3 install -r requirements.txt &> /dev/null")
    os.system(f"kill -9 {os.getpid()} && bash StartMusic")
    exit()
    

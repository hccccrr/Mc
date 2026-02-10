import os
import base64
import ipaddress
import random
import struct
from random import randint

try:
    from instagrapi import Client as IClient
    from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired
except:
    os.system("pip install instagrapi")
    from instagrapi import Client as IClient
    from instagrapi.exceptions import ChallengeRequired, TwoFactorRequired

try:
    from telethon.sessions import StringSession
    from telethon.sessions.string import (_STRUCT_PREFORMAT, CURRENT_VERSION,
                                          StringSession)
    from telethon.sync import TelegramClient
except:
    os.system("pip install telethon")
    from telethon.sessions import StringSession
    from telethon.sessions.string import (_STRUCT_PREFORMAT, CURRENT_VERSION,
                                          StringSession)
    from telethon.sync import TelegramClient


def main():
    print("T E A M    H E L L B O T   ! !")
    print("Hello!! Welcome to HellBot Session Generator\n")
    print("Human Verification Required !!")
    while True:
        verify = int(randint(1, 50))
        okvai = int(input(f"Enter {verify} to continue: "))
        if okvai == verify:
            print("\nChoose the string session type: \n1. Telethon (Music Bot) \n2. Instagram")
            while True:
                library = input("\nYour Choice: ")
                if library == "1":
                    generate_telethon_session()
                    break
                elif library == "2":
                    generate_insta_session()
                    break
                else:
                    print("Please enter integer values (1/2 only).")
            break
        else:
            print("Verification Failed! Try Again:")


def generate_telethon_session():
    print("\n✨ Telethon Session For HellBot Music!")
    APP_ID = int(input("\nEnter APP ID here: "))
    API_HASH = input("\nEnter API HASH here: ")
    
    print("\n📱 Please login to your Telegram account...")
    print("Note: Use the account you want to use as the assistant/userbot for the music bot.")
    
    with TelegramClient(StringSession(), APP_ID, API_HASH) as hellbot:
        session_string = hellbot.session.save()
        
        print("\n✅ Session generated successfully!")
        print("\n🔐 Your HellBot Telethon Session String:")
        print("=" * 60)
        print(session_string)
        print("=" * 60)
        
        # Try to send to saved messages
        try:
            hellbot.send_message(
                "me",
                f"**#HELLBOT #TELETHON #MUSIC_BOT**\n\n"
                f"**Session String:**\n"
                f"`{session_string}`\n\n"
                f"**⚠️ Keep this session string private!**\n"
                f"Add this to your bot's environment variables as `STRING_SESSION`",
            )
            print("\n📩 Session string also sent to your Telegram Saved Messages!")
        except Exception as e:
            print(f"\n⚠️ Could not send to Saved Messages: {e}")
        
        print("\n📝 Copy the session string above and add it to your .env file or environment variables as:")
        print("STRING_SESSION=<your_session_string>")


def generate_insta_session():
    print("Instagram Session For HellBot!")
    cl = IClient()
    username = input("Enter your Instagram Username: ")
    password = input("Enter your Instagram Password: ")
    try:
        cl.login(username, password)
        xyz = cl.get_settings()
        sessionid = xyz['authorization_data']['sessionid']
        print(f"Your Instagram Session is: \n>>> {sessionid}")
        print("\nCopy it from here and remember not to share it with anyone!")
    except (ChallengeRequired, TwoFactorRequired, Exception) as e:
        print(e)


def challenge_code(username, choice):
    while True:
        otp = input("Enter the OTP sent to your Email: ")
        if otp.isdigit():
            break
        else:
            print("Enter digits only!")
    return otp


if __name__ == "__main__":
    main()

import datetime
import os

from ntgcalls import TelegramServerError
from telethon import TelegramClient
from telethon.errors import (
    ChatAdminRequiredError,
    FloodWaitError,
    UserAlreadyParticipantError,
    UserNotParticipantError,
)
from telethon.tl.types import (
    InputMessagesFilterPhotos,
    KeyboardButtonRow,
)
from pytgcalls import PyTgCalls
from pytgcalls.exceptions import NoActiveGroupCall
from pytgcalls.types import (
    AudioQuality,
    ChatUpdate,
    MediaStream,
    StreamEnded,
    Update,
    VideoQuality,
)

from config import Config
from Music.helpers.buttons import Buttons
from Music.helpers.strings import TEXTS
from Music.utils.exceptions import (
    ChangeVCException,
    JoinGCException,
    JoinVCException,
    UserException,
)
from Music.utils.queue import Queue
from Music.utils.thumbnail import thumb
from Music.utils.youtube import ytube
from Music.utils import formatter

from .clients import hellbot
from .database import db
from .logger import LOGS


async def __clean__(chat_id: int, force: bool):
    if force:
        Queue.rm_queue(chat_id, 0)
    else:
        Queue.clear_queue(chat_id)
    await db.remove_active_vc(chat_id)


class HellMusic(PyTgCalls):
    def __init__(self):
        self.music = PyTgCalls(hellbot.user)
        self.audience = {}

    async def autoend(self, chat_id: int, users: list):
        autoend = await db.get_autoend()
        if autoend:
            if len(users) == 1:
                get = await hellbot.app.get_entity(users[0])
                if get.id == hellbot.user.id:
                    db.inactive[chat_id] = datetime.datetime.now() + datetime.timedelta(
                        minutes=5
                    )
            else:
                db.inactive[chat_id] = {}

    async def autoclean(self, file: str):
        # dirty way. but works :)
        try:
            os.remove(file)
            os.remove(f"downloads/{file}.webm")
            os.remove(f"downloads/{file}.mp4")
        except:
            pass

    async def start(self):
        LOGS.info(">> Booting PyTgCalls Client...")
        if Config.STRING_SESSION:
            await self.music.start()
            LOGS.info(">> Booted PyTgCalls Client!")
        else:
            LOGS.error(">> PyTgCalls Client not booted!")
            quit(1)

    async def ping(self):
        # In PyTgCalls 2.2.8, ping is a property not a method
        pinged = self.music.ping
        return pinged

    async def vc_participants(self, chat_id: int):
        # In PyTgCalls 2.2.8, we need to get active call first
        try:
            call = await self.music.get_call(chat_id)
            if call:
                return call.participants if hasattr(call, 'participants') else []
            return []
        except:
            return []

    async def mute_vc(self, chat_id: int):
        await self.music.mute(chat_id)

    async def unmute_vc(self, chat_id: int):
        await self.music.unmute(chat_id)

    async def pause_vc(self, chat_id: int):
        await self.music.pause(chat_id)

    async def resume_vc(self, chat_id: int):
        await self.music.resume(chat_id)

    async def leave_vc(self, chat_id: int, force: bool = False):
        try:
            await __clean__(chat_id, force)
            await self.music.leave_call(chat_id)
        except:
            pass
        previous = Config.PLAYER_CACHE.get(chat_id)
        if previous:
            try:
                await previous.delete()
            except:
                pass

    def get_ffmpeg_parameters(self, bass_boost: int = 0, speed: float = 1.0, seek: str = None, duration: str = None):
        """
        Generate FFmpeg parameters for audio effects
        bass_boost: 0-10 (0 = no boost, 10 = maximum boost)
        speed: 0.5-2.0 (0.5 = half speed, 2.0 = double speed)
        """
        filters = []
        
        # Bass boost filter
        if bass_boost > 0:
            # Bass boost using equalizer
            bass_value = bass_boost * 2  # Scale 0-10 to 0-20 dB
            filters.append(f"equalizer=f=100:width_type=h:width=200:g={bass_value}")
        
        # Speed filter
        if speed != 1.0:
            # atempo filter (range: 0.5 to 2.0)
            if 0.5 <= speed <= 2.0:
                filters.append(f"atempo={speed}")
        
        # Combine all filters
        filter_string = ",".join(filters) if filters else None
        
        # Build ffmpeg parameters
        params = []
        if seek:
            params.append(f"-ss {seek}")
        if duration:
            params.append(f"-to {duration}")
        if filter_string:
            params.append(f"-af {filter_string}")
        
        return " ".join(params) if params else None

    async def apply_effects(self, chat_id: int, bass_boost: int = 0, speed: float = 1.0):
        """Apply bass boost and speed effects to current stream"""
        que = Queue.get_queue(chat_id)
        if not que or que == []:
            return False
        
        current = que[0]
        video = True if current["vc_type"] == "video" else False
        
        # Get file path
        if current["video_id"] == "telegram":
            file_path = current["file"]
        else:
            try:
                file_path = await ytube.download(current["video_id"], True, video)
            except Exception as e:
                LOGS.error(f"Error downloading for effects: {e}")
                return False
        
        # Get current playback position to maintain continuity
        played = int(current.get("played", 0))
        duration = current.get("duration", "0:00")
        
        # Get FFmpeg parameters with effects and seek to current position
        if played > 0:
            seek_time = formatter.secs_to_mins(played)
            ffmpeg_params = self.get_ffmpeg_parameters(bass_boost, speed, seek_time, duration)
        else:
            ffmpeg_params = self.get_ffmpeg_parameters(bass_boost, speed)
        
        # Create MediaStream with effects
        if video:
            stream = MediaStream(
                file_path,
                audio_parameters=AudioQuality.MEDIUM,
                video_parameters=VideoQuality.SD_480p,
                ffmpeg_parameters=ffmpeg_params,
            )
        else:
            stream = MediaStream(
                file_path,
                audio_parameters=AudioQuality.MEDIUM,
                ffmpeg_parameters=ffmpeg_params,
            )
        
        try:
            await self.music.play(chat_id, stream)
            # Store current effects in database
            await db.set_audio_effects(chat_id, bass_boost, speed)
            return True
        except Exception as e:
            LOGS.error(f"Error applying effects: {e}")
            return False

    @hellmusic.music.on_update()
    async def on_update(self, update: Update):
        """Handle PyTgCalls updates"""
        if isinstance(update, ChatUpdate):
            chat_id = update.chat_id
            
            # Handle stream ended
            if isinstance(update, StreamEnded):
                await self.change_vc(chat_id)

    async def change_vc(self, chat_id: int):
        """Change to next song in queue or leave VC if no songs"""
        try:
            # Process queue - remove played song or decrease loop count
            que = Queue.get_queue(chat_id)
            if not que or que == []:
                LOGS.info(f"Queue is empty for chat {chat_id}, leaving VC")
                return await self.leave_vc(chat_id)
            
            loop = await db.get_loop(chat_id)
            if loop == 0:
                file = Queue.rm_queue(chat_id, 0)
                await self.autoclean(file)
            else:
                await db.set_loop(chat_id, loop - 1)
        except Exception as e:
            LOGS.error(f"Error in change_vc processing queue: {e}")
            return await self.leave_vc(chat_id)
        
        # Check queue again after processing
        get = Queue.get_queue(chat_id)
        if get == []:
            LOGS.info(f"No more songs in queue for chat {chat_id}, leaving VC")
            return await self.leave_vc(chat_id)
        
        # Get next song details
        chat_id = get[0]["chat_id"]
        duration = get[0]["duration"]
        queue = get[0]["file"]
        title = get[0]["title"]
        user_id = get[0]["user_id"]
        vc_type = get[0]["vc_type"]
        video_id = get[0]["video_id"]
        
        try:
            user = await hellbot.app.get_entity(user_id)
            user_mention = f"[{user.first_name}](tg://user?id={user.id})"
        except:
            user_mention = get[0]["user"]
        
        if queue:
            tg = True if video_id == "telegram" else False
            if tg:
                to_stream = queue
            else:
                try:
                    to_stream = await ytube.download(
                        video_id, True, True if vc_type == "video" else False
                    )
                except Exception as e:
                    LOGS.error(f"Error downloading next song: {e}")
                    # Try next song in queue
                    Queue.rm_queue(chat_id, 0)
                    return await self.change_vc(chat_id)
            
            # Don't apply effects automatically on song change
            # User can reapply effects if they want them
            
            # Create MediaStream for PyTgCalls 2.2.8 (no effects initially)
            if vc_type == "video":
                stream = MediaStream(
                    to_stream,
                    audio_parameters=AudioQuality.MEDIUM,
                    video_parameters=VideoQuality.SD_480p,
                )
            else:
                stream = MediaStream(
                    to_stream,
                    audio_parameters=AudioQuality.MEDIUM,
                )
            
            try:
                photo = thumb.generate((359), (297, 302), video_id)
                # In PyTgCalls 2.2.8+, use play() to change stream
                await self.music.play(int(chat_id), stream)
                
                btns = Buttons.player_markup(
                    chat_id,
                    "None" if video_id == "telegram" else video_id,
                    hellbot.app.me.username,
                )
                
                if photo:
                    sent = await hellbot.app.send_file(
                        int(chat_id),
                        photo,
                        caption=TEXTS.PLAYING.format(
                            f"@{hellbot.app.me.username}",
                            title,
                            duration,
                            user_mention,
                        ),
                        buttons=btns,
                    )
                    os.remove(photo)
                else:
                    sent = await hellbot.app.send_message(
                        int(chat_id),
                        TEXTS.PLAYING.format(
                            f"@{hellbot.app.me.username}",
                            title,
                            duration,
                            user_mention,
                        ),
                        link_preview=False,
                        buttons=btns,
                    )
                
                previous = Config.PLAYER_CACHE.get(chat_id)
                if previous:
                    try:
                        await previous.delete()
                    except:
                        pass
                
                Config.PLAYER_CACHE[chat_id] = sent
                await db.update_songs_count(1)
                await db.update_user(user_id, "songs_played", 1)
                chat = await hellbot.app.get_entity(chat_id)
                chat_name = chat.title if hasattr(chat, 'title') else 'Unknown'
                await hellbot.logit(
                    f"play {vc_type}",
                    f"**⤷ Song:** `{title}` \n**⤷ Chat:** {chat_name} [`{chat_id}`] \n**⤷ User:** {user_mention}",
                )
            except Exception as e:
                LOGS.error(f"Error in change_vc streaming: {e}")
                raise ChangeVCException(f"[ChangeVCException]: {e}")

    async def join_vc(self, chat_id: int, file_path: str, video: bool = False):
        # Don't apply effects on initial join - let stream start normally
        # User can apply effects after song starts playing
        
        # Create MediaStream for PyTgCalls 2.2.8 (no effects initially)
        if video:
            stream = MediaStream(
                file_path,
                audio_parameters=AudioQuality.MEDIUM,
                video_parameters=VideoQuality.SD_480p,
            )
        else:
            stream = MediaStream(
                file_path,
                audio_parameters=AudioQuality.MEDIUM,
            )

        # Join VC using PyTgCalls 2.2.8 method
        try:
            await self.music.play(chat_id, stream)
        except NoActiveGroupCall:
            try:
                await self.join_gc(chat_id)
            except Exception as e:
                await self.leave_vc(chat_id)
                raise JoinGCException(e)
            try:
                await self.music.play(chat_id, stream)
            except Exception as e:
                await self.leave_vc(chat_id)
                raise JoinVCException(f"[JoinVCException]: {e}")
        except TelegramServerError as e:
            if "GROUPCALL_ALREADY_STARTED" in str(e) or "already" in str(e).lower():
                raise UserException(
                    f"[UserException]: Already joined in the voice chat. If this is a mistake then try to restart the voice chat."
                )
            raise UserException(f"[UserException]: {e}")
        except Exception as e:
            raise UserException(f"[UserException]: {e}")

        await db.add_active_vc(chat_id, "video" if video else "voice")
        self.audience[chat_id] = {}
        users = await self.vc_participants(chat_id)
        user_ids = [user.user_id for user in users] if users else []
        await self.autoend(chat_id, user_ids)
        
        # Initialize audio effects to default
        await db.set_audio_effects(chat_id, 0, 1.0)

    async def join_gc(self, chat_id: int):
        try:
            try:
                # Get participant info using Telethon
                participant = await hellbot.app.get_permissions(chat_id, hellbot.user.id)
            except ChatAdminRequiredError:
                raise UserException(
                    f"[UserException]: Bot is not admin in chat {chat_id}"
                )
            
            # Check if user is restricted or banned
            if participant.is_banned:
                raise UserException(
                    f"[UserException]: Assistant is restricted or banned in chat {chat_id}"
                )
        except UserNotParticipantError:
            chat = await hellbot.app.get_entity(chat_id)
            
            # Check if chat has username (public group/channel)
            if hasattr(chat, 'username') and chat.username:
                try:
                    await hellbot.user(JoinChannelRequest(chat.username))
                except UserAlreadyParticipantError:
                    pass
                except Exception as e:
                    raise UserException(f"[UserException]: {e}")
            else:
                # Private group - need invite link
                try:
                    try:
                        # Get full chat info to access invite link
                        full_chat = await hellbot.app(GetFullChatRequest(chat_id))
                        link = full_chat.full_chat.exported_invite.link if full_chat.full_chat.exported_invite else None
                        
                        if link is None:
                            # Export new invite link
                            link = await hellbot.app(ExportChatInviteRequest(chat_id))
                            link = link.link
                    except ChatAdminRequiredError:
                        raise UserException(
                            f"[UserException]: Bot is not admin in chat {chat_id}"
                        )
                    except Exception as e:
                        raise UserException(f"[UserException]: {e}")
                    
                    hell = await hellbot.app.send_message(
                        chat_id, "Inviting assistant to chat..."
                    )
                    
                    # Join using invite link
                    if link.startswith("https://t.me/+"):
                        link = link.replace("https://t.me/+", "https://t.me/joinchat/")
                    
                    await hellbot.user(ImportChatInviteRequest(link.split('/')[-1]))
                    await hell.edit("Assistant joined the chat! Enjoy your music!")
                except UserAlreadyParticipantError:
                    pass
                except Exception as e:
                    raise UserException(f"[UserException]: {e}")


hellmusic = HellMusic()

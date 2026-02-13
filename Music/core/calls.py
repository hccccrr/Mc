import asyncio
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
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ExportChatInviteRequest, ImportChatInviteRequest
from telethon.tl.functions.messages import GetFullChatRequest
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
from Music.helpers.formatters import formatter
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
        pinged = self.music.ping
        return pinged

    async def vc_participants(self, chat_id: int):
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

    def get_ffmpeg_parameters(self, bass_boost: int = 0, speed: float = 1.0, seek: str = None):
        """
        Generate FFmpeg parameters for audio effects
        bass_boost: 0-10 (0 = no boost, 10 = maximum boost)
        speed: 0.5-2.0 (0.5 = half speed, 2.0 = double speed)
        seek: timestamp in format "00:00:00"
        """
        filters = []
        
        # Bass boost filter - using bass and treble adjustment
        if bass_boost > 0:
            # Scale bass_boost (0-10) to gain values
            # Low frequencies (60-250 Hz) boost
            gain = bass_boost * 3  # 0-30 dB range
            filters.append(f"bass=g={gain}:f=110:w=0.3")
        
        # Speed/tempo filter
        if speed != 1.0:
            if 0.5 <= speed <= 2.0:
                filters.append(f"atempo={speed}")
            elif speed < 0.5:
                # For very slow speeds, chain atempo filters
                filters.append("atempo=0.5,atempo=" + str(speed/0.5))
            elif speed > 2.0:
                # For very fast speeds, chain atempo filters  
                filters.append("atempo=2.0,atempo=" + str(speed/2.0))
        
        # Build parameters
        params = []
        
        # Add seek if provided
        if seek:
            params.extend(["-ss", seek])
        
        # Add audio filters if any
        if filters:
            filter_string = ",".join(filters)
            params.extend(["-af", filter_string])
        
        return params if params else None

    async def apply_effects(self, chat_id: int, bass_boost: int = 0, speed: float = 1.0):
        """Apply bass boost and speed effects with advanced processing"""
        try:
            que = Queue.get_queue(chat_id)
            if not que or que == []:
                return False
            
            current = que[0]
            is_video = current["vc_type"] == "video"
            
            # Get file path
            if current["video_id"] == "telegram":
                file_path = current["file"]
            else:
                try:
                    file_path = await ytube.download(current["video_id"], True, is_video)
                except Exception as e:
                    LOGS.error(f"Error downloading for effects: {e}")
                    return False
            
            # Build FFmpeg filter strings
            audio_filters = []
            video_filter = None
            
            # Bass boost filter
            if bass_boost > 0:
                gain = bass_boost * 3  # Scale 0-10 to 0-30 dB
                audio_filters.append(f"bass=g={gain}:f=110:w=0.3")
            
            # Speed/tempo filter for audio
            if speed != 1.0:
                if 0.5 <= speed <= 2.0:
                    audio_filters.append(f"atempo={speed}")
                elif speed < 0.5:
                    audio_filters.append(f"atempo=0.5,atempo={speed/0.5}")
                elif speed > 2.0:
                    audio_filters.append(f"atempo=2.0,atempo={speed/2.0}")
            
            # Video speed filter (if video and speed changed)
            if is_video and speed != 1.0:
                if speed == 0.5:
                    vs = 2.0
                elif speed == 0.75:
                    vs = 1.35
                elif speed == 1.5:
                    vs = 0.68
                elif speed == 2.0:
                    vs = 0.5
                else:
                    vs = 1.0 / speed
                video_filter = f"setpts={vs}*PTS"
            
            # Determine if we need pre-processing (video with speed change)
            needs_processing = (is_video and speed != 1.0)
            
            if needs_processing:
                # Pre-process video with speed change
                base = os.path.basename(file_path)
                effect_name = f"bass{bass_boost}_speed{str(speed).replace('.', '_')}"
                chatdir = os.path.join(os.getcwd(), "playback", effect_name)
                
                if not os.path.isdir(chatdir):
                    os.makedirs(chatdir)
                
                output_file = os.path.join(chatdir, base)
                
                if not os.path.isfile(output_file):
                    # Build FFmpeg command
                    cmd_parts = ["ffmpeg", "-i", file_path]
                    
                    if video_filter:
                        cmd_parts.extend(["-filter:v", video_filter])
                    
                    if audio_filters:
                        audio_filter_str = ",".join(audio_filters)
                        cmd_parts.extend(["-filter:a", audio_filter_str])
                    
                    cmd_parts.append(output_file)
                    cmd = " ".join(cmd_parts)
                    
                    # Process file
                    proc = await asyncio.create_subprocess_shell(
                        cmd=cmd,
                        stdin=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    await proc.communicate()
                
                ffmpeg_params = None  # Already processed
                
                # Update queue with speed info
                if "old_dur" not in current:
                    current["old_dur"] = current.get("duration", "0:00")
                    current["old_second"] = formatter.mins_to_secs(current["old_dur"])
                
                old_seconds = current.get("old_second", 0)
                new_seconds = int(old_seconds / speed)
                new_duration = formatter.secs_to_mins(new_seconds)
                
                current["duration"] = new_duration
                current["seconds"] = new_seconds
                current["speed"] = speed
                current["speed_path"] = output_file
                
            else:
                # Use real-time FFmpeg parameters (no pre-processing)
                output_file = file_path
                
                # Build FFmpeg parameters
                params = []
                
                # Add seek if currently playing
                played = int(current.get("played", 0))
                if played > 0:
                    played_time = formatter.secs_to_mins(played)
                    params.extend(["-ss", played_time])
                
                # Add audio filters
                if audio_filters:
                    audio_filter_str = ",".join(audio_filters)
                    params.extend(["-af", audio_filter_str])
                
                ffmpeg_params = " ".join(params) if params else None
            
            # Create MediaStream
            if is_video:
                stream = MediaStream(
                    output_file,
                    audio_parameters=AudioQuality.MEDIUM,
                    video_parameters=VideoQuality.SD_480p,
                    ffmpeg_parameters=ffmpeg_params,
                )
            else:
                stream = MediaStream(
                    output_file,
                    audio_parameters=AudioQuality.MEDIUM,
                    ffmpeg_parameters=ffmpeg_params,
                )
            
            # Apply the stream with effects
            await self.music.play(chat_id, stream)
            
            # Store bass boost info
            if bass_boost > 0:
                current["bass_boost"] = bass_boost
            
            # Store current effects in database
            await db.set_audio_effects(chat_id, bass_boost, speed)
            
            return True
            
        except Exception as e:
            LOGS.error(f"Error applying effects: {e}")
            return False

    async def seek_vc(self, context: dict):
        """Seek to specific position in current track"""
        chat_id = context["chat_id"]
        file_path = context["file"]
        seek_time = context["seek"]
        video = context["video"]
        
        # Get current effects
        effects = await db.get_audio_effects(chat_id)
        bass = effects.get("bass_boost", 0) if effects else 0
        speed_val = effects.get("speed", 1.0) if effects else 1.0
        
        # Get FFmpeg parameters with seek and effects
        ffmpeg_params = self.get_ffmpeg_parameters(bass, speed_val, seek_time)
        
        # Create stream with seek position
        if video:
            stream = MediaStream(
                file_path,
                audio_parameters=AudioQuality.MEDIUM,
                video_parameters=VideoQuality.SD_480p,
                ffmpeg_parameters=" ".join(ffmpeg_params) if ffmpeg_params else None,
            )
        else:
            stream = MediaStream(
                file_path,
                audio_parameters=AudioQuality.MEDIUM,
                ffmpeg_parameters=" ".join(ffmpeg_params) if ffmpeg_params else None,
            )
        
        await self.music.play(chat_id, stream)

    async def replay_vc(self, chat_id: int, file_path: str, video: bool):
        """Replay current track from beginning"""
        # Get current effects
        effects = await db.get_audio_effects(chat_id)
        bass = effects.get("bass_boost", 0) if effects else 0
        speed_val = effects.get("speed", 1.0) if effects else 1.0
        
        # Get FFmpeg parameters with effects
        ffmpeg_params = self.get_ffmpeg_parameters(bass, speed_val)
        
        # Create stream
        if video:
            stream = MediaStream(
                file_path,
                audio_parameters=AudioQuality.MEDIUM,
                video_parameters=VideoQuality.SD_480p,
                ffmpeg_parameters=" ".join(ffmpeg_params) if ffmpeg_params else None,
            )
        else:
            stream = MediaStream(
                file_path,
                audio_parameters=AudioQuality.MEDIUM,
                ffmpeg_parameters=" ".join(ffmpeg_params) if ffmpeg_params else None,
            )
        
        await self.music.play(chat_id, stream)

    async def change_vc(self, chat_id: int):
        """Change to next song in queue"""
        is_loop = await db.get_loop(chat_id)
        
        if is_loop != 0:
            # Decrement loop counter
            await db.set_loop(chat_id, is_loop - 1)
        else:
            # Remove current song from queue
            Queue.rm_queue(chat_id, 0)
        
        get = Queue.get_queue(chat_id)
        
        if not get or get == []:
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
                    Queue.rm_queue(chat_id, 0)
                    return await self.change_vc(chat_id)
            
            # Create MediaStream WITHOUT effects initially
            # Effects will be reapplied when user requests
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
                await self.music.play(int(chat_id), stream)
                
                btns = Buttons.player_markup(
                    chat_id,
                    "None" if video_id == "telegram" else video_id,
                    hellbot.app.me.username,
                )
                
                if photo:
                    sent = await hellbot.app.send_message(
                        int(chat_id),
                        TEXTS.PLAYING.format(
                            f"@{hellbot.app.me.username}",
                            title,
                            duration,
                            user_mention,
                        ),
                        file=photo,
                        buttons=btns,
                    )
                    if os.path.exists(photo):
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
                
                # Reset effects to default on song change
                await db.set_audio_effects(chat_id, 0, 1.0)
                
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
        """Join voice chat and start streaming"""
        # Create MediaStream without effects initially
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

        # Join VC
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
        """Join group chat if not already joined"""
        try:
            try:
                participant = await hellbot.app.get_permissions(chat_id, hellbot.user.id)
            except ChatAdminRequiredError:
                raise UserException(
                    f"[UserException]: Bot is not admin in chat {chat_id}"
                )
            
            if participant.is_banned:
                raise UserException(
                    f"[UserException]: Assistant is restricted or banned in chat {chat_id}"
                )
        except UserNotParticipantError:
            chat = await hellbot.app.get_entity(chat_id)
            
            if hasattr(chat, 'username') and chat.username:
                try:
                    await hellbot.user(JoinChannelRequest(chat.username))
                except UserAlreadyParticipantError:
                    pass
                except Exception as e:
                    raise UserException(f"[UserException]: {e}")
            else:
                try:
                    try:
                        full_chat = await hellbot.app(GetFullChatRequest(chat_id))
                        link = full_chat.full_chat.exported_invite.link if full_chat.full_chat.exported_invite else None
                        
                        if link is None:
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
                    
                    if link.startswith("https://t.me/+"):
                        link = link.replace("https://t.me/+", "https://t.me/joinchat/")
                    
                    await hellbot.user(ImportChatInviteRequest(link.split('/')[-1]))
                    await hell.edit("Assistant joined the chat! Enjoy your music!")
                except UserAlreadyParticipantError:
                    pass
                except Exception as e:
                    raise UserException(f"[UserException]: {e}")


hellmusic = HellMusic()

from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsAdmins

from Music.core.clients import hellbot
from Music.core.database import db


async def get_admins(chat_id: int):
    """Get all admins in a chat"""
    admins = []
    try:
        # For channels/supergroups
        participants = await hellbot.app(GetParticipantsRequest(
            channel=chat_id,
            filter=ChannelParticipantsAdmins(),
            offset=0,
            limit=200,
            hash=0
        ))
        
        for user in participants.users:
            admins.append(user.id)
    except Exception as e:
        # For small groups, use get_participants
        try:
            async for user in hellbot.app.iter_participants(chat_id, filter=ChannelParticipantsAdmins):
                admins.append(user.id)
        except:
            pass
    
    return admins


async def get_auth_users(chat_id: int):
    """Get all authorized users (admins + custom auth users)"""
    auth_users = []
    
    # Get admins first
    try:
        participants = await hellbot.app(GetParticipantsRequest(
            channel=chat_id,
            filter=ChannelParticipantsAdmins(),
            offset=0,
            limit=200,
            hash=0
        ))
        
        for user in participants.users:
            auth_users.append(user.id)
    except Exception:
        try:
            async for user in hellbot.app.iter_participants(chat_id, filter=ChannelParticipantsAdmins):
                auth_users.append(user.id)
        except:
            pass
    
    # Get custom authorized users from database
    users = await db.get_all_authusers(chat_id)
    if users:
        auth_users.extend(users)
    
    return auth_users


async def get_user_rights(chat_id: int, user_id: int):
    """Check if user has manage voice chats permission"""
    try:
        # Get user's permissions in the chat
        participant = await hellbot.app.get_permissions(chat_id, user_id)
        
        # Check if user is admin
        if not participant.is_admin:
            return False
        
        # Check for manage_call permission (voice chat management)
        if hasattr(participant, 'manage_call') and participant.manage_call:
            return True
        
        # For older Telethon versions or if manage_call not available
        # Check for general admin rights
        if participant.is_admin:
            return True
            
        return False
    except Exception:
        return False


async def get_user_type(chat_id: int, user_id: int):
    """Get user type: admin, auth, or user"""
    admins = await get_admins(chat_id)
    auth_users = await get_auth_users(chat_id)
    
    if user_id in admins:
        return "admin"
    if user_id in auth_users:
        return "auth"
    return "user"

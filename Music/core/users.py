from config import Config

from .database import db
from .logger import LOGS


class UsersData:
    """User data management for HellMusic V3"""
    
    def __init__(self) -> None:
        # Developer IDs (HellBot Developers)
        self.DEVS = [
            8244881089,  # Vivan
            7616808278,  # Bad
        ]

    async def god_users(self):
        """Setup owner/god users"""
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("👑 Setting up owners...")
        
        if not hasattr(Config, 'GOD_USERS'):
            Config.GOD_USERS = set()
        
        if hasattr(Config, 'OWNER_ID') and Config.OWNER_ID:
            god_users = str(Config.OWNER_ID).split()
            
            for user in god_users:
                if user.isdigit():
                    Config.GOD_USERS.add(int(user))
                    LOGS.info(f"✅ Added owner: {user}")
        
        LOGS.info("✅ Owners setup complete!")

    async def sudo_users(self):
        """Setup sudo users"""
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("⭐ Setting up sudo users...")
        
        if not hasattr(Config, 'SUDO_USERS'):
            Config.SUDO_USERS = set()
        
        # Add developers
        for user_id in self.DEVS:
            Config.SUDO_USERS.add(user_id)
        
        # Get sudo users from database
        db_users = await db.get_sudo_users()
        
        # Add developers to database if not present
        for user_id in self.DEVS:
            if user_id not in db_users:
                await db.add_sudo(user_id)
                LOGS.info(f"✅ Added developer: {user_id}")
        
        # Add owners from config
        if hasattr(Config, 'OWNER_ID') and Config.OWNER_ID:
            god_users = str(Config.OWNER_ID).split()
            
            for user in god_users:
                if not user.isdigit():
                    continue
                
                user_id = int(user)
                Config.SUDO_USERS.add(user_id)
                
                if user_id not in db_users:
                    await db.add_sudo(user_id)
                    LOGS.info(f"✅ Added owner as sudo: {user_id}")
        
        # Add all database sudo users to config
        for user_id in db_users:
            Config.SUDO_USERS.add(user_id)
        
        LOGS.info(f"✅ Total sudo users: {len(Config.SUDO_USERS)}")

    async def banned_users(self):
        """Setup banned users"""
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("🚫 Setting up banned users...")
        
        if not hasattr(Config, 'BANNED_USERS'):
            Config.BANNED_USERS = set()
        
        # Get blocked users from database
        bl_users = await db.get_blocked_users()
        
        if bl_users:
            for user_id in bl_users:
                Config.BANNED_USERS.add(user_id)
        
        # Get globally banned users from database
        gb_users = await db.get_gbanned_users()
        
        if gb_users:
            for user_id in gb_users:
                Config.BANNED_USERS.add(user_id)
        
        LOGS.info(f"✅ Total banned users: {len(Config.BANNED_USERS)}")

    async def setup(self):
        """Setup all user data"""
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("👥 Initializing user data...")
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        await self.god_users()
        await self.sudo_users()
        await self.banned_users()
        
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        LOGS.info("✅ User data initialized successfully!")
        LOGS.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


# Global user data instance
user_data = UsersData()

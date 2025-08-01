"""
Admin-related command handlers for Telegram bot.
"""
import os
from typing import Dict, Any, List

from aws_lambda_powertools import Logger
from src.utils.telegram import TelegramClient
from src.utils.auth import Authorization

logger = Logger()

# Initialize shared clients (lazy loading)
_telegram = None
_auth = None

def get_telegram():
    """Get or create Telegram client."""
    global _telegram
    if _telegram is None:
        _telegram = TelegramClient()
    return _telegram

def get_auth():
    """Get or create Authorization instance."""
    global _auth
    if _auth is None:
        _auth = Authorization()
    return _auth

def is_admin(user_id: str) -> bool:
    """
    Check if user is an admin.
    
    Args:
        user_id: Telegram user ID to check
        
    Returns:
        bool: True if user is an admin
    """
    admin_ids = os.environ.get("ADMIN_USER_IDS", "").split(",")
    return user_id in admin_ids

def handle_allow_command(user_id: str, chat_id: str, args: List[str]) -> Dict[str, Any]:
    """Handle /allow command for admins."""
    telegram, auth = get_telegram(), get_auth()
    
    if not args:
        return telegram.send_message(
            chat_id=chat_id,
            text=(
                "Usage: /allow <user_id>\n\n"
                "Example:\n"
                "/allow 123456"
            )
        )
    
    target_id = args[0]
    
    # Try to send welcome message to new user first
    try:
        telegram.bot.send_message(
            chat_id=target_id,
            text=(
                "Welcome to Family Forest! 🌳\n\n"
                "You've been granted access to use this bot.\n"
                "Use /start to begin your family tree journey!"
            )
        )
    except Exception as e:
        logger.warning(
            "Failed to send welcome message to new user",
            extra={"error": str(e), "target_id": target_id}
        )
    
    auth.add_allowed_user(target_id, user_id)
    
    logger.info("Added user to allowlist", extra={
        "admin_id": user_id,
        "target_id": target_id,
        "action": "allow",
        "command": "/allow"
    })
    
    return telegram.send_message(
        chat_id=chat_id,
        text=f"✅ Added user {target_id} to Family Forest\nA welcome message has been sent to the user."
    )

def handle_revoke_command(user_id: str, chat_id: str, args: List[str]) -> Dict[str, Any]:
    """Handle /revoke command for admins."""
    telegram, auth = get_telegram(), get_auth()
    
    if not args:
        return telegram.send_message(
            chat_id=chat_id,
            text=(
                "Usage: /revoke <user_id>\n\n"
                "Example:\n"
                "/revoke 123456"
            )
        )
        
    target_id = args[0]
    
    # Try to notify user about access revocation
    try:
        telegram.bot.send_message(
            chat_id=target_id,
            text=(
                "Your access to Family Forest has been revoked.\n\n"
                "Please contact an administrator if you believe this is a mistake."
            )
        )
    except Exception as e:
        logger.warning(
            "Failed to send revocation message to user",
            extra={"error": str(e), "target_id": target_id}
        )
    
    auth.remove_user(target_id)
    
    logger.info("Removed from allowlist", extra={
        "admin_id": user_id,
        "target_id": target_id,
        "action": "revoke",
        "command": "/revoke"
    })
    
    return telegram.send_message(
        chat_id=chat_id,
        text=f"✅ Removed user {target_id} from Family Forest\nThe user has been notified of the access revocation."
    )

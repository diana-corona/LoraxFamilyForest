"""
Handler for the /help command.
"""
from telegram import Update
from telegram.ext import ContextTypes
from aws_lambda_powertools import Logger

from src.utils.auth import Authorization

logger = Logger()
auth = Authorization()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    user_id = str(update.effective_user.id)
    
    try:
        if not auth.check_user_authorized(user_id):
            logger.warning("Unauthorized help access attempt", extra={"user_id": user_id})
            return  # Silent fail for unauthorized users
            
        await update.message.reply_text(
            "Family Forest Help 🌳\n\n"
            "Available Commands:\n"
            "/new_tree - Create a new family tree\n"
            "/add_member - Add a family member\n"
            "/view_tree - View your family tree\n"
            "/help - Show this help message\n\n"
            "For more assistance, contact support."
        )
    except Exception as e:
        logger.exception("Error handling help command")

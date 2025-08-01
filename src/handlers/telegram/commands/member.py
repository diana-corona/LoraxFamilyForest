"""
Handlers for member-related commands.
"""
from telegram import Update
from telegram.ext import ContextTypes
from aws_lambda_powertools import Logger

from src.utils.auth import Authorization
from src.services.tree_service import TreeService

logger = Logger()
auth = Authorization()
tree_service = TreeService()

async def add_member_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /add_member command."""
    user_id = str(update.effective_user.id)
    
    try:
        if not auth.check_user_authorized(user_id):
            logger.warning("Unauthorized member addition attempt", extra={"user_id": user_id})
            return  # Silent fail for unauthorized users
            
        # TODO: Implement member addition flow using conversation handlers
        # For now, just show instructions
        await update.message.reply_text(
            "To add a family member, please provide:\n"
            "1. Member's name\n"
            "2. Birth date (optional)\n"
            "3. Relationship to you\n\n"
            "Example: /add_member John Smith, 1980-01-01, father"
        )
    except Exception as e:
        logger.exception("Error handling add member command")

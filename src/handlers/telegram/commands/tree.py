"""
Handlers for tree-related commands.
"""
from telegram import Update
from telegram.ext import ContextTypes
from aws_lambda_powertools import Logger

from src.utils.auth import Authorization
from src.services.tree_service import TreeService

logger = Logger()
auth = Authorization()
tree_service = TreeService()

async def new_tree_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /new_tree command."""
    user_id = str(update.effective_user.id)
    
    try:
        if not auth.check_user_authorized(user_id):
            logger.warning("Unauthorized tree creation attempt", extra={"user_id": user_id})
            return  # Silent fail for unauthorized users
            
        # Extract tree name from command
        args = context.args
        if not args:
            await update.message.reply_text(
                "Please provide a name for your family tree:\n"
                "/new_tree My Family Tree"
            )
            return
            
        tree_name = " ".join(args)
        tree = tree_service.create_tree(user_id, tree_name)
        
        await update.message.reply_text(
            f"Created new family tree: {tree_name}\n"
            "Use /add_member to start adding family members!"
        )
    except Exception as e:
        logger.exception("Error creating tree")

async def view_tree_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /view_tree command."""
    user_id = str(update.effective_user.id)
    
    try:
        if not auth.check_user_authorized(user_id):
            logger.warning("Unauthorized tree access attempt", extra={"user_id": user_id})
            return  # Silent fail for unauthorized users
            
        # Will implement tree visualization
        await update.message.reply_text(
            "Family tree visualization coming soon!"
        )
    except Exception as e:
        logger.exception("Error handling view tree command")

"""
Main Telegram bot webhook handler.
"""
import os
import json
from typing import Dict, Any

from aws_lambda_powertools import Logger
from telegram import Update
from telegram.ext import Application, CommandHandler

from src.utils.auth import Authorization
from src.handlers.telegram.admin import is_admin, handle_allow_command, handle_revoke_command
from src.handlers.telegram.commands.start import start_command
from src.handlers.telegram.commands.help import help_command
from src.handlers.telegram.commands.tree import new_tree_command, view_tree_command
from src.handlers.telegram.commands.member import add_member_command

logger = Logger()
auth = Authorization()

def create_application() -> Application:
    """Create and configure the bot application."""
    application = Application.builder().token(
        os.environ["TELEGRAM_BOT_TOKEN"]
    ).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("new_tree", new_tree_command))
    application.add_handler(CommandHandler("view_tree", view_tree_command))
    application.add_handler(CommandHandler("add_member", add_member_command))
    
    return application

def parse_command(text: str):
    """Parse command and args from message text."""
    parts = text.split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    return command, args

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for Telegram webhook.
    
    Args:
        event: Lambda event containing webhook data
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    try:
        if "body" not in event:
            return {
                "statusCode": 200,  # Return 200 even for errors to avoid exposing bot existence
                "body": json.dumps({"ok": True})
            }
            
        body = (
            json.loads(event["body"])
            if isinstance(event["body"], str)
            else event["body"]
        )
        
        # Extract message details for admin command checks
        if "message" in body:
            message = body["message"]
            user_id = str(message["from"]["id"])
            chat_id = str(message["chat"]["id"])
            text = message.get("text", "")
            
            # Handle admin commands before regular processing
            if text:
                command, args = parse_command(text)
                if command in ["/allow", "/revoke"]:
                    if is_admin(user_id):
                        if command == "/allow":
                            return handle_allow_command(user_id, chat_id, args)
                        else:
                            return handle_revoke_command(user_id, chat_id, args)
                    else:
                        logger.warning(f"Unauthorized admin command attempt: {user_id}")
                        return {
                            "statusCode": 200,
                            "body": json.dumps({"ok": True})
                        }
            
            # Check authorization for non-admin commands
            if not auth.check_user_authorized(user_id):
                logger.warning("Unauthorized access attempt", extra={"user_id": user_id})
                return {
                    "statusCode": 200,
                    "body": json.dumps({"ok": True})
                }
        
        application = create_application()
        update = Update.de_json(body, application.bot)
        
        # Process update asynchronously using event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Initialize application before processing updates
        loop.run_until_complete(application.initialize())
        loop.run_until_complete(application.process_update(update))
        loop.close()
        
        return {
            "statusCode": 200,
            "body": json.dumps({"ok": True})
        }
        
    except Exception as e:
        logger.exception("Error processing webhook")
        return {
            "statusCode": 200,  # Always return 200 to avoid exposing bot existence
            "body": json.dumps({"ok": True})
        }

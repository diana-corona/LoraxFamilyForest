"""
Telegram bot utilities.
"""
from typing import Dict, Any, Optional, List
import os
import json

from telegram import Bot

class TelegramClient:
    """Client for sending Telegram messages."""
    
    def __init__(self):
        """Initialize Telegram client."""
        self._bot = None
        
    @property
    def bot(self) -> Bot:
        """Get or create Telegram bot instance."""
        if self._bot is None:
            self._bot = Bot(os.environ["TELEGRAM_BOT_TOKEN"])
        return self._bot
    
    def send_message(
        self, 
        chat_id: str, 
        text: str
    ) -> Dict[str, Any]:
        """
        Send message to Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            
        Returns:
            API Gateway Lambda proxy response
        """
        import asyncio
        
        # Run the async operation in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        ))
        loop.close()
            
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"ok": True})
        }
        
def parse_command(text: str) -> tuple[str, List[str]]:
    """
    Parse command and args from message text.
    
    Args:
        text: Message text
        
    Returns:
        Tuple of (command, args list)
    """
    parts = text.split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    return command, args

def format_error_message(error: Exception) -> str:
    """
    Format error message for user display.
    
    Args:
        error: Exception to format
        
    Returns:
        Formatted error message
    """
    return (
        "Sorry, an error occurred while processing your request.\n\n"
        f"Error: {str(error)}"
    )

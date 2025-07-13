"""
Telegram client service for Ethiopian Medical Business Data Platform.
Handles authentication and provides methods for scraping channels and downloading media.
"""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import time

from telethon import TelegramClient, events
from telethon.tl.types import Message, MessageMediaPhoto, MessageMediaDocument
from telethon.errors import FloodWaitError, ChannelPrivateError, ChatAdminRequiredError
from telethon.sessions import StringSession

from config import settings
from app.utils.logging.logger import telegram_logger, scraping_metrics


class TelegramClientService:
    """Service for interacting with Telegram API."""
    
    def __init__(self):
        self.api_id = settings.telegram.api_id
        self.api_hash = settings.telegram.api_hash
        self.bot_token = settings.telegram.bot_token
        self.client = None
        self.session_file = Path(settings.storage.data_dir) / "telegram_session.txt"
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Connect to Telegram API."""
        try:
            # Load existing session if available
            session_string = None
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    session_string = f.read().strip()
            
            self.client = TelegramClient(
                StringSession(session_string),
                self.api_id,
                self.api_hash
            )
            
            await self.client.start(bot_token=self.bot_token)
            
            # Save session for future use
            session_string = self.client.session.save()
            with open(self.session_file, 'w') as f:
                f.write(session_string)
            
            telegram_logger.log_scraping_start("telegram_client", "connection")
            print(f"✅ Connected to Telegram API as {await self.client.get_me()}")
            
        except Exception as e:
            telegram_logger.log_scraping_error("telegram_client", e, "connection")
            raise
    
    async def disconnect(self):
        """Disconnect from Telegram API."""
        if self.client:
            await self.client.disconnect()
            telegram_logger.log_scraping_start("telegram_client", "disconnection")
    
    async def get_channel_info(self, channel_username: str) -> Optional[Dict[str, Any]]:
        """Get information about a Telegram channel."""
        try:
            entity = await self.client.get_entity(channel_username)
            return {
                "id": entity.id,
                "title": getattr(entity, 'title', None),
                "username": getattr(entity, 'username', None),
                "participants_count": getattr(entity, 'participants_count', None),
                "description": getattr(entity, 'about', None),
                "created_at": getattr(entity, 'date', None),
                "verified": getattr(entity, 'verified', False),
                "scam": getattr(entity, 'scam', False),
                "fake": getattr(entity, 'fake', False)
            }
        except Exception as e:
            telegram_logger.log_scraping_error(channel_username, e, "get_channel_info")
            return None
    
    async def scrape_messages(
        self, 
        channel_username: str, 
        limit: int = 1000,
        offset_date: Optional[datetime] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Scrape messages from a Telegram channel.
        
        Args:
            channel_username: Username of the channel (without @)
            limit: Maximum number of messages to scrape
            offset_date: Start scraping from this date (for incremental scraping)
        """
        try:
            telegram_logger.log_scraping_start(channel_username, "message_scraping")
            
            entity = await self.client.get_entity(channel_username)
            message_count = 0
            image_count = 0
            
            async for message in self.client.iter_messages(
                entity,
                limit=limit,
                offset_date=offset_date,
                reverse=True  # Get oldest messages first
            ):
                if message is None:
                    continue
                
                message_data = await self._process_message(message, channel_username)
                if message_data:
                    message_count += 1
                    if message_data.get("has_image"):
                        image_count += 1
                    
                    yield message_data
                
                # Rate limiting - small delay between messages
                await asyncio.sleep(0.1)
            
            telegram_logger.log_scraping_success(channel_username, message_count, image_count)
            scraping_metrics.update_channel_metrics(channel_username, message_count, image_count)
            
        except FloodWaitError as e:
            telegram_logger.log_rate_limit(channel_username, e.seconds)
            await asyncio.sleep(e.seconds)
            # Retry the operation
            async for message_data in self.scrape_messages(channel_username, limit, offset_date):
                yield message_data
                
        except (ChannelPrivateError, ChatAdminRequiredError) as e:
            telegram_logger.log_scraping_error(channel_username, e, "access_denied")
            raise
            
        except Exception as e:
            telegram_logger.log_scraping_error(channel_username, e, "message_scraping")
            raise
    
    async def _process_message(self, message: Message, channel_username: str) -> Optional[Dict[str, Any]]:
        """Process a single Telegram message and extract relevant data."""
        try:
            # Basic message data
            message_data = {
                "message_id": message.id,
                "channel_username": channel_username,
                "date": message.date.isoformat() if message.date else None,
                "text": message.text if message.text else "",
                "has_image": False,
                "has_document": False,
                "image_paths": [],
                "document_paths": [],
                "forward_from": None,
                "reply_to": message.reply_to.reply_to_msg_id if message.reply_to else None,
                "views": getattr(message, 'views', None),
                "forwards": getattr(message, 'forwards', None),
                "reactions": [],
                "entities": [],
                "scraped_at": datetime.now().isoformat()
            }
            
            # Extract entities (mentions, hashtags, links, etc.)
            if message.entities:
                for entity in message.entities:
                    entity_data = {
                        "type": type(entity).__name__,
                        "offset": entity.offset,
                        "length": entity.length
                    }
                    if hasattr(entity, 'url'):
                        entity_data["url"] = entity.url
                    message_data["entities"].append(entity_data)
            
            # Extract reactions
            if hasattr(message, 'reactions') and message.reactions:
                for reaction in message.reactions.results:
                    reaction_data = {
                        "emoji": reaction.reaction.emoji if hasattr(reaction.reaction, 'emoji') else None,
                        "count": reaction.count
                    }
                    message_data["reactions"].append(reaction_data)
            
            # Handle media (images and documents)
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    message_data["has_image"] = True
                    image_path = await self._download_media(message, channel_username, "image")
                    if image_path:
                        message_data["image_paths"].append(image_path)
                
                elif isinstance(message.media, MessageMediaDocument):
                    message_data["has_document"] = True
                    doc_path = await self._download_media(message, channel_username, "document")
                    if doc_path:
                        message_data["document_paths"].append(doc_path)
            
            # Handle forwarded messages
            if message.forward:
                message_data["forward_from"] = {
                    "chat_id": message.forward.chat_id if message.forward.chat_id else None,
                    "user_id": message.forward.user_id if message.forward.user_id else None,
                    "date": message.forward.date.isoformat() if message.forward.date else None
                }
            
            return message_data
            
        except Exception as e:
            telegram_logger.log_scraping_error(channel_username, e, "message_processing")
            return None
    
    async def _download_media(
        self, 
        message: Message, 
        channel_username: str, 
        media_type: str
    ) -> Optional[str]:
        """Download media from a message."""
        try:
            # Create directory structure
            date_str = message.date.strftime("%Y-%m-%d") if message.date else datetime.now().strftime("%Y-%m-%d")
            media_dir = Path(settings.storage.data_dir) / "raw" / f"telegram_{media_type}s" / date_str / channel_username
            media_dir.mkdir(parents=True, exist_ok=True)
            
            # Download the media
            file_path = await self.client.download_media(
                message.media,
                file=str(media_dir / f"{message.id}_{media_type}")
            )
            
            if file_path:
                telegram_logger.log_image_download(channel_username, str(message.id), True, file_path)
                return str(file_path)
            else:
                telegram_logger.log_image_download(channel_username, str(message.id), False)
                return None
                
        except Exception as e:
            telegram_logger.log_scraping_error(channel_username, e, "media_download")
            return None
    
    async def get_channel_messages_count(self, channel_username: str) -> int:
        """Get the total number of messages in a channel."""
        try:
            entity = await self.client.get_entity(channel_username)
            return await self.client.get_messages(entity, limit=0)
        except Exception as e:
            telegram_logger.log_scraping_error(channel_username, e, "get_message_count")
            return 0


# Convenience function for creating client
async def create_telegram_client() -> TelegramClientService:
    """Create and return a Telegram client service."""
    return TelegramClientService()


if __name__ == "__main__":
    # Test the client
    async def test_client():
        async with TelegramClientService() as client:
            # Test with a public channel
            channel_info = await client.get_channel_info("telegram")
            print(f"Channel info: {channel_info}")
            
            # Test message scraping (limit to 5 messages)
            async for message in client.scrape_messages("telegram", limit=5):
                print(f"Message: {message['message_id']} - {message['text'][:100]}...")
    
    asyncio.run(test_client()) 
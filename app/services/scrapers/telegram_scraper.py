"""
Telegram scraper service for Ethiopian Medical Business Data Platform.
Orchestrates scraping of medical business channels and saves data to the data lake.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import time

from app.services.telegram.client import TelegramClientService
from app.utils.logging.logger import telegram_logger, scraping_metrics
from config import settings


class TelegramScraper:
    """Main scraper for Telegram medical business channels."""
    
    def __init__(self):
        self.channels = [
            "chemed",  # Chemed Telegram Channel
            "lobelia4cosmetics",  # Lobelia4cosmetics
            "tikvahpharma"  # Tikvah Pharma
        ]
        
        # Data lake structure
        self.data_dir = Path(settings.storage.data_dir)
        self.raw_messages_dir = self.data_dir / "raw" / "telegram_messages"
        self.raw_images_dir = self.data_dir / "raw" / "telegram_images"
        
        # Create directories
        self.raw_messages_dir.mkdir(parents=True, exist_ok=True)
        self.raw_images_dir.mkdir(parents=True, exist_ok=True)
    
    async def scrape_all_channels(self, limit_per_channel: int = 1000, days_back: int = 30):
        """
        Scrape all configured channels.
        
        Args:
            limit_per_channel: Maximum messages to scrape per channel
            days_back: Number of days back to scrape (for incremental scraping)
        """
        telegram_logger.log_scraping_start("all_channels", "batch_scraping")
        
        results = {}
        offset_date = datetime.now() - timedelta(days=days_back) if days_back > 0 else None
        
        async with TelegramClientService() as client:
            for channel in self.channels:
                try:
                    print(f"🔄 Scraping channel: {channel}")
                    channel_results = await self._scrape_channel(
                        client, 
                        channel, 
                        limit_per_channel, 
                        offset_date
                    )
                    results[channel] = channel_results
                    
                    # Small delay between channels to be respectful
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    telegram_logger.log_scraping_error(channel, e, "channel_scraping")
                    results[channel] = {"error": str(e)}
                    continue
        
        # Generate summary report
        await self._generate_scraping_report(results)
        
        return results
    
    async def scrape_single_channel(
        self, 
        channel_username: str, 
        limit: int = 1000, 
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Scrape a single channel.
        
        Args:
            channel_username: Username of the channel to scrape
            limit: Maximum messages to scrape
            days_back: Number of days back to scrape
        """
        offset_date = datetime.now() - timedelta(days=days_back) if days_back > 0 else None
        
        async with TelegramClientService() as client:
            return await self._scrape_channel(client, channel_username, limit, offset_date)
    
    async def _scrape_channel(
        self, 
        client: TelegramClientService, 
        channel_username: str, 
        limit: int, 
        offset_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Scrape a single channel and save data."""
        try:
            # Get channel info
            channel_info = await client.get_channel_info(channel_username)
            if not channel_info:
                return {"error": "Could not get channel info"}
            
            # Create date-based directory structure
            date_str = datetime.now().strftime("%Y-%m-%d")
            channel_dir = self.raw_messages_dir / date_str / channel_username
            channel_dir.mkdir(parents=True, exist_ok=True)
            
            # Scrape messages
            messages = []
            message_count = 0
            image_count = 0
            
            async for message_data in client.scrape_messages(channel_username, limit, offset_date):
                messages.append(message_data)
                message_count += 1
                
                if message_data.get("has_image"):
                    image_count += 1
                
                # Save in batches to avoid memory issues
                if len(messages) >= 100:
                    await self._save_messages_batch(channel_username, messages, channel_dir)
                    messages = []
            
            # Save remaining messages
            if messages:
                await self._save_messages_batch(channel_username, messages, channel_dir)
            
            # Save channel metadata
            metadata = {
                "channel_info": channel_info,
                "scraping_info": {
                    "scraped_at": datetime.now().isoformat(),
                    "messages_scraped": message_count,
                    "images_scraped": image_count,
                    "limit": limit,
                    "offset_date": offset_date.isoformat() if offset_date else None
                }
            }
            
            metadata_file = channel_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            telegram_logger.log_data_saved(
                channel_username, 
                str(channel_dir), 
                message_count
            )
            
            return {
                "success": True,
                "channel_info": channel_info,
                "messages_scraped": message_count,
                "images_scraped": image_count,
                "data_path": str(channel_dir)
            }
            
        except Exception as e:
            telegram_logger.log_scraping_error(channel_username, e, "channel_scraping")
            return {"error": str(e)}
    
    async def _save_messages_batch(
        self, 
        channel_username: str, 
        messages: List[Dict[str, Any]], 
        channel_dir: Path
    ):
        """Save a batch of messages to JSON files."""
        try:
            # Create timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"messages_{timestamp}_{len(messages)}.json"
            file_path = channel_dir / filename
            
            # Save messages with proper encoding
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            
            telegram_logger.log_data_saved(
                channel_username, 
                str(file_path), 
                len(messages)
            )
            
        except Exception as e:
            telegram_logger.log_scraping_error(channel_username, e, "batch_save")
    
    async def _generate_scraping_report(self, results: Dict[str, Any]):
        """Generate a summary report of the scraping operation."""
        report = {
            "scraping_report": {
                "generated_at": datetime.now().isoformat(),
                "total_channels": len(self.channels),
                "successful_channels": 0,
                "failed_channels": 0,
                "total_messages": 0,
                "total_images": 0,
                "channel_results": results
            }
        }
        
        for channel, result in results.items():
            if result.get("success"):
                report["scraping_report"]["successful_channels"] += 1
                report["scraping_report"]["total_messages"] += result.get("messages_scraped", 0)
                report["scraping_report"]["total_images"] += result.get("images_scraped", 0)
            else:
                report["scraping_report"]["failed_channels"] += 1
        
        # Save report
        report_file = self.data_dir / "raw" / f"scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Scraping Report: {report['scraping_report']['successful_channels']}/{report['scraping_report']['total_channels']} channels successful")
        print(f"📝 Total messages: {report['scraping_report']['total_messages']}")
        print(f"🖼️  Total images: {report['scraping_report']['total_images']}")
    
    def get_scraping_status(self) -> Dict[str, Any]:
        """Get the current status of scraping operations."""
        status = {
            "configured_channels": self.channels,
            "channel_summaries": {}
        }
        
        for channel in self.channels:
            summary = scraping_metrics.get_channel_summary(channel)
            status["channel_summaries"][channel] = summary
        
        return status
    
    async def incremental_scrape(self, hours_back: int = 24):
        """
        Perform incremental scraping for recent messages.
        
        Args:
            hours_back: Number of hours back to scrape
        """
        print(f"🔄 Starting incremental scrape for last {hours_back} hours")
        return await self.scrape_all_channels(limit_per_channel=500, days_back=hours_back/24)


# Convenience functions
async def scrape_ethiopian_medical_channels(limit_per_channel: int = 1000):
    """Convenience function to scrape all Ethiopian medical channels."""
    scraper = TelegramScraper()
    return await scraper.scrape_all_channels(limit_per_channel)


async def incremental_scrape_recent(hours_back: int = 24):
    """Convenience function for incremental scraping."""
    scraper = TelegramScraper()
    return await scraper.incremental_scrape(hours_back)


if __name__ == "__main__":
    # Test the scraper
    async def test_scraper():
        scraper = TelegramScraper()
        
        # Test single channel scraping (small limit for testing)
        print("Testing single channel scraping...")
        result = await scraper.scrape_single_channel("telegram", limit=5)
        print(f"Result: {result}")
        
        # Test status
        status = scraper.get_scraping_status()
        print(f"Status: {status}")
    
    asyncio.run(test_scraper()) 
#!/usr/bin/env python3
"""
Standalone Telegram scraping script for Ethiopian Medical Business Data Platform.
Can be run independently or as part of the data pipeline.
"""

import asyncio
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.scrapers.telegram_scraper import TelegramScraper
from app.utils.logging.logger import telegram_logger, scraping_metrics
from config import settings


async def main():
    """Main function for the scraping script."""
    parser = argparse.ArgumentParser(
        description="Scrape Ethiopian medical business Telegram channels"
    )
    
    parser.add_argument(
        "--channels",
        nargs="+",
        default=["chemed", "lobelia4cosmetics", "tikvahpharma"],
        help="List of channel usernames to scrape"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum messages to scrape per channel"
    )
    
    parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="Number of days back to scrape"
    )
    
    parser.add_argument(
        "--hours-back",
        type=int,
        default=None,
        help="Number of hours back for incremental scraping (overrides days-back)"
    )
    
    parser.add_argument(
        "--single-channel",
        type=str,
        help="Scrape only a single channel"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show scraping status and metrics"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test connection without scraping"
    )
    
    args = parser.parse_args()
    
    print("🏥 Ethiopian Medical Business Data Platform - Telegram Scraper")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Configuration: {args}")
    print()
    
    # Initialize scraper
    scraper = TelegramScraper()
    
    # Override channels if single channel is specified
    if args.single_channel:
        scraper.channels = [args.single_channel]
    
    # Show status if requested
    if args.status:
        print("📊 Current Scraping Status:")
        print("-" * 40)
        status = scraper.get_scraping_status()
        
        for channel, summary in status["channel_summaries"].items():
            if summary:
                print(f"📺 {channel}:")
                print(f"   Total messages: {summary.get('total_messages', 0)}")
                print(f"   Total images: {summary.get('total_images', 0)}")
                print(f"   Days scraped: {summary.get('days_scraped', 0)}")
                print(f"   Last scraped: {summary.get('last_scraped', 'Never')}")
                print()
            else:
                print(f"📺 {channel}: No data available")
                print()
        
        return
    
    # Dry run - test connection
    if args.dry_run:
        print("🔍 Testing Telegram connection...")
        try:
            from app.services.telegram.client import TelegramClientService
            
            async with TelegramClientService() as client:
                print("✅ Successfully connected to Telegram API")
                
                # Test channel access
                for channel in scraper.channels:
                    try:
                        info = await client.get_channel_info(channel)
                        if info:
                            print(f"✅ Channel {channel}: {info.get('title', 'Unknown')}")
                        else:
                            print(f"❌ Channel {channel}: Could not access")
                    except Exception as e:
                        print(f"❌ Channel {channel}: Error - {str(e)}")
                
        except Exception as e:
            print(f"❌ Failed to connect to Telegram API: {str(e)}")
            return
        
        print("🔍 Dry run completed successfully")
        return
    
    # Perform scraping
    try:
        if args.hours_back:
            print(f"🔄 Starting incremental scrape for last {args.hours_back} hours...")
            results = await scraper.incremental_scrape(args.hours_back)
        else:
            print(f"🔄 Starting full scrape for last {args.days_back} days...")
            results = await scraper.scrape_all_channels(args.limit, args.days_back)
        
        # Display results
        print("\n📋 Scraping Results:")
        print("-" * 40)
        
        successful_channels = 0
        total_messages = 0
        total_images = 0
        
        for channel, result in results.items():
            if result.get("success"):
                successful_channels += 1
                messages = result.get("messages_scraped", 0)
                images = result.get("images_scraped", 0)
                total_messages += messages
                total_images += images
                
                print(f"✅ {channel}: {messages} messages, {images} images")
                print(f"   Data saved to: {result.get('data_path', 'Unknown')}")
            else:
                print(f"❌ {channel}: Failed - {result.get('error', 'Unknown error')}")
        
        print(f"\n📊 Summary: {successful_channels}/{len(scraper.channels)} channels successful")
        print(f"📝 Total messages scraped: {total_messages}")
        print(f"🖼️  Total images scraped: {total_images}")
        
        # Show updated status
        print("\n📈 Updated Metrics:")
        print("-" * 40)
        status = scraper.get_scraping_status()
        for channel, summary in status["channel_summaries"].items():
            if summary:
                print(f"📺 {channel}: {summary.get('total_messages', 0)} total messages")
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed: {str(e)}")
        telegram_logger.log_scraping_error("script", e, "main_scraping")
        return 1
    
    print(f"\n✅ Scraping completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    # Run the main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
#!/usr/bin/env python3
"""
Test script for Telegram scraping functionality.
Verifies that the scraping system works correctly with the configured channels.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.telegram.client import TelegramClientService
from app.services.scrapers.telegram_scraper import TelegramScraper
from app.services.scrapers.channel_config import get_enabled_channels, validate_channel_configs
from app.utils.logging.logger import telegram_logger
from config import settings


async def test_telegram_connection():
    """Test basic Telegram API connection."""
    print("🔍 Testing Telegram API connection...")
    
    try:
        async with TelegramClientService() as client:
            me = await client.client.get_me()
            print(f"✅ Connected successfully as: {me.first_name} (@{me.username})")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False


async def test_channel_access():
    """Test access to configured channels."""
    print("\n🔍 Testing channel access...")
    
    channels = get_enabled_channels()
    accessible_channels = []
    
    async with TelegramClientService() as client:
        for channel in channels:
            try:
                print(f"  Testing {channel.username}...")
                info = await client.get_channel_info(channel.username)
                
                if info:
                    print(f"    ✅ Accessible: {info.get('title', 'Unknown')}")
                    accessible_channels.append(channel.username)
                else:
                    print(f"    ❌ Not accessible")
                    
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
    
    print(f"\n📊 Channel access summary: {len(accessible_channels)}/{len(channels)} channels accessible")
    return accessible_channels


async def test_message_scraping(limit: int = 5):
    """Test message scraping with a small limit."""
    print(f"\n🔍 Testing message scraping (limit: {limit})...")
    
    channels = get_enabled_channels()
    results = {}
    
    async with TelegramClientService() as client:
        for channel in channels[:2]:  # Test first 2 channels only
            try:
                print(f"  Scraping {channel.username}...")
                messages = []
                
                async for message in client.scrape_messages(channel.username, limit=limit):
                    messages.append(message)
                    if len(messages) >= limit:
                        break
                
                results[channel.username] = {
                    "success": True,
                    "messages_scraped": len(messages),
                    "sample_message": messages[0] if messages else None
                }
                
                print(f"    ✅ Scraped {len(messages)} messages")
                
            except Exception as e:
                print(f"    ❌ Error: {str(e)}")
                results[channel.username] = {
                    "success": False,
                    "error": str(e)
                }
    
    return results


async def test_data_lake_storage():
    """Test data lake storage functionality."""
    print("\n🔍 Testing data lake storage...")
    
    from app.services.scrapers.data_lake_manager import data_lake_manager
    
    # Test saving sample data
    sample_messages = [
        {
            "message_id": 12345,
            "channel_username": "test_channel",
            "date": "2024-01-01T12:00:00",
            "text": "Test message for data lake",
            "has_image": False,
            "has_document": False
        }
    ]
    
    try:
        file_path = data_lake_manager.save_messages("test_channel", sample_messages)
        print(f"✅ Sample data saved to: {file_path}")
        
        # Test retrieving data
        messages = data_lake_manager.get_latest_messages("test_channel", limit=10)
        print(f"✅ Retrieved {len(messages)} messages from data lake")
        
        return True
        
    except Exception as e:
        print(f"❌ Data lake test failed: {str(e)}")
        return False


async def test_full_scraping_pipeline():
    """Test the complete scraping pipeline."""
    print("\n🔍 Testing complete scraping pipeline...")
    
    try:
        scraper = TelegramScraper()
        
        # Test with very small limits for testing
        results = await scraper.scrape_single_channel("telegram", limit=3)
        
        if results.get("success"):
            print(f"✅ Pipeline test successful: {results['messages_scraped']} messages scraped")
            return True
        else:
            print(f"❌ Pipeline test failed: {results.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {str(e)}")
        return False


def test_configuration():
    """Test channel configuration."""
    print("\n🔍 Testing channel configuration...")
    
    # Validate configurations
    validation = validate_channel_configs()
    
    if validation["errors"]:
        print("❌ Configuration errors found:")
        for error in validation["errors"]:
            print(f"  - {error}")
    else:
        print("✅ No configuration errors found")
    
    if validation["warnings"]:
        print("⚠️  Configuration warnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
    
    print(f"📊 Configuration summary:")
    print(f"  - Total channels: {validation['total_channels']}")
    print(f"  - Enabled channels: {validation['enabled_channels']}")
    print(f"  - Categories: {validation['categories']}")
    print(f"  - Priorities: {validation['priorities']}")
    
    return len(validation["errors"]) == 0


async def main():
    """Run all tests."""
    print("🧪 Telegram Scraping System Test Suite")
    print("=" * 50)
    
    test_results = {
        "configuration": False,
        "connection": False,
        "channel_access": False,
        "message_scraping": False,
        "data_lake": False,
        "pipeline": False
    }
    
    # Test 1: Configuration
    print("\n1️⃣ Testing Configuration...")
    test_results["configuration"] = test_configuration()
    
    # Test 2: Telegram Connection
    print("\n2️⃣ Testing Telegram Connection...")
    test_results["connection"] = await test_telegram_connection()
    
    if not test_results["connection"]:
        print("❌ Cannot proceed with other tests without Telegram connection")
        return
    
    # Test 3: Channel Access
    print("\n3️⃣ Testing Channel Access...")
    accessible_channels = await test_channel_access()
    test_results["channel_access"] = len(accessible_channels) > 0
    
    # Test 4: Message Scraping
    print("\n4️⃣ Testing Message Scraping...")
    scraping_results = await test_message_scraping(limit=3)
    test_results["message_scraping"] = any(r.get("success") for r in scraping_results.values())
    
    # Test 5: Data Lake Storage
    print("\n5️⃣ Testing Data Lake Storage...")
    test_results["data_lake"] = await test_data_lake_storage()
    
    # Test 6: Full Pipeline
    print("\n6️⃣ Testing Full Pipeline...")
    test_results["pipeline"] = await test_full_scraping_pipeline()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The scraping system is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
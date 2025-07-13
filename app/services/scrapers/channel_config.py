"""
Channel configuration for Ethiopian Medical Business Data Platform.
Defines the channels to be scraped with their specific settings and metadata.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChannelConfig:
    """Configuration for a single Telegram channel."""
    
    username: str
    name: str
    description: str
    category: str
    priority: int  # 1 = highest priority
    enabled: bool = True
    scraping_limit: int = 1000
    scraping_interval_hours: int = 24
    keywords: List[str] = None
    image_download: bool = True
    document_download: bool = True
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


# Ethiopian Medical Business Channels Configuration
ETHIOPIAN_MEDICAL_CHANNELS = [
    ChannelConfig(
        username="chemed",
        name="Chemed Telegram Channel",
        description="Official channel for Chemed medical products and services",
        category="pharmaceutical",
        priority=1,
        keywords=["medicine", "pharmaceutical", "health", "medical", "drugs", "treatment"],
        scraping_limit=2000,
        scraping_interval_hours=12
    ),
    
    ChannelConfig(
        username="lobelia4cosmetics",
        name="Lobelia4cosmetics",
        description="Cosmetics and beauty products channel",
        category="cosmetics",
        priority=2,
        keywords=["cosmetics", "beauty", "skincare", "makeup", "personal_care"],
        scraping_limit=1500,
        scraping_interval_hours=24
    ),
    
    ChannelConfig(
        username="tikvahpharma",
        name="Tikvah Pharma",
        description="Tikvah pharmaceutical products and services",
        category="pharmaceutical",
        priority=1,
        keywords=["pharma", "medicine", "healthcare", "medical", "drugs", "treatment"],
        scraping_limit=2000,
        scraping_interval_hours=12
    )
]

# Additional channels that might be relevant (commented out for future use)
ADDITIONAL_CHANNELS = [
    # ChannelConfig(
    #     username="ethiopian_pharma",
    #     name="Ethiopian Pharmaceutical Association",
    #     description="Official channel of Ethiopian Pharmaceutical Association",
    #     category="association",
    #     priority=3,
    #     keywords=["pharmaceutical", "association", "regulation", "health_policy"],
    #     scraping_limit=1000,
    #     scraping_interval_hours=48
    # ),
    
    # ChannelConfig(
    #     username="addis_medical",
    #     name="Addis Medical Supplies",
    #     description="Medical supplies and equipment in Addis Ababa",
    #     category="medical_supplies",
    #     priority=2,
    #     keywords=["medical_supplies", "equipment", "hospital", "clinic", "healthcare"],
    #     scraping_limit=1500,
    #     scraping_interval_hours=24
    # ),
]


def get_enabled_channels() -> List[ChannelConfig]:
    """Get all enabled channels."""
    return [channel for channel in ETHIOPIAN_MEDICAL_CHANNELS if channel.enabled]


def get_channels_by_category(category: str) -> List[ChannelConfig]:
    """Get channels filtered by category."""
    return [channel for channel in get_enabled_channels() if channel.category == category]


def get_channels_by_priority(min_priority: int = 1) -> List[ChannelConfig]:
    """Get channels filtered by minimum priority."""
    return [channel for channel in get_enabled_channels() if channel.priority <= min_priority]


def get_channel_by_username(username: str) -> ChannelConfig:
    """Get a specific channel by username."""
    for channel in ETHIOPIAN_MEDICAL_CHANNELS:
        if channel.username == username:
            return channel
    return None


def get_channel_usernames() -> List[str]:
    """Get list of all channel usernames."""
    return [channel.username for channel in get_enabled_channels()]


def get_channels_for_image_analysis() -> List[ChannelConfig]:
    """Get channels that should have images downloaded for analysis."""
    return [channel for channel in get_enabled_channels() if channel.image_download]


def get_channels_for_document_analysis() -> List[ChannelConfig]:
    """Get channels that should have documents downloaded for analysis."""
    return [channel for channel in get_enabled_channels() if channel.document_download]


def get_scraping_schedule() -> Dict[str, Any]:
    """Get the scraping schedule based on channel configurations."""
    schedule = {}
    
    for channel in get_enabled_channels():
        schedule[channel.username] = {
            "name": channel.name,
            "category": channel.category,
            "priority": channel.priority,
            "scraping_limit": channel.scraping_limit,
            "scraping_interval_hours": channel.scraping_interval_hours,
            "keywords": channel.keywords,
            "image_download": channel.image_download,
            "document_download": channel.document_download
        }
    
    return schedule


def validate_channel_configs() -> Dict[str, Any]:
    """Validate channel configurations."""
    validation_results = {
        "total_channels": len(ETHIOPIAN_MEDICAL_CHANNELS),
        "enabled_channels": len(get_enabled_channels()),
        "categories": set(),
        "priorities": set(),
        "errors": [],
        "warnings": []
    }
    
    usernames = set()
    
    for channel in ETHIOPIAN_MEDICAL_CHANNELS:
        # Check for duplicate usernames
        if channel.username in usernames:
            validation_results["errors"].append(f"Duplicate username: {channel.username}")
        else:
            usernames.add(channel.username)
        
        # Collect categories and priorities
        validation_results["categories"].add(channel.category)
        validation_results["priorities"].add(channel.priority)
        
        # Validate configuration
        if channel.scraping_limit <= 0:
            validation_results["errors"].append(f"Invalid scraping limit for {channel.username}")
        
        if channel.scraping_interval_hours <= 0:
            validation_results["errors"].append(f"Invalid scraping interval for {channel.username}")
        
        if channel.priority < 1 or channel.priority > 10:
            validation_results["warnings"].append(f"Priority {channel.priority} for {channel.username} might be too high/low")
    
    validation_results["categories"] = list(validation_results["categories"])
    validation_results["priorities"] = list(validation_results["priorities"])
    
    return validation_results


def get_channel_metadata() -> Dict[str, Dict[str, Any]]:
    """Get metadata for all channels."""
    metadata = {}
    
    for channel in ETHIOPIAN_MEDICAL_CHANNELS:
        metadata[channel.username] = {
            "name": channel.name,
            "description": channel.description,
            "category": channel.category,
            "priority": channel.priority,
            "enabled": channel.enabled,
            "keywords": channel.keywords,
            "scraping_config": {
                "limit": channel.scraping_limit,
                "interval_hours": channel.scraping_interval_hours
            },
            "download_config": {
                "images": channel.image_download,
                "documents": channel.document_download
            }
        }
    
    return metadata


if __name__ == "__main__":
    # Test channel configuration
    print("Testing Channel Configuration...")
    
    # Get enabled channels
    enabled = get_enabled_channels()
    print(f"Enabled channels: {len(enabled)}")
    
    for channel in enabled:
        print(f"  - {channel.username}: {channel.name} ({channel.category})")
    
    # Get scraping schedule
    schedule = get_scraping_schedule()
    print(f"\nScraping schedule: {schedule}")
    
    # Validate configurations
    validation = validate_channel_configs()
    print(f"\nValidation results: {validation}")
    
    # Get metadata
    metadata = get_channel_metadata()
    print(f"\nChannel metadata: {metadata}") 
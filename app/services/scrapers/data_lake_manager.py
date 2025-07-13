"""
Data Lake Manager for Ethiopian Medical Business Data Platform.
Handles storage, organization, and validation of scraped Telegram data.
"""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import gzip

from app.utils.logging.logger import telegram_logger
from config import settings


class DataLakeManager:
    """Manages the data lake structure and operations."""
    
    def __init__(self):
        self.data_dir = Path(settings.storage.data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Create directory structure
        self._create_directory_structure()
    
    def _create_directory_structure(self):
        """Create the data lake directory structure."""
        directories = [
            self.raw_dir / "telegram_messages",
            self.raw_dir / "telegram_images",
            self.raw_dir / "telegram_documents",
            self.processed_dir / "cleaned_messages",
            self.processed_dir / "enriched_data",
            self.processed_dir / "analytics_ready"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def save_messages(
        self, 
        channel: str, 
        messages: List[Dict[str, Any]], 
        date: Optional[datetime] = None
    ) -> str:
        """
        Save messages to the data lake with proper partitioning.
        
        Args:
            channel: Channel username
            messages: List of message dictionaries
            date: Date for partitioning (defaults to today)
        
        Returns:
            Path to the saved file
        """
        if not date:
            date = datetime.now()
        
        # Create partitioned directory structure
        date_str = date.strftime("%Y-%m-%d")
        channel_dir = self.raw_dir / "telegram_messages" / date_str / channel
        channel_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp and message count
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"messages_{timestamp}_{len(messages)}.json"
        file_path = channel_dir / filename
        
        # Add metadata to messages
        enriched_messages = []
        for message in messages:
            enriched_message = message.copy()
            enriched_message["_metadata"] = {
                "scraped_at": datetime.now().isoformat(),
                "channel": channel,
                "partition_date": date_str,
                "file_path": str(file_path),
                "message_hash": self._generate_message_hash(message)
            }
            enriched_messages.append(enriched_message)
        
        # Save with compression
        compressed_path = file_path.with_suffix('.json.gz')
        with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
            json.dump(enriched_messages, f, indent=2, ensure_ascii=False)
        
        # Also save uncompressed version for easy access
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(enriched_messages, f, indent=2, ensure_ascii=False)
        
        telegram_logger.log_data_saved(channel, str(file_path), len(messages))
        
        return str(file_path)
    
    def save_channel_metadata(
        self, 
        channel: str, 
        metadata: Dict[str, Any], 
        date: Optional[datetime] = None
    ) -> str:
        """Save channel metadata to the data lake."""
        if not date:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        channel_dir = self.raw_dir / "telegram_messages" / date_str / channel
        channel_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = channel_dir / "channel_metadata.json"
        
        # Add metadata
        enriched_metadata = metadata.copy()
        enriched_metadata["_metadata"] = {
            "saved_at": datetime.now().isoformat(),
            "channel": channel,
            "partition_date": date_str
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(enriched_metadata, f, indent=2, ensure_ascii=False)
        
        return str(metadata_file)
    
    def get_messages_for_date_range(
        self, 
        channel: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Retrieve messages for a specific date range."""
        messages = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            channel_dir = self.raw_dir / "telegram_messages" / date_str / channel
            
            if channel_dir.exists():
                for file_path in channel_dir.glob("messages_*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            file_messages = json.load(f)
                            messages.extend(file_messages)
                    except Exception as e:
                        telegram_logger.log_scraping_error(
                            channel, e, f"loading_messages_from_{file_path}"
                        )
            
            current_date += timedelta(days=1)
        
        return messages
    
    def get_latest_messages(
        self, 
        channel: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get the latest messages for a channel."""
        # Find the most recent message files
        message_files = []
        
        for date_dir in sorted(self.raw_dir.glob("telegram_messages/*"), reverse=True):
            channel_dir = date_dir / channel
            if channel_dir.exists():
                for file_path in sorted(channel_dir.glob("messages_*.json"), reverse=True):
                    message_files.append(file_path)
        
        messages = []
        for file_path in message_files[:limit]:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_messages = json.load(f)
                    messages.extend(file_messages)
            except Exception as e:
                telegram_logger.log_scraping_error(
                    channel, e, f"loading_latest_messages_from_{file_path}"
                )
        
        # Sort by message date and return the latest
        messages.sort(key=lambda x: x.get('date', ''), reverse=True)
        return messages[:limit]
    
    def validate_data_integrity(self, channel: str) -> Dict[str, Any]:
        """Validate the integrity of stored data for a channel."""
        validation_results = {
            "channel": channel,
            "validation_date": datetime.now().isoformat(),
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "total_messages": 0,
            "duplicate_messages": 0,
            "missing_fields": [],
            "errors": []
        }
        
        message_hashes = set()
        
        for date_dir in self.raw_dir.glob("telegram_messages/*"):
            channel_dir = date_dir / channel
            if not channel_dir.exists():
                continue
            
            for file_path in channel_dir.glob("messages_*.json"):
                validation_results["total_files"] += 1
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        messages = json.load(f)
                    
                    if not isinstance(messages, list):
                        validation_results["errors"].append(f"Invalid format in {file_path}")
                        validation_results["invalid_files"] += 1
                        continue
                    
                    validation_results["valid_files"] += 1
                    validation_results["total_messages"] += len(messages)
                    
                    # Check for duplicates and missing fields
                    for message in messages:
                        message_hash = message.get("_metadata", {}).get("message_hash")
                        if message_hash:
                            if message_hash in message_hashes:
                                validation_results["duplicate_messages"] += 1
                            else:
                                message_hashes.add(message_hash)
                        
                        # Check for required fields
                        required_fields = ["message_id", "channel_username", "date", "text"]
                        for field in required_fields:
                            if field not in message:
                                validation_results["missing_fields"].append(field)
                
                except Exception as e:
                    validation_results["errors"].append(f"Error reading {file_path}: {str(e)}")
                    validation_results["invalid_files"] += 1
        
        return validation_results
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data files to save storage space."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for date_dir in self.raw_dir.glob("telegram_messages/*"):
            try:
                date_str = date_dir.name
                dir_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if dir_date < cutoff_date:
                    shutil.rmtree(date_dir)
                    print(f"🗑️  Removed old data directory: {date_dir}")
            
            except Exception as e:
                print(f"⚠️  Error cleaning up {date_dir}: {str(e)}")
    
    def get_data_lake_stats(self) -> Dict[str, Any]:
        """Get statistics about the data lake."""
        stats = {
            "total_channels": 0,
            "total_messages": 0,
            "total_images": 0,
            "total_documents": 0,
            "date_range": {},
            "storage_size": {},
            "channel_stats": {}
        }
        
        # Count messages and get date range
        all_dates = set()
        channels = set()
        
        for date_dir in self.raw_dir.glob("telegram_messages/*"):
            all_dates.add(date_dir.name)
            
            for channel_dir in date_dir.iterdir():
                if channel_dir.is_dir():
                    channels.add(channel_dir.name)
                    
                    if channel_dir.name not in stats["channel_stats"]:
                        stats["channel_stats"][channel_dir.name] = {
                            "total_messages": 0,
                            "date_range": {"earliest": None, "latest": None}
                        }
                    
                    for file_path in channel_dir.glob("messages_*.json"):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                messages = json.load(f)
                                stats["channel_stats"][channel_dir.name]["total_messages"] += len(messages)
                                stats["total_messages"] += len(messages)
                        except:
                            pass
        
        stats["total_channels"] = len(channels)
        
        if all_dates:
            stats["date_range"] = {
                "earliest": min(all_dates),
                "latest": max(all_dates)
            }
        
        # Calculate storage size
        stats["storage_size"] = {
            "raw_messages": self._get_directory_size(self.raw_dir / "telegram_messages"),
            "raw_images": self._get_directory_size(self.raw_dir / "telegram_images"),
            "raw_documents": self._get_directory_size(self.raw_dir / "telegram_documents")
        }
        
        return stats
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate the size of a directory in bytes."""
        total_size = 0
        if directory.exists():
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        return total_size
    
    def _generate_message_hash(self, message: Dict[str, Any]) -> str:
        """Generate a hash for a message to detect duplicates."""
        # Create a string representation of the message content
        content = f"{message.get('message_id', '')}{message.get('date', '')}{message.get('text', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()


# Global data lake manager instance
data_lake_manager = DataLakeManager()


if __name__ == "__main__":
    # Test the data lake manager
    print("Testing Data Lake Manager...")
    
    # Get stats
    stats = data_lake_manager.get_data_lake_stats()
    print(f"Data Lake Stats: {json.dumps(stats, indent=2)}")
    
    # Test validation
    for channel in ["chemed", "lobelia4cosmetics", "tikvahpharma"]:
        validation = data_lake_manager.validate_data_integrity(channel)
        print(f"Validation for {channel}: {validation}") 
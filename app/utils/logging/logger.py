"""
Logging configuration for Ethiopian Medical Business Data Platform.
Provides structured logging for Telegram scraping operations.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
from loguru import logger
import os

from config import settings


class TelegramScrapingLogger:
    """Specialized logger for Telegram scraping operations."""
    
    def __init__(self, log_file: Optional[str] = None):
        self.log_file = log_file or settings.logging.file
        self.setup_logger()
    
    def setup_logger(self):
        """Configure the logger with appropriate handlers and formatting."""
        # Remove default handler
        logger.remove()
        
        # Console handler with color
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.logging.level,
            colorize=True
        )
        
        # File handler for all logs
        logger.add(
            self.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )
        
        # Special file for scraping operations
        scraping_log_file = Path(settings.storage.logs_dir) / "telegram_scraping.log"
        scraping_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            scraping_log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[channel]} | {extra[operation]} | {message}",
            level="INFO",
            rotation="50 MB",
            retention="90 days",
            compression="zip",
            filter=lambda record: "telegram_scraping" in record["extra"]
        )
    
    def log_scraping_start(self, channel: str, operation: str = "scraping"):
        """Log the start of a scraping operation."""
        logger.bind(
            telegram_scraping=True,
            channel=channel,
            operation=operation
        ).info(f"Starting {operation} for channel: {channel}")
    
    def log_scraping_success(self, channel: str, message_count: int, image_count: int = 0):
        """Log successful scraping operation."""
        logger.bind(
            telegram_scraping=True,
            channel=channel,
            operation="scraping"
        ).info(f"Successfully scraped {message_count} messages and {image_count} images from {channel}")
    
    def log_scraping_error(self, channel: str, error: Exception, operation: str = "scraping"):
        """Log scraping errors."""
        logger.bind(
            telegram_scraping=True,
            channel=channel,
            operation=operation
        ).error(f"Error during {operation} for {channel}: {str(error)}")
    
    def log_rate_limit(self, channel: str, retry_after: int):
        """Log rate limiting events."""
        logger.bind(
            telegram_scraping=True,
            channel=channel,
            operation="rate_limit"
        ).warning(f"Rate limited for {channel}, retry after {retry_after} seconds")
    
    def log_data_saved(self, channel: str, file_path: str, record_count: int):
        """Log when data is saved to the data lake."""
        logger.bind(
            telegram_scraping=True,
            channel=channel,
            operation="data_save"
        ).info(f"Saved {record_count} records to {file_path} for {channel}")
    
    def log_image_download(self, channel: str, image_id: str, success: bool, file_path: Optional[str] = None):
        """Log image download operations."""
        operation = "image_download"
        if success:
            logger.bind(
                telegram_scraping=True,
                channel=channel,
                operation=operation
            ).info(f"Downloaded image {image_id} to {file_path} from {channel}")
        else:
            logger.bind(
                telegram_scraping=True,
                channel=channel,
                operation=operation
            ).error(f"Failed to download image {image_id} from {channel}")


class ScrapingMetrics:
    """Track scraping metrics and statistics."""
    
    def __init__(self):
        self.metrics_file = Path(settings.storage.logs_dir) / "scraping_metrics.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics = self.load_metrics()
    
    def load_metrics(self) -> Dict[str, Any]:
        """Load existing metrics from file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metrics: {e}")
                return {}
        return {}
    
    def save_metrics(self):
        """Save metrics to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def update_channel_metrics(self, channel: str, message_count: int, image_count: int = 0):
        """Update metrics for a specific channel."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if channel not in self.metrics:
            self.metrics[channel] = {}
        
        if today not in self.metrics[channel]:
            self.metrics[channel][today] = {
                "messages": 0,
                "images": 0,
                "last_scraped": None,
                "scraping_count": 0
            }
        
        self.metrics[channel][today]["messages"] += message_count
        self.metrics[channel][today]["images"] += image_count
        self.metrics[channel][today]["last_scraped"] = datetime.now().isoformat()
        self.metrics[channel][today]["scraping_count"] += 1
        
        self.save_metrics()
    
    def get_channel_summary(self, channel: str) -> Dict[str, Any]:
        """Get summary statistics for a channel."""
        if channel not in self.metrics:
            return {}
        
        channel_data = self.metrics[channel]
        total_messages = sum(day["messages"] for day in channel_data.values())
        total_images = sum(day["images"] for day in channel_data.values())
        total_scrapes = sum(day["scraping_count"] for day in channel_data.values())
        
        return {
            "total_messages": total_messages,
            "total_images": total_images,
            "total_scrapes": total_scrapes,
            "days_scraped": len(channel_data),
            "last_scraped": max(day["last_scraped"] for day in channel_data.values()) if channel_data else None
        }


# Global logger instance
telegram_logger = TelegramScrapingLogger()
scraping_metrics = ScrapingMetrics()


def get_logger(name: str = __name__):
    """Get a logger instance with the specified name."""
    return logger.bind(name=name)


def log_scraping_operation(channel: str, operation: str, **kwargs):
    """Convenience function for logging scraping operations."""
    logger.bind(
        telegram_scraping=True,
        channel=channel,
        operation=operation
    ).info(f"{operation} for {channel}: {kwargs}")


if __name__ == "__main__":
    # Test logging functionality
    test_logger = get_logger("test")
    test_logger.info("Testing logging system")
    
    telegram_logger.log_scraping_start("test_channel")
    telegram_logger.log_scraping_success("test_channel", 100, 5)
    telegram_logger.log_data_saved("test_channel", "/path/to/file.json", 100)
    
    scraping_metrics.update_channel_metrics("test_channel", 100, 5)
    print("Logging system test completed") 
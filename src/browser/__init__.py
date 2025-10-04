"""
Package chứa các module liên quan đến trình duyệt Playwright.
Cung cấp cấu hình, instance và quản lý cho browser.
"""

from .browser_config import (
    BrowserConfig,
    ConfigType,
    get_browser_config,
)
from .browser_instance import (
    BrowserInstance,
)
from .browser_manager import (
    BrowserManager,
)

__all__ = [
    # Config
    "BrowserConfig",
    "ConfigType",
    "get_browser_config",
    # Instance
    "BrowserInstance",
    # Manager
    "BrowserManager",
]

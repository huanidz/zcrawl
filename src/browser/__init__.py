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
    browser_context,
    create_browser_instance,
)
from .browser_manager import (
    BrowserManager,
    get_browser_manager,
)
from .browser_manager import (
    create_browser_instance as create_managed_browser_instance,
)
from .browser_manager import (
    get_browser_instance as get_managed_browser_instance,
)

__all__ = [
    # Config
    "BrowserConfig",
    "ConfigType",
    "get_browser_config",
    # Instance
    "BrowserInstance",
    "browser_context",
    "create_browser_instance",
    # Manager
    "BrowserManager",
    "get_browser_manager",
    "create_managed_browser_instance",
    "get_managed_browser_instance",
]

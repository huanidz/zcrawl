"""
Module chứa cấu hình cho trình duyệt Playwright Chromium.
Cung cấp các phương thức để lấy cấu hình trình duyệt phù hợp cho crawling.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ConfigType(str, Enum):
    """
    Enum định nghĩa các loại cấu hình trình duyệt có sẵn.
    """

    DEFAULT = "default"
    STEALTH = "stealth"
    DEBUG = "debug"


class BrowserConfig(BaseModel):
    """
    Class chứa cấu hình cho trình duyệt Playwright Chromium.
    Cung cấp các phương thức để lấy cấu hình trình duyệt phù hợp.
    """

    # Cấu hình cơ bản
    headless: bool = Field(
        default=True, description="Chạy trình duyệt ở chế độ headless"
    )
    devtools: bool = Field(default=False, description="Bật developer tools")

    # Cấu hình viewport
    viewport_width: int = Field(default=1920, description="Chiều rộng viewport")
    viewport_height: int = Field(default=1080, description="Chiều cao viewport")

    # Cấu hình user agent
    user_agent: Optional[str] = Field(default=None, description="User agent tùy chỉnh")

    # Cấu hình proxy
    proxy_server: Optional[str] = Field(
        default=None, description="Địa chỉ proxy server"
    )
    proxy_username: Optional[str] = Field(
        default=None, description="Tên đăng nhập proxy"
    )
    proxy_password: Optional[str] = Field(default=None, description="Mật khẩu proxy")

    # Cấu hình timeouts
    timeout: int = Field(default=30000, description="Timeout mặc định (ms)")

    # Cấu hình additional arguments
    args: List[str] = Field(
        default_factory=list, description="Additional arguments for chromium"
    )

    class Config:
        """Pydantic configuration"""

        arbitrary_types_allowed = True

    def get_launch_options(self) -> Dict:
        """
        Lấy các tùy chọn khởi động cho playwright browser.

        Returns:
            Dict: Dictionary chứa các tùy chọn khởi động
        """
        options = {
            "headless": self.headless,
            "devtools": self.devtools,
            "timeout": self.timeout,
            "args": self.args.copy(),
        }

        # Thêm proxy nếu có
        if self.proxy_server:
            proxy_config = {"server": self.proxy_server}
            if self.proxy_username and self.proxy_password:
                proxy_config["username"] = self.proxy_username
                proxy_config["password"] = self.proxy_password
            options["proxy"] = proxy_config

        return options

    def get_context_options(self) -> Dict:
        """
        Lấy các tùy chọn cho browser context.

        Returns:
            Dict: Dictionary chứa các tùy chọn context
        """
        options = {
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
        }

        # Thêm user agent nếu có
        if self.user_agent:
            options["user_agent"] = self.user_agent

        return options

    @classmethod
    def create_default_config(cls) -> "BrowserConfig":
        """
        Tạo cấu hình mặc định cho trình duyệt.

        Returns:
            BrowserConfig: Instance với cấu hình mặc định
        """
        return cls(
            headless=True,
            devtools=False,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=30000,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--single-process",
                "--disable-gpu",
            ],
        )

    @classmethod
    def create_stealth_config(cls) -> "BrowserConfig":
        """
        Tạo cấu hình stealth để tránh bị phát hiện.

        Returns:
            BrowserConfig: Instance với cấu hình stealth
        """
        return cls(
            headless=True,
            devtools=False,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            timeout=60000,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--single-process",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-blink-features=AutomationControlled",
            ],
        )

    @classmethod
    def create_debug_config(cls) -> "BrowserConfig":
        """
        Tạo cấu hình cho việc debug.

        Returns:
            BrowserConfig: Instance với cấu hình debug
        """
        return cls(
            headless=False,
            devtools=True,
            viewport_width=1920,
            viewport_height=1080,
            timeout=60000,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--auto-open-devtools-for-tabs",
            ],
        )


def get_browser_config(config_type: ConfigType = ConfigType.DEFAULT) -> BrowserConfig:
    """
    Helper function để lấy cấu hình trình duyệt theo loại.

    Args:
        config_type (ConfigType): Loại cấu hình (ConfigType.DEFAULT, ConfigType.STEALTH, ConfigType.DEBUG)

    Returns:
        BrowserConfig: Instance BrowserConfig với cấu hình tương ứng
    """
    config_map = {
        ConfigType.DEFAULT: BrowserConfig.create_default_config(),
        ConfigType.STEALTH: BrowserConfig.create_stealth_config(),
        ConfigType.DEBUG: BrowserConfig.create_debug_config(),
    }

    return config_map[config_type]

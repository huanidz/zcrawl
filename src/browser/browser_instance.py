"""
Module chứa wrapper cho Playwright browser instance.
Cung cấp các phương thức để quản lý browser và contexts một cách dễ dàng.
"""

from contextlib import asynccontextmanager
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    BrowserType,
    Playwright,
    async_playwright,
)

from .browser_config import BrowserConfig, ConfigType, get_browser_config


class BrowserInstance:
    """
    Class wrapper cho Playwright browser instance.
    Cung cấp các phương thức để khởi động và quản lý browser contexts.
    """

    def __init__(self, config: Optional[BrowserConfig] = None):
        """
        Khởi tạo BrowserInstance.

        Args:
            config (Optional[BrowserConfig]): Cấu hình cho browser. Nếu None, sử dụng cấu hình mặc định.
        """
        self.config = config or get_browser_config(ConfigType.DEFAULT)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._browser_type: Optional[BrowserType] = None
        self._is_started = False

    async def start(self) -> None:
        """
        Khởi động browser instance.
        """
        if self._is_started:
            return

        self._playwright = await async_playwright().start()
        self._browser_type = self._playwright.chromium

        launch_options = self.config.get_launch_options()
        self._browser = await self._browser_type.launch(**launch_options)
        self._is_started = True

    async def stop(self) -> None:
        """
        Dừng browser instance và cleanup resources.
        """
        if not self._is_started:
            return

        try:
            if self._browser:
                await self._browser.close()
                self._browser = None

            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

            self._browser_type = None
            self._is_started = False
        except Exception as e:
            # Log lỗi nhưng không raise để đảm bảo cleanup hoàn tất
            from loguru import logger
            logger.warning(f"Lỗi khi dừng browser instance: {e}")

    @property
    def browser(self) -> Browser:
        """
        Lấy Playwright browser instance.

        Returns:
            Browser: Playwright browser instance

        Raises:
            RuntimeError: Nếu browser chưa được khởi động
        """
        if not self._is_started or not self._browser:
            raise RuntimeError("Browser chưa được khởi động. Gọi start() trước.")
        return self._browser

    async def create_context(self, **kwargs) -> BrowserContext:
        """
        Tạo mới browser context.

        Args:
            **kwargs: Additional options cho context

        Returns:
            BrowserContext: Browser context mới

        Raises:
            RuntimeError: Nếu browser chưa được khởi động
        """
        if not self._is_started or not self._browser:
            raise RuntimeError("Browser chưa được khởi động. Gọi start() trước.")

        context_options = self.config.get_context_options()
        context_options.update(kwargs)

        return await self._browser.new_context(**context_options)

    @asynccontextmanager
    async def context(self, **kwargs):
        """
        Context manager cho browser context.

        Args:
            **kwargs: Additional options cho context

        Yields:
            BrowserContext: Browser context
        """
        context = None
        try:
            context = await self.create_context(**kwargs)
            yield context
        finally:
            if context:
                await context.close()

    async def create_page(self, **kwargs):
        """
        Tạo mới page trong một context mới.

        Args:
            **kwargs: Additional options cho context

        Returns:
            Page: Page mới
        """
        async with self.context(**kwargs) as context:
            return await context.new_page()

    def is_started(self) -> bool:
        """
        Kiểm tra xem browser đã được khởi động chưa.

        Returns:
            bool: True nếu browser đã được khởi động
        """
        return self._is_started

    async def __aenter__(self):
        """
        Async context manager entry.
        """
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        """
        await self.stop()

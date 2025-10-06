"""
Module chứa class BaseScraper - class cơ bản cho tất cả các Scraper.
Cung cấp các chức năng chung và quản lý trình duyệt.
"""

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import List, Optional

from loguru import logger
from playwright.async_api import BrowserContext, Page, Response

from ..browser.browser_config import BrowserConfig, ConfigType, get_browser_config
from ..browser.browser_instance import BrowserInstance
from ..models.ScrapingResult import NavigableLink, PageScrapeResult, ScrapedImage
from ..utils.image import extract_images
from ..utils.navigation import extract_navigable_links


class BaseScraper(ABC):
    """
    Class cơ bản cho tất cả các Scraper.
    Cung cấp các chức năng chung và quản lý trình duyệt.
    """

    def __init__(
        self,
        browser_config: Optional[BrowserConfig] = None,
    ):
        """
        Khởi tạo BaseScraper.

        Args:
            browser_config (Optional[BrowserConfig]): Cấu hình cho trình duyệt
        """
        self.browser_config = browser_config or get_browser_config(ConfigType.DEFAULT)
        self._browser_instance = BrowserInstance(self.browser_config)
        self._is_started = False
        self._context: Optional[BrowserContext] = None
        self._current_page: Optional[Page] = None
        self._startup_task = None


    async def start(self) -> None:
        """
        Khởi động Scraper và trình duyệt.
        """
        if self._is_started:
            return

        try:
            await self._browser_instance.start()
            self._is_started = True
            logger.info("BaseScraper đã được khởi động")
        except Exception as e:
            logger.error(f"Lỗi khi khởi động BaseScraper: {e}")
            raise

    async def stop(self) -> None:
        """
        Dừng Scraper và trình duyệt.
        """
        if not self._is_started:
            return

        try:
            # Hủy startup task nếu vẫn đang chạy
            if self._startup_task and not self._startup_task.done():
                self._startup_task.cancel()
                try:
                    await self._startup_task
                except asyncio.CancelledError:
                    pass
                self._startup_task = None

            # Đóng page hiện tại nếu có
            if self._current_page:
                await self._current_page.close()
                self._current_page = None

            # Đóng context nếu có
            if self._context:
                await self._context.close()
                self._context = None

            # Dừng trình duyệt
            await self._browser_instance.stop()
            self._is_started = False
            logger.info("BaseScraper đã được dừng")
        except Exception as e:
            logger.error(f"Lỗi khi dừng BaseScraper: {e}")
            raise

    @property
    def browser_instance(self) -> BrowserInstance:
        """
        Lấy browser instance.

        Returns:
            BrowserInstance: Browser instance

        Raises:
            RuntimeError: Nếu Scraper chưa được khởi động
        """
        if not self._is_started:
            raise RuntimeError("Scraper chưa được khởi động. Gọi start() trước.")
        return self._browser_instance

    @property
    def is_started(self) -> bool:
        """
        Kiểm tra Scraper đã được khởi động chưa.

        Returns:
            bool: True nếu Scraper đã được khởi động
        """
        return self._is_started

    async def create_context(self, **kwargs) -> BrowserContext:
        """
        Tạo mới browser context.

        Args:
            **kwargs: Additional options cho context

        Returns:
            BrowserContext: Browser context mới
        """
        if not self._is_started:
            raise RuntimeError("Scraper chưa được khởi động. Gọi start() trước.")

        # Đóng context cũ nếu có
        if self._context:
            await self._context.close()

        self._context = await self._browser_instance.create_context(**kwargs)
        return self._context

    async def get_context(self) -> BrowserContext:
        """
        Lấy browser context hiện tại, tạo mới nếu chưa có.

        Returns:
            BrowserContext: Browser context
        """
        if not self._context:
            await self.create_context()
        return self._context

    async def create_page(self, **kwargs) -> Page:
        """
        Tạo mới page trong context hiện tại.

        Args:
            **kwargs: Additional options cho page

        Returns:
            Page: Page mới
        """
        if not self._is_started:
            raise RuntimeError("Scraper chưa được khởi động. Gọi start() trước.")

        context = await self.get_context()

        # Đóng page cũ nếu có
        if self._current_page:
            await self._current_page.close()

        self._current_page = await context.new_page()
        return self._current_page

    async def get_page(self) -> Page:
        """
        Lấy page hiện tại, tạo mới nếu chưa có.

        Returns:
            Page: Page hiện tại
        """
        if not self._current_page:
            await self.create_page()
        return self._current_page

    @asynccontextmanager
    async def page_context(self, **kwargs):
        """
        Context manager cho việc sử dụng page.

        Args:
            **kwargs: Additional options cho page

        Yields:
            Page: Page mới
        """
        page = None
        try:
            page = await self.create_page(**kwargs)
            yield page
        finally:
            if page:
                await page.close()

    @asynccontextmanager
    async def browser_context(self, **kwargs):
        """
        Context manager cho việc sử dụng browser context.

        Args:
            **kwargs: Additional options cho context

        Yields:
            BrowserContext: Browser context mới
        """
        context = None
        try:
            context = await self.create_context(**kwargs)
            yield context
        finally:
            if context:
                await context.close()

    async def navigate_to(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: Optional[int] = None,
    ) -> Response:
        """
        Điều hướng đến URL.

        Args:
            url (str): URL để điều hướng
            wait_until (str): Điều kiện chờ ("domcontentloaded", "load", "networkidle")
            timeout (Optional[int]): Timeout tùy chỉnh

        Returns:
            Response: Response từ trang web
        """
        page = await self.get_page()

        actual_timeout = timeout or self.browser_config.timeout

        logger.info(f"Điều hướng đến: {url}")
        response = await page.goto(
            url,
            wait_until=wait_until,
            timeout=actual_timeout,
        )

        return response

    async def wait_for_element(
        self,
        selector: str,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Chờ cho element xuất hiện.

        Args:
            selector (str): CSS selector của element
            timeout (Optional[int]): Timeout tùy chỉnh
        """
        page = await self.get_page()

        actual_timeout = timeout or self.browser_config.timeout

        logger.debug(f"Chờ element: {selector}")
        await page.wait_for_selector(selector, timeout=actual_timeout)

    async def click_element(
        self,
        selector: str,
        wait_for_selector: bool = True,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Click vào element.

        Args:
            selector (str): CSS selector của element
            wait_for_selector (bool): Có chờ element xuất hiện không
            timeout (Optional[int]): Timeout tùy chỉnh
        """
        page = await self.get_page()

        if wait_for_selector:
            await self.wait_for_element(selector, timeout)

        logger.debug(f"Click element: {selector}")
        await page.click(selector)

    async def type_text(
        self,
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Nhập text vào element.

        Args:
            selector (str): CSS selector của element
            text (str): Text cần nhập
            clear_first (bool): Xóa text hiện tại trước khi nhập
            timeout (Optional[int]): Timeout tùy chỉnh
        """
        page = await self.get_page()

        if clear_first:
            await page.fill(selector, "")

        logger.debug(f"Nhập text vào {selector}: {text}")
        await page.type(selector, text)

    async def get_page_html(self) -> str:
        """
        Lấy HTML của trang hiện tại.

        Returns:
            str: HTML của trang
        """
        page = await self.get_page()
        return await page.content()

    async def execute_script(self, script: str) -> any:
        """
        Thực thi JavaScript trên trang.

        Args:
            script (str): JavaScript code

        Returns:
            any: Kết quả thực thi script
        """
        page = await self.get_page()
        return await page.evaluate(script)

    async def take_screenshot(self, path: str, full_page: bool = True) -> None:
        """
        Chụp screenshot trang hiện tại.

        Args:
            path (str): Đường dẫn lưu screenshot
            full_page (bool): Chụp toàn bộ trang
        """
        page = await self.get_page()
        await page.screenshot(path=path, full_page=full_page)
        logger.info(f"Đã chụp screenshot: {path}")

    async def wait_for_navigation(
        self,
        wait_until: str = "domcontentloaded",
        timeout: Optional[int] = None,
    ) -> Response:
        """
        Chờ cho navigation hoàn tất.

        Args:
            wait_until (str): Điều kiện chờ
            timeout (Optional[int]): Timeout tùy chỉnh

        Returns:
            Response: Response từ navigation
        """
        page = await self.get_page()

        actual_timeout = timeout or self.browser_config.timeout

        return await page.wait_for_load_state(wait_until, timeout=actual_timeout)

    async def extract_navigable_links(
        self, html: str, base_url: Optional[str] = None, current_depth: int = 0
    ) -> List[NavigableLink]:
        """
        Trích xuất tất cả các liên kết có thể điều hướng từ HTML.

        Args:
            html (str): Nội dung HTML cần phân tích
            base_url (Optional[str]): URL để giải quyết các liên kết tương đối
            current_depth (int): Độ sâu hiện tại của liên kết

        Returns:
            List[NavigableLink]: Danh sách các liên kết có thể điều hướng
        """
        return extract_navigable_links(html, base_url, current_depth)

    async def extract_images(
        self, html: str, base_url: Optional[str] = None
    ) -> List[ScrapedImage]:
        """
        Trích xuất tất cả các hình ảnh từ HTML.

        Args:
            html (str): Nội dung HTML cần phân tích
            base_url (Optional[str]): URL cơ sở để giải quyết các liên kết tương đối

        Returns:
            List[ScrapedImage]: Danh sách các hình ảnh đã trích xuất
        """
        return extract_images(html, base_url)

    @abstractmethod
    async def scrape(self, url: str, **kwargs) -> PageScrapeResult:
        """
        Phương thức abstract để scrape một URL.
        Phải được implement bởi các class con.

        Args:
            url (str): URL để scrape
            **kwargs: Additional parameters

        Returns:
            PageScrapeResult: Kết quả scrape
        """
        pass

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

"""
Module chứa class SinglePageCrawler - crawler đơn giản cho một trang web.
Kế thừa từ BaseCrawler và cung cấp chức năng crawl trang đơn.
"""

from typing import Optional

from loguru import logger

from ..browser.browser_config import BrowserConfig
from ..models.CrawlResult import CrawlResult
from .BaseCrawler import BaseCrawler


class SinglePageCrawler(BaseCrawler):
    """
    Crawler đơn giản cho việc lấy nội dung của một trang web.
    Kế thừa từ BaseCrawler và implement phương thức crawl().
    """

    def __init__(
        self,
        browser_config: Optional[BrowserConfig] = None,
        auto_start: bool = True,
        wait_for_selector: Optional[str] = None,
        wait_timeout: int = 30000,
    ):
        """
        Khởi tạo SinglePageCrawler.

        Args:
            browser_config (Optional[BrowserConfig]): Cấu hình cho trình duyệt
            auto_start (bool): Tự động khởi động trình duyệt sau khi tạo
            wait_for_selector (Optional[str]): CSS selector để chờ trước khi lấy nội dung
            wait_timeout (int): Timeout khi chờ element (ms)
        """
        super().__init__(browser_config, auto_start)
        self.wait_for_selector = wait_for_selector
        self.wait_timeout = wait_timeout

    async def crawl(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: Optional[int] = None,
        screenshot_path: Optional[str] = None,
        **kwargs,
    ) -> CrawlResult:
        """
        Crawl một trang web và trả về nội dung HTML.

        Args:
            url (str): URL để crawl
            wait_until (str): Điều kiện chờ ("domcontentloaded", "load", "networkidle")
            timeout (Optional[int]): Timeout tùy chỉnh
            screenshot_path (Optional[str]): Đường dẫn lưu screenshot (nếu có)
            **kwargs: Additional parameters

        Returns:
            CrawlResult: Kết quả crawl với URL và HTML content

        Raises:
            RuntimeError: Nếu crawler chưa được khởi động
            Exception: Nếu có lỗi trong quá trình crawl
        """
        if not self._is_started:
            raise RuntimeError("Crawler chưa được khởi động. Gọi start() trước.")

        logger.info(f"Bắt đầu crawl URL: {url}")

        try:
            # Điều hướng đến trang
            await self.navigate_to(url, wait_until=wait_until, timeout=timeout)

            # Chờ cho selector cụ thể nếu có
            if self.wait_for_selector:
                logger.debug(f"Chờ selector: {self.wait_for_selector}")
                await self.wait_for_element(
                    self.wait_for_selector, timeout=self.wait_timeout
                )

            # Lấy HTML của trang
            html_content = await self.get_page_html()

            # Chụp screenshot nếu có yêu cầu
            if screenshot_path:
                await self.take_screenshot(screenshot_path)

            # Tạo kết quả
            result = CrawlResult(url=url, raw_html=html_content)

            navigable_links = await self.extract_navigable_links(html_content, url)
            result.navigable_links = navigable_links
            logger.info(f"👉 result: {result.model_dump_json(indent=2)}")

            # logger.info(
            #     f"Đã crawl thành công URL: {url}, HTML length: {len(html_content)}"
            # )
            return result

        except Exception as e:
            logger.error(f"Lỗi khi crawl URL {url}: {e}")
            raise

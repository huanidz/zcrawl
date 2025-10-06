"""
Module chứa class SimpleScraper - một scraper đơn giản kế thừa từ BaseScraper.
Cung cấp chức năng scrape cơ bản cho các trang web.
"""

from loguru import logger
import re
from bs4 import BeautifulSoup

from ..models.ScrapingResult import PageScrapeResult
from .BaseScraper import BaseScraper


class SimpleScraper(BaseScraper):
    """
    SimpleScraper - một scraper đơn giản kế thừa từ BaseScraper.
    Cung cấp chức năng scrape cơ bản cho các trang web.
    """

    def __init__(
        self,
        browser_config=None,
        remove_script: bool = False,
        remove_icons: bool = False,
    ):
        """
        Khởi tạo SimpleScraper.

        Args:
            browser_config: Cấu hình cho trình duyệt (từ BaseScraper)
            remove_script (bool): Có loại bỏ script tags khỏi HTML không (default: False)
            remove_icons (bool): Có loại bỏ SVG icons khỏi HTML không (default: False)
        """
        super().__init__(browser_config)
        self.remove_script = remove_script
        self.remove_icons = remove_icons

    async def scrape(self, url: str, **kwargs) -> PageScrapeResult:
        """
        Scrape một URL và trả về kết quả cơ bản.

        Args:
            url (str): URL để scrape
            **kwargs: Additional parameters:
                - wait_until (str): Điều kiện chờ ("domcontentloaded", "load", "networkidle")
                - timeout (int): Timeout tùy chỉnh
                - extract_links (bool): Có trích xuất liên kết không (default: True)
                - extract_images (bool): Có trích xuất hình ảnh không (default: True)
                - current_depth (int): Độ sâu hiện tại của liên kết (default: 0)

        Returns:
            PageScrapeResult: Kết quả scrape với HTML và các liên kết/hình ảnh trích xuất được
        """
        wait_until = kwargs.get("wait_until", "domcontentloaded")
        timeout = kwargs.get("timeout", 5000)
        current_depth = kwargs.get("current_depth", 0)

        logger.info(f"Bắt đầu scrape URL: {url}")

        try:
            # Điều hướng đến trang
            await self.navigate_to(url, wait_until=wait_until, timeout=timeout)

            # Lấy HTML của trang
            html = await self.get_page_html()
            # Phân tích HTML bằng BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            # Chuyển đổi BeautifulSoup object thành chuỗi HTML đã được định dạng
            formatted_html = str(soup)
            # Khởi tạo kết quả
            result = PageScrapeResult(url=url, raw_html=html, fit_html=formatted_html)

            # Trích xuất liên kết nếu được yêu cầu
            result.navigable_links = await self.extract_navigable_links(formatted_html, url, current_depth)

            result.images = await self.extract_images(formatted_html, url)

            return result

        except Exception as e:
            logger.error(f"Lỗi khi scrape URL {url}: {e}")
            raise

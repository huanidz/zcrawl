"""
Module chứa class SimpleScraper - một scraper đơn giản kế thừa từ BaseScraper.
Cung cấp chức năng scrape cơ bản cho các trang web.
"""

from loguru import logger

from ..models.ScrapingResult import PageScrapeResult
from .BaseScraper import BaseScraper


class SimpleScraper(BaseScraper):
    """
    SimpleScraper - một scraper đơn giản kế thừa từ BaseScraper.
    Cung cấp chức năng scrape cơ bản cho các trang web.
    """

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

        Returns:
            PageScrapeResult: Kết quả scrape với HTML và các liên kết/hình ảnh trích xuất được
        """
        wait_until = kwargs.get("wait_until", "domcontentloaded")
        timeout = kwargs.get("timeout", None)

        logger.info(f"Bắt đầu scrape URL: {url}")

        try:
            # Điều hướng đến trang
            await self.navigate_to(url, wait_until=wait_until, timeout=timeout)

            # Lấy HTML của trang
            html = await self.get_page_html()

            # Khởi tạo kết quả
            result = PageScrapeResult(url=url, raw_html=html)

            # Trích xuất liên kết nếu được yêu cầu
            logger.debug("Trích xuất liên kết từ trang")
            result.navigable_links = await self.extract_navigable_links(html, url)
            logger.info(f"Đã trích xuất {len(result.navigable_links)} liên kết")

            logger.debug("Trích xuất hình ảnh từ trang")
            result.images = await self.extract_images(html, url)
            logger.info(f"Đã trích xuất {len(result.images)} hình ảnh")

            logger.info(f"Hoàn thành scrape URL: {url}")
            return result

        except Exception as e:
            logger.error(f"Lỗi khi scrape URL {url}: {e}")
            raise

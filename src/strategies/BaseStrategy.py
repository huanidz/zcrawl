"""
Module chứa class BaseStrategy - class cơ bản cho tất cả các strategy.
Cung cấp interface chung cho các chiến lược crawl khác nhau.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from loguru import logger

from ..models.ScrapingResult import PageScrapeResult
from ..scrapers.BaseScraper import BaseCrawler


class BaseStrategy(ABC):
    """
    Class cơ bản cho tất cả các strategy.
    Cung cấp interface chung cho các chiến lược crawl khác nhau.
    """

    def __init__(self, crawler: BaseCrawler, **kwargs):
        """
        Khởi tạo BaseStrategy.

        Args:
            crawler (BaseCrawler): Instance của crawler để sử dụng
            **kwargs: Các tham số bổ sung cho strategy
        """
        self.crawler = crawler
        self.config = kwargs

    @abstractmethod
    async def run(self, url: str, **kwargs) -> PageScrapeResult:
        """
        Phương thức abstract để thực thi strategy.
        Phải được implement bởi các class con.

        Args:
            url (str): URL để crawl
            **kwargs: Additional parameters

        Returns:
            PageScrapeResult: Kết quả crawl
        """
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị config theo key.

        Args:
            key (str): Key của config
            default (Any): Giá trị mặc định nếu không tìm thấy

        Returns:
            Any: Giá trị config
        """
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """
        Đặt giá trị config.

        Args:
            key (str): Key của config
            value (Any): Giá trị cần đặt
        """
        self.config[key] = value

    def update_config(self, **kwargs) -> None:
        """
        Cập nhật nhiều config cùng lúc.

        Args:
            **kwargs: Các cặp key-value cần cập nhật
        """
        self.config.update(kwargs)

    async def validate_url(self, url: str) -> bool:
        """
        Kiểm tra URL có hợp lệ cho strategy này không.

        Args:
            url (str): URL cần kiểm tra

        Returns:
            bool: True nếu URL hợp lệ
        """
        # Implementation mặc định, có thể override ở class con
        return bool(url) and url.startswith(("http://", "https://"))

    async def prepare_crawl(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Chuẩn bị trước khi crawl.

        Args:
            url (str): URL sẽ crawl
            **kwargs: Additional parameters

        Returns:
            Dict[str, Any]: Các tham số đã được chuẩn bị
        """
        logger.debug(f"Chuẩn bị crawl URL: {url}")

        # Kết hợp config từ strategy và tham số truyền vào
        prepared_params = self.config.copy()
        prepared_params.update(kwargs)

        return prepared_params

    async def post_process(
        self, result: PageScrapeResult, **kwargs
    ) -> PageScrapeResult:
        """
        Xử lý sau khi crawl.

        Args:
            result (PageScrapeResult): Kết quả crawl
            **kwargs: Additional parameters

        Returns:
            PageScrapeResult: Kết quả sau khi xử lý
        """
        logger.debug(f"Hoàn thành crawl URL: {result.url}")
        return result

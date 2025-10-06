"""
Module chứa DFSCrawlingStrategy - chiến lược crawling theo chiều sâu (Depth-First Search).
Chiến lược này sẽ đi sâu vào một nhánh trước khi chuyển sang nhánh khác.
"""

from typing import List, Optional

from loguru import logger

from ..models.CrawlingResult import CrawlingResult
from .BaseStrategy import BaseStrategy


class DFSCrawlingStrategy(BaseStrategy):
    """
    Chiến lược crawling theo chiều sâu (Depth-First Search).
    Chiến lược này sẽ đi sâu vào một nhánh trước khi chuyển sang nhánh khác.
    """

    def __init__(
        self,
        scraper,
        max_depth: int = 3,
        max_pages: int = 100,
        allowed_domains: Optional[List[str]] = None,
        url_filter: Optional[callable] = None,
        respect_robots_txt: bool = True,
    ):
        """
        Khởi tạo DFSCrawlingStrategy.

        Args:
            scraper: Scraper instance để sử dụng
            max_depth (int): Độ sâu tối đa cho crawling
            max_pages (int): Số trang tối đa để crawl
            allowed_domains (Optional[List[str]]): Danh sách các domain được phép crawl
            url_filter (Optional[callable]): Hàm filter để kiểm tra URL có hợp lệ không
            respect_robots_txt (bool): Có tuân thủ robots.txt không
        """
        super().__init__(
            scraper=scraper,
            max_depth=max_depth,
            max_pages=max_pages,
            allowed_domains=allowed_domains,
            url_filter=url_filter,
            respect_robots_txt=respect_robots_txt,
        )

    async def crawl(self, start_url: str) -> CrawlingResult:
        """
        Thực hiện crawling theo chiến lược DFS.

        Args:
            start_url (str): URL bắt đầu crawling

        Returns:
            CrawlingResult: Kết quả crawling
        """
        # Reset trạng thái
        self._reset_state()
        self._is_running = True

        logger.info(f"Bắt đầu crawling DFS từ URL: {start_url}")

        # Tạo kết quả crawling
        result = self._create_crawling_result(start_url, "DFS")

        # Bắt đầu crawling từ URL gốc
        await self._dfs_crawl(start_url, result, 0)

        # Đánh dấu hoàn thành
        result.mark_completed()
        self._is_running = False

        logger.info(f"Hoàn thành crawling DFS. Tổng trang: {len(result.scraped_pages)}")

        return result

    async def _dfs_crawl(self, url: str, result: CrawlingResult, depth: int) -> None:
        """
        Thực hiện crawling đệ quy theo DFS.

        Args:
            url (str): URL hiện tại
            result (CrawlingResult): Kết quả crawling để cập nhật
            depth (int): Độ sâu hiện tại
        """
        # Kiểm tra điều kiện dừng
        if not self._should_continue_crawling() or not self._is_running:
            return

        # Cập nhật độ sâu hiện tại
        self._current_depth = max(self._current_depth, depth)

        # Scrape trang hiện tại
        page_result = await self._scrape_page(url, depth)
        if page_result is None:
            return

        # Thêm kết quả vào crawling result
        result.add_scraped_page(page_result)

        # Nếu đạt độ sâu tối đa, không crawl các liên kết con
        if depth >= self.max_depth:
            logger.debug(f"Đạt độ sâu tối đa ({self.max_depth}) tại URL: {url}")
            return

        # Trích xuất các liên kết từ trang
        links = self._extract_links(page_result)
        logger.debug(f"Tìm thấy {len(links)} liên kết từ {url}")

        # Crawl các liên kết theo DFS (đệ quy)
        for link in links:
            if not self._is_running or not self._should_continue_crawling():
                break

            await self._dfs_crawl(link, result, depth + 1)

"""
Module chứa BFSCrawlingStrategy - chiến lược crawling theo chiều rộng (Breadth-First Search).
Chiến lược này sẽ crawl tất cả các trang cùng độ sâu trước khi đi sâu hơn.
"""

import asyncio
from collections import deque
from typing import List, Optional, Set

from loguru import logger

from ..models.CrawlingResult import CrawlingResult
from .BaseStrategy import BaseStrategy


class BFSCrawlingStrategy(BaseStrategy):
    """
    Chiến lược crawling theo chiều rộng (Breadth-First Search).
    Chiến lược này sẽ crawl tất cả các trang cùng độ sâu trước khi đi sâu hơn.
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
        Khởi tạo BFSCrawlingStrategy.

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
        Thực hiện crawling theo chiến lược BFS.

        Args:
            start_url (str): URL bắt đầu crawling

        Returns:
            CrawlingResult: Kết quả crawling
        """
        # Reset trạng thái
        self._reset_state()
        self._is_running = True

        logger.info(f"Bắt đầu crawling BFS từ URL: {start_url}")

        # Tạo kết quả crawling
        result = self._create_crawling_result(start_url, "BFS")

        # Queue để lưu trữ (url, depth)
        queue = deque([(start_url, 0)])

        # Set để theo dõi các URL đã thêm vào queue
        queued_urls: Set[str] = {start_url}

        while queue and self._should_continue_crawling() and self._is_running:
            # Lấy URL và độ sâu từ queue
            url, depth = queue.popleft()
            queued_urls.discard(url)

            # Cập nhật độ sâu hiện tại
            self._current_depth = max(self._current_depth, depth)

            # Scrape trang hiện tại
            page_result = await self._scrape_page(url)
            if page_result is None:
                continue

            # Thêm kết quả vào crawling result
            result.add_scraped_page(page_result)

            # Nếu đạt độ sâu tối đa, không thêm các liên kết con vào queue
            if depth >= self.max_depth:
                logger.debug(f"Đạt độ sâu tối đa ({self.max_depth}) tại URL: {url}")
                continue

            # Trích xuất các liên kết từ trang
            links = self._extract_links(page_result)
            logger.debug(f"Tìm thấy {len(links)} liên kết từ {url}")

            # Thêm các liên kết vào queue với độ sâu + 1
            for link in links:
                if link not in self._visited_urls and link not in queued_urls:
                    queue.append((link, depth + 1))
                    queued_urls.add(link)

        # Đánh dấu hoàn thành
        result.mark_completed()
        self._is_running = False

        logger.info(f"Hoàn thành crawling BFS. Tổng trang: {len(result.scraped_pages)}")

        return result

    async def _bfs_level_crawl(
        self, urls: List[str], depth: int, result: CrawlingResult
    ) -> List[str]:
        """
        Crawl tất cả các trang ở một độ sâu nhất định và trả về các liên kết cho độ sâu tiếp theo.

        Args:
            urls (List[str]): Danh sách các URL ở độ sâu hiện tại
            depth (int): Độ sâu hiện tại
            result (CrawlingResult): Kết quả crawling để cập nhật

        Returns:
            List[str]: Danh sách các URL cho độ sâu tiếp theo
        """
        next_level_urls = []

        # Tạo các task để crawl song song
        tasks = []
        for url in urls:
            if self._should_continue_crawling() and self._is_running:
                tasks.append(self._scrape_and_extract_links(url, result, depth))

        # Chờ tất cả các tasks hoàn thành
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Xử lý kết quả
            for i, task_result in enumerate(results):
                if isinstance(task_result, Exception):
                    logger.error(f"Lỗi khi crawl {urls[i]}: {task_result}")
                elif task_result:
                    next_level_urls.extend(task_result)

        return next_level_urls

    async def _scrape_and_extract_links(
        self, url: str, result: CrawlingResult, depth: int
    ) -> List[str]:
        """
        Scrape một trang và trích xuất các liên kết.

        Args:
            url (str): URL để scrape
            result (CrawlingResult): Kết quả crawling để cập nhật
            depth (int): Độ sâu hiện tại

        Returns:
            List[str]: Danh sách các liên kết tìm thấy
        """
        # Scrape trang hiện tại
        page_result = await self._scrape_page(url)
        if page_result is None:
            return []

        # Thêm kết quả vào crawling result
        result.add_scraped_page(page_result)

        # Nếu đạt độ sâu tối đa, không trích xuất liên kết
        if depth >= self.max_depth:
            return []

        # Trích xuất các liên kết từ trang
        links = self._extract_links(page_result)
        logger.debug(f"Tìm thấy {len(links)} liên kết từ {url}")

        return links

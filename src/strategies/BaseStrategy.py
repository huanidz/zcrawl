"""
Module chứa BaseStrategy - class cơ bản cho tất cả các crawling strategies.
Cung cấp các chức năng chung và interface cho các chiến lược crawling khác nhau.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Set

from loguru import logger

from ..models.CrawlingResult import CrawlingResult
from ..models.ScrapingResult import PageScrapeResult
from ..scrapers.BaseScraper import BaseScraper


class BaseStrategy(ABC):
    """
    Class cơ bản cho tất cả các crawling strategies.
    Cung cấp các chức năng chung và interface cho các chiến lược crawling khác nhau.
    """

    def __init__(
        self,
        scraper: BaseScraper,
        max_depth: int = 3,
        max_pages: int = 100,
        allowed_domains: Optional[List[str]] = None,
        url_filter: Optional[Callable[[str], bool]] = None,
        respect_robots_txt: bool = True,
    ):
        """
        Khởi tạo BaseStrategy.

        Args:
            scraper (BaseScraper): Scraper instance để sử dụng
            max_depth (int): Độ sâu tối đa cho crawling
            max_pages (int): Số trang tối đa để crawl
            allowed_domains (Optional[List[str]]): Danh sách các domain được phép crawl
            url_filter (Optional[Callable[[str], bool]]): Hàm filter để kiểm tra URL có hợp lệ không
            respect_robots_txt (bool): Có tuân thủ robots.txt không
        """
        self.scraper = scraper
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.allowed_domains = allowed_domains or []
        self.url_filter = url_filter
        self.respect_robots_txt = respect_robots_txt

        # Internal state
        self._visited_urls: Set[str] = set()
        self._failed_urls: Set[str] = set()
        self._current_depth = 0
        self._pages_crawled = 0
        self._is_running = False

    @abstractmethod
    async def crawl(self, start_url: str) -> CrawlingResult:
        """
        Phương thức abstract để thực hiện crawling.
        Phải được implement bởi các class con.

        Args:
            start_url (str): URL bắt đầu crawling

        Returns:
            CrawlingResult: Kết quả crawling
        """
        pass

    async def _scrape_page(self, url: str, current_depth: int = 0) -> Optional[PageScrapeResult]:
        """
        Scrape một trang web sử dụng scraper.

        Args:
            url (str): URL để scrape
            current_depth (int): Độ sâu hiện tại của trang

        Returns:
            Optional[PageScrapeResult]: Kết quả scrape, None nếu thất bại
        """
        try:
            logger.debug(f"Đang scrape trang: {url} ở độ sâu {current_depth}")
            result = await self.scraper.scrape(url, current_depth=current_depth)
            self._visited_urls.add(url)
            self._pages_crawled += 1
            logger.debug(f"Đã scrape thành công trang: {url}")
            return result
        except Exception as e:
            logger.error(f"Lỗi khi scrape trang {url}: {e}")
            self._failed_urls.add(url)
            return None

    def _extract_links(self, page_result: PageScrapeResult) -> List[str]:
        """
        Trích xuất các liên kết từ kết quả scrape.

        Args:
            page_result (PageScrapeResult): Kết quả scrape của trang

        Returns:
            List[str]: Danh sách các liên kết đã được lọc
        """
        links = []

        for link in page_result.navigable_links:
            url = str(link.url)
            # Chỉ thêm liên kết nếu chưa được visit
            if url not in self._visited_urls:
                links.append(url)

        return links

    def _should_continue_crawling(self) -> bool:
        """
        Kiểm tra xem có nên tiếp tục crawling không.

        Returns:
            bool: True nếu nên tiếp tục
        """
        if self._pages_crawled >= self.max_pages:
            logger.info(f"Đạt giới hạn số trang ({self.max_pages})")
            return False

        return True

    def _reset_state(self) -> None:
        """
        Reset trạng thái internal cho một lần crawling mới.
        """
        self._visited_urls.clear()
        self._failed_urls.clear()
        self._current_depth = 0
        self._pages_crawled = 0
        self._is_running = False

    def _create_crawling_result(
        self, start_url: str, strategy_name: str
    ) -> CrawlingResult:
        """
        Tạo CrawlingResult từ trạng thái hiện tại.

        Args:
            start_url (str): URL bắt đầu
            strategy_name (str): Tên strategy

        Returns:
            CrawlingResult: Kết quả crawling
        """
        result = CrawlingResult(
            start_url=start_url,
            max_depth=self._current_depth,
            strategy=strategy_name,
            visited_urls=list(self._visited_urls),
            failed_urls=list(self._failed_urls),
        )

        return result

    async def stop(self) -> None:
        """
        Dừng quá trình crawling.
        """
        self._is_running = False
        logger.info("Đã yêu cầu dừng crawling")

    @property
    def is_running(self) -> bool:
        """
        Kiểm tra xem strategy đang chạy không.

        Returns:
            bool: True nếu đang chạy
        """
        return self._is_running

    @property
    def visited_urls(self) -> Set[str]:
        """
        Lấy danh sách các URL đã visit.

        Returns:
            Set[str]: Set các URL đã visit
        """
        return self._visited_urls.copy()

    @property
    def failed_urls(self) -> Set[str]:
        """
        Lấy danh sách các URL thất bại.

        Returns:
            Set[str]: Set các URL thất bại
        """
        return self._failed_urls.copy()

    @property
    def pages_crawled(self) -> int:
        """
        Lấy số trang đã crawl.

        Returns:
            int: Số trang đã crawl
        """
        return self._pages_crawled

    @property
    def current_depth(self) -> int:
        """
        Lấy độ sâu hiện tại.

        Returns:
            int: Độ sâu hiện tại
        """
        return self._current_depth

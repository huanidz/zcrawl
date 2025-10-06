from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .ScrapingResult import PageScrapeResult


class CrawlingResult(BaseModel):
    """
    Model đại diện cho kết quả của một quá trình crawling.
    Chứa thông tin tổng quan và danh sách các trang đã được crawl.
    """

    start_url: str = Field(..., description="URL bắt đầu crawling")
    start_time: datetime = Field(
        default_factory=datetime.now, description="Thời gian bắt đầu crawling"
    )
    end_time: Optional[datetime] = Field(
        None, description="Thời gian kết thúc crawling"
    )
    total_pages: int = Field(default=0, description="Tổng số trang đã crawl")
    max_depth: int = Field(default=1, description="Độ sâu tối đa đã đạt được")
    strategy: str = Field(..., description="Strategy đã sử dụng (DFS/BFS)")
    scraped_pages: List[PageScrapeResult] = Field(
        default_factory=list, description="Danh sách các trang đã scrape"
    )
    visited_urls: List[str] = Field(
        default_factory=list, description="Danh sách các URL đã visit"
    )
    failed_urls: List[str] = Field(
        default_factory=list, description="Danh sách các URL thất bại"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata bổ sung"
    )

    @property
    def duration(self) -> Optional[float]:
        """
        Tính toán thời gian crawling đã thực hiện (giây).

        Returns:
            Optional[float]: Thời gian crawling trong giây, None nếu chưa kết thúc
        """
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        """
        Tính toán tỷ lệ thành công của crawling.

        Returns:
            float: Tỷ lệ thành công (0-1)
        """
        total_attempts = len(self.visited_urls) + len(self.failed_urls)
        if total_attempts == 0:
            return 0.0
        return len(self.visited_urls) / total_attempts

    def add_scraped_page(self, page_result: PageScrapeResult) -> None:
        """
        Thêm một trang đã scrape vào kết quả.

        Args:
            page_result (PageScrapeResult): Kết quả scrape của trang
        """
        self.scraped_pages.append(page_result)
        self.visited_urls.append(page_result.url)
        self.total_pages = len(self.scraped_pages)

    def add_failed_url(self, url: str) -> None:
        """
        Thêm một URL thất bại vào danh sách.

        Args:
            url (str): URL thất bại
        """
        self.failed_urls.append(url)

    def mark_completed(self) -> None:
        """
        Đánh dấu quá trình crawling đã hoàn thành.
        """
        self.end_time = datetime.now()

    def get_all_links(self) -> List[str]:
        """
        Lấy tất cả các liên kết từ tất cả các trang đã scrape.

        Returns:
            List[str]: Danh sách tất cả các liên kết
        """
        all_links = []
        for page in self.scraped_pages:
            for link in page.navigable_links:
                all_links.append(str(link.url))
        return all_links

    def get_all_images(self) -> List[str]:
        """
        Lấy tất cả các URL hình ảnh từ tất cả các trang đã scrape.

        Returns:
            List[str]: Danh sách tất cả các URL hình ảnh
        """
        all_images = []
        for page in self.scraped_pages:
            for image in page.images:
                all_images.append(str(image.url))
        return all_images

    class Config:
        arbitrary_types_allowed = True

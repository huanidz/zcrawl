"""
Module chứa AsyncRunner - class để thực thi crawling sessions trên một browser.
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from loguru import logger

from ..browser.browser_config import BrowserConfig, ConfigType, get_browser_config
from ..models.CrawlingResult import CrawlingResult
from ..scrapers.BaseScraper import BaseScraper
from ..scrapers.SimpleScraper import SimpleScraper
from ..strategies.BaseStrategy import BaseStrategy


class AsyncRunner:
    """
    Class để thực thi crawling sessions trên một browser.
    Quản lý vòng đời của scraper và strategy để thực hiện crawling.
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        scraper: Optional[BaseScraper] = None,
        browser_config: Optional[BrowserConfig] = None,
    ):
        """
        Khởi tạo AsyncRunner.

        Args:
            strategy (BaseStrategy): Strategy để sử dụng cho crawling
            scraper (Optional[BaseScraper]): Scraper instance, sẽ tạo SimpleScraper nếu không cung cấp
            browser_config (Optional[BrowserConfig]): Cấu hình cho browser
            auto_start (bool): Tự động khởi động scraper sau khi tạo
        """
        self.strategy = strategy
        self.browser_config = browser_config or get_browser_config(ConfigType.DEFAULT)

        # Tạo scraper nếu không cung cấp
        if scraper is None:
            self.scraper = SimpleScraper(
                browser_config=self.browser_config, auto_start=False
            )
        else:
            self.scraper = scraper

        # Internal state
        self._is_started = False
        self._current_result: Optional[CrawlingResult] = None
        self._progress_callback: Optional[Callable[[CrawlingResult], None]] = None
        self._startup_task = None

    async def start(self) -> None:
        """
        Khởi động AsyncRunner và scraper.
        """
        if self._is_started:
            return

        try:
            await self.scraper.start()
            self._is_started = True
            logger.info("AsyncRunner đã được khởi động")
        except Exception as e:
            logger.error(f"Lỗi khi khởi động AsyncRunner: {e}")
            raise

    async def stop(self) -> None:
        """
        Dừng AsyncRunner và scraper.
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

            # Dừng strategy nếu đang chạy
            if hasattr(self.strategy, "stop"):
                await self.strategy.stop()

            # Dừng scraper
            await self.scraper.stop()
            self._is_started = False
            logger.info("AsyncRunner đã được dừng")
        except Exception as e:
            logger.error(f"Lỗi khi dừng AsyncRunner: {e}")
            raise

    async def run(self, start_url: str, **kwargs) -> CrawlingResult:
        """
        Thực thi crawling từ URL bắt đầu.

        Args:
            start_url (str): URL bắt đầu crawling
            **kwargs: Additional parameters cho strategy

        Returns:
            CrawlingResult: Kết quả crawling
        """
        if not self._is_started:
            await self.start()

        logger.info(f"Bắt đầu crawling với AsyncRunner từ URL: {start_url}")

        try:
            # Gán scraper vào strategy nếu chưa có
            if self.strategy.scraper != self.scraper:
                self.strategy.scraper = self.scraper

            # Thực thi crawling
            self._current_result = await self.strategy.crawl(start_url, **kwargs)

            # Gọi progress callback nếu có
            if self._progress_callback:
                self._progress_callback(self._current_result)

            logger.info(
                f"Hoàn thành crawling. Tổng trang: {len(self._current_result.scraped_pages)}"
            )

            return self._current_result
        except Exception as e:
            logger.error(f"Lỗi khi thực thi crawling: {e}")
            raise

    async def run_with_progress(
        self,
        start_url: str,
        progress_callback: Callable[[CrawlingResult], None],
        **kwargs,
    ) -> CrawlingResult:
        """
        Thực thi crawling với callback để theo dõi tiến trình.

        Args:
            start_url (str): URL bắt đầu crawling
            progress_callback (Callable[[CrawlingResult], None]): Callback được gọi khi có cập nhật
            **kwargs: Additional parameters cho strategy

        Returns:
            CrawlingResult: Kết quả crawling
        """
        self._progress_callback = progress_callback
        return await self.run(start_url, **kwargs)

    def set_progress_callback(self, callback: Callable[[CrawlingResult], None]) -> None:
        """
        Thiết lập callback để theo dõi tiến trình.

        Args:
            callback (Callable[[CrawlingResult], None]): Callback được gọi khi có cập nhật
        """
        self._progress_callback = callback

    def get_current_result(self) -> Optional[CrawlingResult]:
        """
        Lấy kết quả crawling hiện tại.

        Returns:
            Optional[CrawlingResult]: Kết quả crawling, None nếu chưa có
        """
        return self._current_result

    def is_running(self) -> bool:
        """
        Kiểm tra xem AsyncRunner đang chạy không.

        Returns:
            bool: True nếu đang chạy
        """
        return self._is_started and (
            self.strategy.is_running if hasattr(self.strategy, "is_running") else False
        )

    async def restart(self) -> None:
        """
        Khởi động lại AsyncRunner.
        """
        await self.stop()
        await self.start()

    def get_stats(self) -> Dict[str, Any]:
        """
        Lấy thông tin thống kê về runner.

        Returns:
            Dict[str, Any]: Thông tin thống kê
        """
        stats = {
            "is_started": self._is_started,
            "strategy": type(self.strategy).__name__,
            "scraper": type(self.scraper).__name__,
            "browser_config": {
                "headless": self.browser_config.headless,
                "viewport": {
                    "width": self.browser_config.viewport_width,
                    "height": self.browser_config.viewport_height,
                },
            },
        }

        if self._current_result:
            stats["current_result"] = {
                "total_pages": self._current_result.total_pages,
                "visited_urls": len(self._current_result.visited_urls),
                "failed_urls": len(self._current_result.failed_urls),
                "duration": self._current_result.duration,
                "success_rate": self._current_result.success_rate,
            }

        return stats

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

    async def save_result_to_json(self, file_path: str) -> None:
        """
        Lưu kết quả crawling hiện tại ra file JSON.
        
        Args:
            file_path (str): Đường dẫn đến file JSON để lưu kết quả
        """
        if not self._current_result:
            logger.warning("Không có kết quả nào để lưu")
            return
        
        try:
            # Chuyển đổi kết quả thành dictionary có thể serialize
            result_dict = self._current_result.model_dump()
            
            # Tạo thư mục nếu chưa tồn tại
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Ghi kết quả ra file JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Đã lưu kết quả crawling vào file: {file_path}")
            
        except Exception as e:
            logger.error(f"Lỗi khi lưu kết quả ra file JSON: {e}")
            raise

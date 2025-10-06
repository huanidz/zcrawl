"""
Module chứa AsyncManyRunner - class để thực thi crawling sessions trên nhiều browser instances.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from loguru import logger

from ..browser.browser_config import BrowserConfig, ConfigType, get_browser_config
from ..models.CrawlingResult import CrawlingResult
from ..scrapers.BaseScraper import BaseScraper
from ..scrapers.SimpleScraper import SimpleScraper
from ..strategies.BaseStrategy import BaseStrategy
from .AsyncRunner import AsyncRunner


class AsyncManyRunner:
    """
    Class để thực thi crawling sessions trên nhiều browser instances.
    Hỗ trợ crawling song song từ nhiều URL bắt đầu.
    """

    def __init__(
        self,
        strategy_factory: Callable[[], BaseStrategy],
        scraper_factory: Optional[Callable[[], BaseScraper]] = None,
        browser_config: Optional[BrowserConfig] = None,
        max_concurrent: int = 3,
        auto_start: bool = True,
    ):
        """
        Khởi tạo AsyncManyRunner.

        Args:
            strategy_factory (Callable[[], BaseStrategy]): Factory function để tạo strategy instances
            scraper_factory (Optional[Callable[[], BaseScraper]]): Factory function để tạo scraper instances
            browser_config (Optional[BrowserConfig]): Cấu hình cho browser
            max_concurrent (int): Số lượng concurrent crawling tối đa
            auto_start (bool): Tự động khởi động các runners sau khi tạo
        """
        self.strategy_factory = strategy_factory
        self.browser_config = browser_config or get_browser_config(ConfigType.DEFAULT)
        self.max_concurrent = max_concurrent

        # Tạo scraper factory nếu không cung cấp
        if scraper_factory is None:

            def default_scraper_factory():
                return SimpleScraper(
                    browser_config=self.browser_config, auto_start=False
                )

            self.scraper_factory = default_scraper_factory
        else:
            self.scraper_factory = scraper_factory

        # Internal state
        self._runners: List[AsyncRunner] = []
        self._is_started = False
        self._results: List[CrawlingResult] = []
        self._progress_callback: Optional[Callable[[List[CrawlingResult]], None]] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)

        if auto_start:
            asyncio.create_task(self.start())

    async def start(self) -> None:
        """
        Khởi động AsyncManyRunner và tất cả runners.
        """
        if self._is_started:
            return

        try:
            # Khởi động tất cả runners
            for runner in self._runners:
                await runner.start()

            self._is_started = True
            logger.info(
                f"AsyncManyRunner đã được khởi động với {len(self._runners)} runners"
            )
        except Exception as e:
            logger.error(f"Lỗi khi khởi động AsyncManyRunner: {e}")
            raise

    async def stop(self) -> None:
        """
        Dừng AsyncManyRunner và tất cả runners.
        """
        if not self._is_started:
            return

        try:
            # Dừng tất cả runners
            tasks = [runner.stop() for runner in self._runners]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self._is_started = False
            logger.info("AsyncManyRunner đã được dừng")
        except Exception as e:
            logger.error(f"Lỗi khi dừng AsyncManyRunner: {e}")
            raise

    async def run(self, start_urls: List[str], **kwargs) -> List[CrawlingResult]:
        """
        Thực thi crawling từ nhiều URL bắt đầu.

        Args:
            start_urls (List[str]): Danh sách URL bắt đầu crawling
            **kwargs: Additional parameters cho strategy

        Returns:
            List[CrawlingResult]: Danh sách kết quả crawling
        """
        if not self._is_started:
            await self.start()

        logger.info(f"Bắt đầu crawling với AsyncManyRunner từ {len(start_urls)} URLs")

        # Reset kết quả
        self._results = []

        try:
            # Tạo runners cho mỗi URL
            tasks = []
            for url in start_urls:
                task = self._run_single_crawl(url, **kwargs)
                tasks.append(task)

            # Chờ tất cả tasks hoàn thành
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Xử lý kết quả
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Lỗi khi crawl {start_urls[i]}: {result}")
                else:
                    self._results.append(result)

            # Gọi progress callback nếu có
            if self._progress_callback:
                self._progress_callback(self._results)

            logger.info(
                f"Hoàn thành crawling. Tổng trang: {sum(len(r.scraped_pages) for r in self._results)}"
            )

            return self._results
        except Exception as e:
            logger.error(f"Lỗi khi thực thi crawling: {e}")
            raise

    async def _run_single_crawl(self, start_url: str, **kwargs) -> CrawlingResult:
        """
        Thực thi crawling cho một URL với semaphore để giới hạn concurrent.

        Args:
            start_url (str): URL bắt đầu crawling
            **kwargs: Additional parameters cho strategy

        Returns:
            CrawlingResult: Kết quả crawling
        """
        async with self._semaphore:
            # Tạo strategy và scraper mới cho mỗi URL
            strategy = self.strategy_factory()
            scraper = self.scraper_factory()

            # Tạo runner
            runner = AsyncRunner(
                strategy=strategy,
                scraper=scraper,
                browser_config=self.browser_config,
                auto_start=False,
            )

            # Thêm vào danh sách runners
            self._runners.append(runner)

            try:
                # Khởi động runner
                await runner.start()

                # Thực thi crawling
                result = await runner.run(start_url, **kwargs)

                # Gọi progress callback nếu có
                if self._progress_callback:
                    self._progress_callback(self._results + [result])

                return result
            finally:
                # Dừng và xóa runner
                await runner.stop()
                self._runners.remove(runner)

    async def run_with_progress(
        self,
        start_urls: List[str],
        progress_callback: Callable[[List[CrawlingResult]], None],
        **kwargs,
    ) -> List[CrawlingResult]:
        """
        Thực thi crawling với callback để theo dõi tiến trình.

        Args:
            start_urls (List[str]): Danh sách URL bắt đầu crawling
            progress_callback (Callable[[List[CrawlingResult]], None]): Callback được gọi khi có cập nhật
            **kwargs: Additional parameters cho strategy

        Returns:
            List[CrawlingResult]: Danh sách kết quả crawling
        """
        self._progress_callback = progress_callback
        return await self.run(start_urls, **kwargs)

    def set_progress_callback(
        self, callback: Callable[[List[CrawlingResult]], None]
    ) -> None:
        """
        Thiết lập callback để theo dõi tiến trình.

        Args:
            callback (Callable[[List[CrawlingResult]], None]): Callback được gọi khi có cập nhật
        """
        self._progress_callback = callback

    def get_current_results(self) -> List[CrawlingResult]:
        """
        Lấy kết quả crawling hiện tại.

        Returns:
            List[CrawlingResult]: Danh sách kết quả crawling
        """
        return self._results.copy()

    def is_running(self) -> bool:
        """
        Kiểm tra xem AsyncManyRunner đang chạy không.

        Returns:
            bool: True nếu đang chạy
        """
        return self._is_started and any(runner.is_running() for runner in self._runners)

    async def restart(self) -> None:
        """
        Khởi động lại AsyncManyRunner.
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
            "max_concurrent": self.max_concurrent,
            "active_runners": len(self._runners),
            "strategy_factory": self.strategy_factory.__name__
            if hasattr(self.strategy_factory, "__name__")
            else str(self.strategy_factory),
            "scraper_factory": self.scraper_factory.__name__
            if hasattr(self.scraper_factory, "__name__")
            else str(self.scraper_factory),
            "browser_config": {
                "headless": self.browser_config.headless,
                "viewport": {
                    "width": self.browser_config.viewport_width,
                    "height": self.browser_config.viewport_height,
                },
            },
        }

        if self._results:
            total_pages = sum(len(r.scraped_pages) for r in self._results)
            total_visited = sum(len(r.visited_urls) for r in self._results)
            total_failed = sum(len(r.failed_urls) for r in self._results)

            stats["results"] = {
                "total_results": len(self._results),
                "total_pages": total_pages,
                "total_visited_urls": total_visited,
                "total_failed_urls": total_failed,
                "average_success_rate": sum(r.success_rate for r in self._results)
                / len(self._results)
                if self._results
                else 0,
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

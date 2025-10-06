import asyncio
import sys
from typing import List

from loguru import logger

from src.scrapers import SimpleScraper
from src.strategies import DFSCrawlingStrategy, BFSCrawlingStrategy
from src.runner import AsyncRunner, AsyncManyRunner
from src.utils.installation import ensure_chromium_installed


async def demo_async_runner():
    """
    Demo sử dụng AsyncRunner với một URL.
    """
    print("\n" + "="*50)
    print("DEMO ASYNC RUNNER")
    print("="*50)
    
    try:
        # Tạo scraper
        scraper = SimpleScraper(auto_start=False)
        
        # Tạo DFS strategy
        dfs_strategy = DFSCrawlingStrategy(
            scraper=scraper,
            max_depth=2,
            max_pages=5
        )
        
        # Tạo AsyncRunner
        async with AsyncRunner(strategy=dfs_strategy, scraper=scraper) as runner:
            # Crawl một URL
            SAMPLE_URL = "https://vnexpress.net/ong-chu-chatgpt-tiet-lo-cong-viec-se-lam-neu-bi-ai-thay-the-4947310.html"
            print(f"Đang crawl với AsyncRunner (DFS strategy): {SAMPLE_URL}")
            
            # Thực thi crawling
            result = await runner.run(SAMPLE_URL)
            
            # In kết quả
            print(f"✅ Hoàn thành crawling!")
            print(f"📄 Tổng số trang: {result.total_pages}")
            print(f"🔗 Tổng số liên kết: {len(result.get_all_links())}")
            print(f"🖼️ Tổng số hình ảnh: {len(result.get_all_images())}")
            print(f"⏱️ Thời gian thực hiện: {result.duration:.2f} giây")
            print(f"📈 Tỷ lệ thành công: {result.success_rate:.2%}")
            
            # In thống kê từ runner
            stats = runner.get_stats()
            print(f"📊 Thống kê runner: {stats}")
            
    except Exception as e:
        logger.error(f"Lỗi trong demo AsyncRunner: {e}")


async def demo_async_many_runner():
    """
    Demo sử dụng AsyncManyRunner với nhiều URLs.
    """
    print("\n" + "="*50)
    print("DEMO ASYNC MANY RUNNER")
    print("="*50)
    
    try:
        # URLs để crawl
        urls = [
            "https://vnexpress.net/",
            "https://tuoitre.vn/",
            "https://thanhnien.vn/"
        ]
        
        # Tạo strategy factory
        def bfs_strategy_factory():
            scraper = SimpleScraper(auto_start=False)
            return BFSCrawlingStrategy(
                scraper=scraper,
                max_depth=1,
                max_pages=3
            )
        
        # Tạo AsyncManyRunner
        async with AsyncManyRunner(
            strategy_factory=bfs_strategy_factory,
            max_concurrent=2
        ) as runner:
            print(f"Đang crawl {len(urls)} URLs với AsyncManyRunner (BFS strategy)...")
            
            # Progress callback
            def progress_callback(results):
                completed = len(results)
                total_pages = sum(len(r.scraped_pages) for r in results)
                print(f"📈 Tiến trình: {completed}/{len(urls)} URLs hoàn thành, {total_pages} trang đã crawl")
            
            # Thực thi crawling với progress callback
            results = await runner.run_with_progress(urls, progress_callback=progress_callback)
            
            # In kết quả tổng hợp
            print(f"\n✅ Hoàn thành crawling tất cả URLs!")
            total_pages = sum(len(r.scraped_pages) for r in results)
            total_links = sum(len(r.get_all_links()) for r in results)
            total_images = sum(len(r.get_all_images()) for r in results)
            total_duration = sum(r.duration or 0 for r in results)
            avg_success_rate = sum(r.success_rate for r in results) / len(results) if results else 0
            
            print(f"📄 Tổng số trang: {total_pages}")
            print(f"🔗 Tổng số liên kết: {total_links}")
            print(f"🖼️ Tổng số hình ảnh: {total_images}")
            print(f"⏱️ Tổng thời gian: {total_duration:.2f} giây")
            print(f"📈 Tỷ lệ thành công trung bình: {avg_success_rate:.2%}")
            
            # In thống kê từ runner
            stats = runner.get_stats()
            print(f"📊 Thống kê runner: {stats}")
            
    except Exception as e:
        logger.error(f"Lỗi trong demo AsyncManyRunner: {e}")


async def main():
    """
    Main function that ensures Chromium is installed and then performs crawling operations.
    """
    print("Starting web crawler...")
    print("Chromium driver is ready.")
    
    # Demo AsyncRunner
    await demo_async_runner()
    
    # Demo AsyncManyRunner
    # await demo_async_many_runner()
    
    print("\n" + "="*50)
    print("HOÀN TẤT TẤT CẢ DEMOS")
    print("="*50)


if __name__ == "__main__":
    # Ensure Chromium is installed
    if not ensure_chromium_installed():
        print("Failed to install Chromium. Exiting...")
        sys.exit(1)

    asyncio.run(main())

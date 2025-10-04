import asyncio
import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawlers.SinglePageCrawler import SinglePageCrawler
from src.utils.installation import ensure_chromium_installed


async def main():
    """
    Main function that ensures Chromium is installed and then performs crawling operations.
    """
    print("Starting web crawler...")

    # Ensure Chromium is installed
    # if not ensure_chromium_installed():
    #     print("Failed to install Chromium. Exiting...")
    #     sys.exit(1)

    print("Chromium driver is ready.")

    # Tạo SinglePageCrawler instance
    crawler = SinglePageCrawler(auto_start=False)

    try:
        # Crawl example.com
        print("Đang crawl example.com...")
        await crawler.start()
        result = await crawler.crawl("https://example.com")

        # In kết quả
        print(f"URL: {result.url}")
        print(f"Độ dài HTML: {len(result.raw_html)} ký tự")
        print(f"Nội dung HTML (500 ký tự đầu tiên):\n{result.raw_html[:500]}...")

    except Exception as e:
        print(f"Lỗi khi crawl: {e}")
    finally:
        # Dừng crawler
        await crawler.stop()
        print("Crawler đã dừng.")


if __name__ == "__main__":
    asyncio.run(main())

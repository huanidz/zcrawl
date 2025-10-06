import asyncio
import os
import sys

# Add the project root directory to the Python path
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from loguru import logger

from src.scrapers import SimpleScraper
from src.utils.installation import ensure_chromium_installed


async def main():
    """
    Main function that ensures Chromium is installed and then performs crawling operations.
    """
    print("Starting web crawler...")

    print("Chromium driver is ready.")

    # Tạo SinglePageCrawler instance
    scraper = SimpleScraper(auto_start=False)

    try:
        SAMPLE_URL = "https://vnexpress.net/can-bo-cong-chuc-khong-dap-ung-nhiem-vu-se-bi-cho-nghi-4947205.html"
        print(f"Đang crawl {SAMPLE_URL}...")
        await scraper.start()
        result = await scraper.scrape(SAMPLE_URL)
        logger.info(f"👉 result: {result.model_dump_json(indent=2)}")

        # In kết quả
        print(f"URL: {result.url}")
        print(f"Độ dài HTML: {len(result.raw_html)} ký tự")
        print(f"Nội dung HTML (500 ký tự đầu tiên):\n{result.raw_html[:500]}...")

    except Exception as e:
        print(f"Lỗi khi crawl: {e}")
    finally:
        # Dừng scraper
        await scraper.stop()
        print("Crawler đã dừng.")


if __name__ == "__main__":
    # Ensure Chromium is installed
    if not ensure_chromium_installed():
        print("Failed to install Chromium. Exiting...")
        sys.exit(1)

    asyncio.run(main())

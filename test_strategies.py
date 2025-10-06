"""
Test script để kiểm tra các thay đổi trong crawling strategies.
"""

import asyncio
from src.scrapers import SimpleScraper
from src.strategies import DFSCrawlingStrategy, BFSCrawlingStrategy


async def test_bfs_strategy():
    """
    Test BFS strategy với max_depth=2 để đảm bảo nó crawl tất cả links trong phạm vi max_depth.
    """
    print("\n" + "="*50)
    print("TEST BFS STRATEGY")
    print("="*50)
    
    try:
        # Tạo scraper
        scraper = SimpleScraper()
        await scraper.start()
        
        # Tạo BFS strategy với max_depth=2 và max_pages=10
        bfs_strategy = BFSCrawlingStrategy(
            scraper=scraper,
            max_depth=2,
            max_pages=10,
            respect_robots_txt=False
        )
        
        # Crawl một URL có nhiều links
        SAMPLE_URL = "https://example.com/"
        print(f"Đang crawl với BFS strategy: {SAMPLE_URL}")
        print(f"Max depth: {bfs_strategy.max_depth}, Max pages: {bfs_strategy.max_pages}")
        
        # Thực thi crawling
        result = await bfs_strategy.crawl(SAMPLE_URL)
        
        # In kết quả
        print(f"✅ Hoàn thành crawling BFS!")
        print(f"📄 Tổng số trang đã crawl: {len(result.scraped_pages)}")
        print(f"🔗 Tổng số liên kết tìm thấy: {len(result.get_all_links())}")
        print(f"🖼️ Tổng số hình ảnh: {len(result.get_all_images())}")
        print(f"⏱️ Thời gian thực hiện: {result.duration:.2f} giây" if result.duration else "⏱️ Thời gian thực hiện: N/A")
        print(f"📈 Tỷ lệ thành công: {result.success_rate:.2%}")
        
        # In danh sách các URL đã crawl
        print("\n📋 Danh sách các URL đã crawl:")
        for i, page in enumerate(result.scraped_pages):
            print(f"  {i+1}. {page.url}")
        
        return result
        
    except Exception as e:
        print(f"❌ Lỗi trong test BFS strategy: {e}")
        return None


async def test_dfs_strategy():
    """
    Test DFS strategy với max_depth=2 để đảm bảo nó crawl tất cả links trong phạm vi max_depth.
    """
    print("\n" + "="*50)
    print("TEST DFS STRATEGY")
    print("="*50)
    
    try:
        # Tạo scraper
        scraper = SimpleScraper()
        await scraper.start()
        
        # Tạo DFS strategy với max_depth=2 và max_pages=10
        dfs_strategy = DFSCrawlingStrategy(
            scraper=scraper,
            max_depth=2,
            max_pages=10,
            respect_robots_txt=False
        )
        
        # Crawl một URL có nhiều links
        SAMPLE_URL = "https://example.com/"
        print(f"Đang crawl với DFS strategy: {SAMPLE_URL}")
        print(f"Max depth: {dfs_strategy.max_depth}, Max pages: {dfs_strategy.max_pages}")
        
        # Thực thi crawling
        result = await dfs_strategy.crawl(SAMPLE_URL)
        
        # In kết quả
        print(f"✅ Hoàn thành crawling DFS!")
        print(f"📄 Tổng số trang đã crawl: {len(result.scraped_pages)}")
        print(f"🔗 Tổng số liên kết tìm thấy: {len(result.get_all_links())}")
        print(f"🖼️ Tổng số hình ảnh: {len(result.get_all_images())}")
        print(f"⏱️ Thời gian thực hiện: {result.duration:.2f} giây" if result.duration else "⏱️ Thời gian thực hiện: N/A")
        print(f"📈 Tỷ lệ thành công: {result.success_rate:.2%}")
        
        # In danh sách các URL đã crawl
        print("\n📋 Danh sách các URL đã crawl:")
        for i, page in enumerate(result.scraped_pages):
            print(f"  {i+1}. {page.url}")
        
        return result
        
    except Exception as e:
        print(f"❌ Lỗi trong test DFS strategy: {e}")
        return None


async def main():
    """
    Main function để test cả hai strategies.
    """
    print("Bắt đầu test crawling strategies...")
    
    try:
        # Test BFS strategy
        bfs_result = await test_bfs_strategy()
        
        # Test DFS strategy
        dfs_result = await test_dfs_strategy()
        
        # So sánh kết quả
        if bfs_result and dfs_result:
            print("\n" + "="*50)
            print("SO SÁNH KẾT QUẢ")
            print("="*50)
            print(f"BFS - Số trang: {len(bfs_result.scraped_pages)}, Số liên kết: {len(bfs_result.get_all_links())}")
            print(f"DFS - Số trang: {len(dfs_result.scraped_pages)}, Số liên kết: {len(dfs_result.get_all_links())}")
            
            # Kiểm tra xem có duplicate URLs không
            bfs_urls = {page.url for page in bfs_result.scraped_pages}
            dfs_urls = {page.url for page in dfs_result.scraped_pages}
            
            print(f"BFS - Số URLs duy nhất: {len(bfs_urls)}")
            print(f"DFS - Số URLs duy nhất: {len(dfs_urls)}")
            
            if len(bfs_urls) == len(bfs_result.scraped_pages):
                print("✅ BFS không có duplicate URLs")
            else:
                print("❌ BFS có duplicate URLs")
                
            if len(dfs_urls) == len(dfs_result.scraped_pages):
                print("✅ DFS không có duplicate URLs")
            else:
                print("❌ DFS có duplicate URLs")
        
        print("\n✅ Hoàn thành test tất cả strategies!")
        
    except Exception as e:
        print(f"❌ Lỗi trong main: {e}")


if __name__ == "__main__":
    asyncio.run(main())
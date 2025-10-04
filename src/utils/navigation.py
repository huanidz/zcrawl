"""
Module chứa các hàm tiện ích cho việc điều hướng và trích xuất liên kết.
"""

from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger

from ..models.CrawlResult import NavigableLink


def extract_navigable_links(
    html: str, base_url: Optional[str] = None
) -> List[NavigableLink]:
    """
    Trích xuất tất cả các liên kết có thể điều hướng từ HTML.

    Args:
        html (str): Nội dung HTML cần phân tích
        base_url (Optional[str]): URL cơ sở để giải quyết các liên kết tương đối

    Returns:
        List[NavigableLink]: Danh sách các liên kết có thể điều hướng
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        links = []

        # Tìm tất cả các thẻ <a> có thuộc tính href
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            text = a_tag.get_text(strip=True) or None

            # Bỏ qua các liên kết rỗng hoặc là các anchor (#)
            if not href or href.startswith("#"):
                continue

            # Bỏ qua các liên kết javascript:void(0) và mailto:
            if href.startswith("javascript:") or href.startswith("mailto:"):
                continue

            # Chuyển đổi liên kết tương đối thành tuyệt đối nếu có base_url
            if base_url and not href.startswith(("http://", "https://")):
                try:
                    href = urljoin(base_url, href)
                except Exception as e:
                    logger.warning(f"Lỗi khi chuyển đổi URL tương đối '{href}': {e}")
                    continue

            # Tạo đối tượng NavigableLink
            try:
                if href == base_url:
                    continue
                navigable_link = NavigableLink(url=href, text=text, parent_url=base_url)
                links.append(navigable_link)
            except Exception as e:
                logger.warning(f"Lỗi khi tạo NavigableLink cho URL '{href}': {e}")
                continue

        logger.info(f"Đã trích xuất {len(links)} liên kết từ HTML")
        return links

    except Exception as e:
        logger.error(f"Lỗi khi trích xuất liên kết từ HTML: {e}")
        return []

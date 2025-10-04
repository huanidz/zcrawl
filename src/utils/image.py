"""
Module chứa các hàm tiện ích cho việc trích xuất hình ảnh từ HTML.
"""

from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from loguru import logger

from ..models.ScrapingResult import ScrapedImage


def extract_images(html: str, base_url: Optional[str] = None) -> List[ScrapedImage]:  # noqa
    """
    Trích xuất tất cả các hình ảnh từ HTML.

    Args:
        html (str): Nội dung HTML cần phân tích
        base_url (Optional[str]): URL cơ sở để giải quyết các liên kết tương đối

    Returns:
        List[ScrapedImage]: Danh sách các hình ảnh đã trích xuất
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        images = []

        # Tìm tất cả các thẻ <img> có thuộc tính src
        for img_tag in soup.find_all("img", src=True):
            src = img_tag["src"].strip()
            alt = img_tag.get("alt", "").strip() or None
            width = img_tag.get("width")
            height = img_tag.get("height")

            # Bỏ qua các src rỗng
            if not src:
                continue

            # Bỏ qua các hình ảnh data URI
            if src.startswith("data:"):
                continue

            # Chuyển đổi liên kết tương đối thành tuyệt đối nếu có base_url
            if base_url and not src.startswith(("http://", "https://")):
                try:
                    src = urljoin(base_url, src)
                except Exception as e:
                    logger.warning(f"Lỗi khi chuyển đổi URL tương đối '{src}': {e}")
                    continue

            # Lấy mime type từ phần mở rộng của URL
            mime_type = None
            if "." in src.split("?")[0]:  # Tách query string nếu có
                extension = src.split("?")[0].split(".")[-1].lower()
                mime_type = f"image/{extension}"

            # Tìm caption trong figure hoặc figcaption
            caption = None
            figure_tag = img_tag.find_parent("figure")
            if figure_tag:
                figcaption = figure_tag.find("figcaption")
                if figcaption:
                    caption = figcaption.get_text(strip=True)

            # Tạo đối tượng ScrapedImage
            try:
                # Chuyển đổi width và height thành số nguyên nếu có
                width_int = None
                height_int = None
                if width:
                    try:
                        width_int = int(width)
                    except (ValueError, TypeError):
                        pass
                if height:
                    try:
                        height_int = int(height)
                    except (ValueError, TypeError):
                        pass

                crawled_image = ScrapedImage(
                    url=src,
                    alt_text=alt,
                    parent_url=base_url,
                    width=width_int,
                    height=height_int,
                    mime_type=mime_type,
                    caption=caption,
                )
                images.append(crawled_image)
            except Exception as e:
                logger.warning(f"Lỗi khi tạo ScrapedImage cho URL '{src}': {e}")
                continue

        logger.info(f"Đã trích xuất {len(images)} hình ảnh từ HTML")
        return images

    except Exception as e:
        logger.error(f"Lỗi khi trích xuất hình ảnh từ HTML: {e}")
        return []

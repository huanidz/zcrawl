from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import List, Optional


class NavigableLink(BaseModel):
    url: AnyHttpUrl
    text: Optional[str] = None
    parent_url: Optional[AnyHttpUrl] = None


class CrawledImage(BaseModel):
    url: AnyHttpUrl  # URL tuyệt đối của ảnh
    alt_text: Optional[str] = None  # Thuộc tính alt từ HTML
    parent_url: Optional[AnyHttpUrl] = None  # Trang chứa ảnh
    width: Optional[int] = None
    height: Optional[int] = None
    mime_type: Optional[str] = None  # Ví dụ: image/jpeg, image/png
    caption: Optional[str] = None  # Nếu tìm được caption hoặc figure text


# ==================================================


class PageCrawlResult(BaseModel):
    """
    Single page crawl result
    """

    url: str
    raw_html: str
    navigable_links: List[NavigableLink] = []
    images: List[CrawledImage] = []

from pydantic import AnyHttpUrl, BaseModel
from typing_extensions import List, Optional


class NavigableLink(BaseModel):
    url: AnyHttpUrl
    text: Optional[str] = None
    parent_url: Optional[AnyHttpUrl] = None


class CrawlResult(BaseModel):
    url: str
    raw_html: str
    navigable_links: List[NavigableLink] = []

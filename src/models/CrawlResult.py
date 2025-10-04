from pydantic import BaseModel


class CrawlResult(BaseModel):
    url: str
    raw_html: str

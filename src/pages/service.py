"""
Page dimension service — resolves page info into d_pages rows.
"""

from urllib.parse import urlparse
from sqlalchemy.orm import Session
from src.pages.model import Page
from src.events.schema import PagePayload


def resolve_page(page: PagePayload, db: Session) -> int:
    """
    Upsert page by URL. Extracts host from the full URL.
    Returns the page_id.
    """

    parsed_url = urlparse(page.url)
    host = parsed_url.netloc or "unknown"

    existing = db.query(Page).filter_by(url=page.url).first()

    if existing:
        return existing.id

    new_page = Page(
        page_name=page.page_name,
        url=page.url,
        full_path=page.full_path,
        host=host
    )

    db.add(new_page)
    db.flush()
    return new_page.id

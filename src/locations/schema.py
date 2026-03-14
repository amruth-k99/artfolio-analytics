from pydantic import BaseModel

class LocationModel(BaseModel):
    id: int | None = None
    city: str
    state: str
    country: str

class LocationFilterRequest(BaseModel):
    search_text: str | None = ""
    page: int = 1 #should be 1-based index for better UX
    page_size: int = 10
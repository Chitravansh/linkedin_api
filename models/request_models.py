from pydantic import BaseModel

class PostRequest(BaseModel):
    group_url: str
    message: str
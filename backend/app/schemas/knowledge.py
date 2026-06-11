from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class KnowledgeBase(BaseModel):
    title: str = Field(..., description="标题")
    content: str = Field(..., description="内容")
    category_id: int = Field(..., description="分类ID")


class KnowledgeCreate(KnowledgeBase):
    pass


class KnowledgeUpdate(BaseModel):
    title: Optional[str] = Field(None, description="标题")
    content: Optional[str] = Field(None, description="内容")
    category_id: Optional[int] = Field(None, description="分类ID")


class KnowledgeResponse(BaseModel):
    id: int
    title: str
    content: str
    category_id: int
    category_name: Optional[str] = None
    submitter_id: int
    submitter_name: Optional[str] = None
    review_status: str
    reject_reason: Optional[str]
    is_read: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeListResponse(BaseModel):
    items: List[KnowledgeResponse]
    total: int
    page: int
    page_size: int

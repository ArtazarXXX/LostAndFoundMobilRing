from typing import Optional
from pydantic import BaseModel, Field


class Item(BaseModel):
    id: int
    url: str
    place: str
    comment: str
    status: str
    type: str = "found"  # "found" or "lost"
    category: str = "other"  # "clothes", "keys", "cards", "tech", "other"
    created_at: str = ""
    return_code: str = ""
    author: str = "Дежурный"


class ItemCreate(BaseModel):
    url: str
    place: str
    comment: str
    type: str = "found"
    category: str = "other"
    author: str = "Максим Кабанов"


class ItemStatusUpdate(BaseModel):
    status: str


class ChatMessage(BaseModel):
    id: int
    item_id: int
    sender_name: str
    text: str
    created_at: str


class ChatMessageCreate(BaseModel):
    sender_name: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=1000)


class VerifyCodeRequest(BaseModel):
    code: str = Field(min_length=4, max_length=10)


class VerifyCodeResponse(BaseModel):
    success: bool
    message: str
    status: str


class Claim(BaseModel):
    id: int
    item_id: int
    fio: str
    group_name: str
    teacher: str
    status: str
    created_at: str


class ClaimCreate(BaseModel):
    item_id: int
    fio: str = Field(min_length=1, max_length=200)
    group_name: str = Field(min_length=1, max_length=100)
    teacher: str = Field(min_length=1, max_length=200)


class ClaimStatusUpdate(BaseModel):
    status: str


class UploadResponse(BaseModel):
    url: str


class MessageResponse(BaseModel):
    message: str


ITEM_STATUSES = {"in_applic", "accept", "not_accept", "delete", "returned"}
ITEM_TYPES = {"found", "lost"}
CATEGORIES = {"clothes", "keys", "cards", "tech", "other"}
CLAIM_STATUSES = {"pending", "done", "rejected"}


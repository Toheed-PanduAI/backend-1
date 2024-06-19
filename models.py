from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime

class Permission(BaseModel):
    permission: str
    granted: bool

class User(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    username: str
    email: EmailStr
    password_hash: str
    created_at: Optional[datetime] = None
    subscription_id: Optional[str] = None
    is_active: bool
    permissions: List[Permission] = []

class Payment(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    subscription_id: str
    amount: float
    currency: str  # e.g., "USD"
    payment_date: datetime
    payment_status: str  # e.g., "completed", "failed"

class Plan(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str  # e.g., "basic", "premium"
    price: float
    description: str
    price_id: str

class Subscription(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    plan: str  # e.g., "basic", "premium"
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str  # e.g., "active", "inactive", "canceled"

class VideoTask(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    task_status: str  # e.g., "pending", "in_progress", "completed", "failed"
    task_details: Dict[str, str]  # Detailed task information
    created_at: datetime
    updated_at: Optional[datetime] = None
    video_url: Optional[HttpUrl] = None  # URL of the generated video

class Item(BaseModel):
    email: str

class SubscriptionItem(BaseModel):
    priceId: str

class CancelItem(BaseModel):
    subscriptionId: str

class UpdateItem(BaseModel):
    subscriptionId: str
    newPriceLookupKey: str

class VoiceResponse(BaseModel):
    status: str
    voice_id: str
    message: str
    audio_file: Optional[bytes] = None

class TranscriptionResponse(BaseModel):
    status: str
    message: str
    text: Optional[str] = None

class ImageGenerationResponse(BaseModel):
    status: str
    message: str
    image_urls: Optional[List[str]] = None

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionResponse(BaseModel):
    status: str
    message: str
    response: Optional[str] = None

class StabilityGenerateImageRequest(BaseModel):
    model: str
    prompt: str
    negative_prompt: str = None
    aspect_ratio: str = None
    seed: int = None
    output_format: str = "webp"

class StabilityImageToVideoRequest(BaseModel):
    seed: int
    cfg_scale: float
    motion_bucket_id: int


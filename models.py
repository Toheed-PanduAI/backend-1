from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime

class Permission(BaseModel):
    permission: str
    granted: bool
    user_id: str

class User(BaseModel):
    user_id: str
    username: Optional[str] = None
    email: EmailStr
    stripe_customer_id: str
    created_at: Optional[datetime] = None
    subscription_id: Optional[str] = None
    price_id: Optional[str] = None
    is_active: bool

class Invoice(BaseModel):
    invoice_id: str
    user_id: str
    stripe_customer_id: str
    created_at: Optional[datetime] = None
    subscription_id: Optional[str] = None
    amount_paid: str = None
    amount_due: str = None
    amount_remaining: str = None
    currency: str = None
    invoice_pdf: str = None
    invoice_status: str = None
    invoice_url: str = None
    payment_intent_id: str = None

class Payment(BaseModel):
    payment_id: str
    user_id: str
    subscription_id: str
    amount: float
    currency: str  # e.g., "USD"
    payment_date: datetime
    payment_status: str  # e.g., "completed", "failed"

class Plan(BaseModel):
    plan_id: str
    name: str  # e.g., "basic", "premium"
    price: float
    description: str
    price_id: str

class Subscription(BaseModel):
    subscription_id: str
    user_id: str
    plan: str  # e.g., "basic", "premium"
    start_date: datetime
    end_date: Optional[datetime] = None
    status: str  # e.g., "active", "inactive", "canceled"

class VideoTask(BaseModel):
    video_task_id: str
    user_id: str
    task_status: str  # e.g., "pending", "in_progress", "completed", "failed"
    task_details: Dict[str, str]  # Detailed task information
    created_at: datetime
    updated_at: Optional[datetime] = None
    video_url: Optional[HttpUrl] = None  # URL of the generated video

class PriceResponse(BaseModel):
    publishableKey: str
    prices: list

class Item(BaseModel):
    email: str

class SubscriptionItem(BaseModel):
    priceId: str
    customerId: str

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

class SegmindImageGenerateRequest(BaseModel):
    data: dict
    model_name: str = "face-to-sticker"

class Dimension(BaseModel):
    width: int
    height: int

class VideoInput(BaseModel):
    character: Dict[str, Any]
    voice: Optional[Dict[str, Any]] = None
    background: Optional[Dict[str, Any]] = None

class HeygenVideoGenerateRequest(BaseModel):
    test: bool = True
    caption: bool = False
    dimension: Dimension = Field(default_factory=lambda: Dimension(width=1920, height=1080))
    video_inputs: List[VideoInput]
    title: Optional[str] = None
    callback_id: Optional[str] = None

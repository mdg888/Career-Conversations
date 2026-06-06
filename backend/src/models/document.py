from pydantic import BaseModel
from typing import Optional


ALLOWED_EXTENSIONS = {
    "txt", "pdf", "docx", "md",
    "png", "jpg", "jpeg", "webp", "tiff"
}

TEXT_TYPES = {"txt", "md"}
PDF_TYPES = {"pdf"}
DOCX_TYPES = {"docx"}
IMAGE_TYPES = {"png", "jpg", "jpeg", "webp", "tiff"}


class DocumentResponse(BaseModel):
    id: str
    chatbot_id: str
    filename: str
    file_type: str
    status: str
    error: Optional[str]
    created_at: str

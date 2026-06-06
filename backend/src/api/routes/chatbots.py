from fastapi import APIRouter, HTTPException, Depends
from backend.src.models.chatbot import ChatbotCreate, ChatbotUpdate, ChatbotResponse
from backend.src.services.config_service import ConfigService

router = APIRouter(prefix="/api/chatbots", tags=["chatbots"])


def get_config_service() -> ConfigService:
    return ConfigService()


@router.post("", response_model=ChatbotResponse, status_code=201)
def create_chatbot(data: ChatbotCreate, service: ConfigService = Depends(get_config_service)):
    return service.create_chatbot(data)


@router.get("", response_model=list[ChatbotResponse])
def list_chatbots(service: ConfigService = Depends(get_config_service)):
    return service.list_chatbots()


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
def get_chatbot(chatbot_id: str, service: ConfigService = Depends(get_config_service)):
    bot = service.get_chatbot(chatbot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    return bot


@router.put("/{chatbot_id}", response_model=ChatbotResponse)
def update_chatbot(chatbot_id: str, data: ChatbotUpdate, service: ConfigService = Depends(get_config_service)):
    bot = service.update_chatbot(chatbot_id, data)
    if not bot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    return bot


@router.delete("/{chatbot_id}", status_code=204)
def delete_chatbot(chatbot_id: str, service: ConfigService = Depends(get_config_service)):
    if not service.delete_chatbot(chatbot_id):
        raise HTTPException(status_code=404, detail="Chatbot not found")

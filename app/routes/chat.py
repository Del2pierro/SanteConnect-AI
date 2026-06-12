"""
Routes pour le chat avec l'assistant médical.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import ChatHistoryItem, ChatHistoryResponse, ChatConversationItem, ChatResponse, HealthStatus, Message
from app.services.chat_history_service import chat_history_service
from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["chat"],
    responses={404: {"description": "Non trouvé"}},
)


@router.get("/", response_model=HealthStatus)
async def health_check():
    """
    Vérification du statut de l'application
    
    Returns:
        HealthStatus: Statut actuel de l'application
    """
    return HealthStatus(
        status="ok",
        version=settings.APP_VERSION
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(data: Message, db: Session = Depends(get_db)) -> ChatResponse:
    """
    Endpoint pour discuter avec l'assistant médical
    
    Args:
        data: Message utilisateur
        
    Returns:
        ChatResponse: Réponse générée par le modèle
        
    Raises:
        HTTPException: Si une erreur survient lors du traitement
    """
    try:
        logger.info(f"Nouveau message reçu: {data.message[:50]}...")
        
        response_text = await llm_service.generate_response(data.message)
        exchange = chat_history_service.create_exchange(
            db,
            data.message,
            response_text,
            conversation_id=data.conversation_id,
        )
        
        return ChatResponse(response=response_text, conversation_id=exchange.conversation_id or 0)
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la génération de la réponse"
        )


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history(db: Session = Depends(get_db)) -> ChatHistoryResponse:
    """Retourne l'historique des conversations de chat depuis la base."""
    conversations = chat_history_service.list_conversations(db)
    items = []

    for conversation in conversations:
        exchanges = getattr(conversation, "exchanges", [])
        items.append(
            ChatConversationItem(
                id=conversation.id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                count=len(exchanges),
                items=[
                    ChatHistoryItem(
                        id=exchange.id,
                        message=exchange.message,
                        response=exchange.response,
                        created_at=exchange.created_at,
                    )
                    for exchange in exchanges
                ],
            )
        )

    return ChatHistoryResponse(items=items, count=len(items))

"""
Modèles Pydantic pour la validation des données
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    """Modèle pour les messages du chat"""
    
    message: str = Field(..., min_length=1, max_length=1000, description="Message à traiter")
    conversation_id: int | None = Field(default=None, description="Identifiant de conversation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Quels sont les symptômes de la grippe?",
                "conversation_id": 1,
            }
        }
    )


class ChatResponse(BaseModel):
    """Modèle pour la réponse du chat"""
    
    response: str = Field(..., description="Réponse du modèle")
    conversation_id: int = Field(..., description="Identifiant de conversation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "response": "Les symptômes de la grippe incluent...",
                "conversation_id": 1,
            }
        }
    )


class ChatHistoryItem(BaseModel):
    """Entrée d'historique pour un échange de chat."""

    id: int = Field(..., description="Identifiant de l'échange")
    message: str = Field(..., description="Message utilisateur")
    response: str = Field(..., description="Réponse de l'assistant")
    created_at: datetime = Field(..., description="Date et heure de l'échange")


class ChatConversationItem(BaseModel):
    """Entrée d'historique pour une conversation complète."""

    id: int = Field(..., description="Identifiant de la conversation")
    title: str = Field(..., description="Titre de la conversation")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de mise à jour")
    count: int = Field(..., description="Nombre d'échanges")
    items: list[ChatHistoryItem] = Field(default_factory=list, description="Échanges de la conversation")


class ChatHistoryResponse(BaseModel):
    """Réponse contenant l'historique des échanges."""

    items: list[ChatConversationItem] = Field(default_factory=list, description="Liste des conversations")
    count: int = Field(..., description="Nombre total de conversations")


class HealthStatus(BaseModel):
    """Modèle pour le statut de santé"""
    
    status: str = Field("ok", description="Statut de l'application")
    version: str = Field(..., description="Version de l'application")

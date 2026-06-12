"""
Service de persistance de l'historique des chats.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import ChatConversation, ChatExchange, _build_conversation_title


class ChatHistoryService:
    """Gère l'écriture et la lecture des échanges de chat."""

    def create_exchange(
        self,
        db: Session,
        message: str,
        response: str,
        conversation_id: int | None = None,
    ) -> ChatExchange:
        conversation = self._get_or_create_conversation(db, conversation_id, message)
        exchange = ChatExchange(
            conversation_id=conversation.id,
            message=message,
            response=response,
        )
        db.add(exchange)
        conversation.updated_at = datetime.now(timezone.utc)
        if not conversation.title:
            conversation.title = _build_conversation_title(message)
        db.add(conversation)
        db.commit()
        db.refresh(exchange)
        return exchange

    def list_conversations(self, db: Session) -> list[ChatConversation]:
        stmt = select(ChatConversation).order_by(ChatConversation.updated_at.desc(), ChatConversation.id.desc())
        conversations = list(db.scalars(stmt).all())

        for conversation in conversations:
            conversation.exchanges = list(
                db.scalars(
                    select(ChatExchange)
                    .where(ChatExchange.conversation_id == conversation.id)
                    .order_by(ChatExchange.created_at.asc(), ChatExchange.id.asc()),
                ).all(),
            )

        return conversations

    def _get_or_create_conversation(
        self,
        db: Session,
        conversation_id: int | None,
        message: str,
    ) -> ChatConversation:
        if conversation_id is not None:
            conversation = db.get(ChatConversation, conversation_id)
            if conversation is not None:
                return conversation

        conversation = ChatConversation(
            title=_build_conversation_title(message),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(conversation)
        db.flush()
        return conversation


chat_history_service = ChatHistoryService()
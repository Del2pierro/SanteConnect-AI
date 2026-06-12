"""
Accès base de données pour l'historique des chats.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Text, create_engine, inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import settings


def _engine_kwargs() -> dict[str, object]:
    if settings.DATABASE_URL.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    **_engine_kwargs(),
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    """Base déclarative SQLAlchemy."""


class ChatConversation(Base):
    """Table des conversations chat."""

    __tablename__ = "chat_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ChatExchange(Base):
    """Table des échanges chat à des fins d'audit."""

    __tablename__ = "chat_exchanges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int | None] = mapped_column(
        Integer,
        index=True,
        nullable=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


def init_db() -> None:
    """Crée les tables si elles n'existent pas."""
    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_history_schema()


def _migrate_sqlite_history_schema() -> None:
    if not settings.DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())

        if "chat_exchanges" not in tables:
            return

        columns = {
            column[1]
            for column in connection.exec_driver_sql("PRAGMA table_info(chat_exchanges)")
        }
        if "conversation_id" not in columns:
            try:
                connection.execute(text("ALTER TABLE chat_exchanges ADD COLUMN conversation_id INTEGER"))
            except OperationalError:
                pass

        legacy_rows = connection.execute(
            text("SELECT COUNT(*) FROM chat_exchanges WHERE conversation_id IS NULL"),
        ).scalar_one()

        if not legacy_rows:
            return

        conversation_row = connection.execute(
            text("SELECT id FROM chat_conversations ORDER BY id LIMIT 1"),
        ).fetchone()

        if conversation_row is None:
            first_message_row = connection.execute(
                text("SELECT message FROM chat_exchanges ORDER BY id LIMIT 1"),
            ).fetchone()
            legacy_title = _build_conversation_title(first_message_row[0] if first_message_row else None)
            result = connection.execute(
                text(
                    """
                    INSERT INTO chat_conversations (title, created_at, updated_at)
                    VALUES (:title, :created_at, :updated_at)
                    """,
                ),
                {
                    "title": legacy_title,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            conversation_id = result.lastrowid
        else:
            conversation_id = conversation_row[0]

        connection.execute(
            text("UPDATE chat_exchanges SET conversation_id = :conversation_id WHERE conversation_id IS NULL"),
            {"conversation_id": conversation_id},
        )


def _build_conversation_title(message: str | None) -> str:
    if not message:
        return "Conversation héritée"

    cleaned = " ".join(message.split())
    if cleaned.startswith("DONNÉES CLINIQUES DU PATIENT :"):
        parts = cleaned.split("OBSERVATION COMPLÉMENTAIRE :", 1)
        if len(parts) == 2:
            cleaned = parts[1].strip() or cleaned

    return cleaned[:60].rstrip() + ("…" if len(cleaned) > 60 else "")


def get_db() -> Generator[Session, None, None]:
    """Fournit une session SQLAlchemy par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
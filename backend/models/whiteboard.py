"""
SQLAlchemy ORM models for the Whiteboard / Excalidraw feature.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


def _gen_uuid() -> str:
    return str(uuid.uuid4())


class WhiteboardRoom(Base):
    """A collaborative drawing room."""
    __tablename__ = "whiteboard_rooms"

    id = Column(String(36), primary_key=True, default=_gen_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    owner_email = Column(String(255), nullable=False)
    is_public = Column(Boolean, default=False)

    # Random token embedded in the invite link
    share_token = Column(String(64), unique=True, nullable=True)

    # Last known canvas state (persisted so restarts don't wipe work)
    current_data = Column(Text, default="[]")        # JSON array of Excalidraw elements
    current_app_state = Column(Text, default="{}")   # JSON object of Excalidraw appState

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    snapshots = relationship(
        "WhiteboardSnapshot", back_populates="room",
        cascade="all, delete-orphan", order_by="WhiteboardSnapshot.created_at.desc()"
    )
    members = relationship(
        "WhiteboardMember", back_populates="room",
        cascade="all, delete-orphan"
    )


class WhiteboardSnapshot(Base):
    """A saved version / history entry of a room's canvas."""
    __tablename__ = "whiteboard_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(String(36), ForeignKey("whiteboard_rooms.id", ondelete="CASCADE"), nullable=False)
    data = Column(Text, nullable=False)       # JSON: Excalidraw elements
    app_state = Column(Text, default="{}")    # JSON: Excalidraw appState
    thumbnail = Column(Text, nullable=True)   # base64 PNG (small preview)
    saved_by = Column(String(255), nullable=True)
    label = Column(String(255), default="Auto-save")
    created_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("WhiteboardRoom", back_populates="snapshots")


class WhiteboardMember(Base):
    """Explicit collaborator access on a room."""
    __tablename__ = "whiteboard_members"

    room_id = Column(
        String(36), ForeignKey("whiteboard_rooms.id", ondelete="CASCADE"),
        primary_key=True
    )
    email = Column(String(255), primary_key=True)
    role = Column(String(20), default="editor")   # 'editor' | 'viewer'
    added_at = Column(DateTime, default=datetime.utcnow)

    room = relationship("WhiteboardRoom", back_populates="members")

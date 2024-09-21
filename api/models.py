from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    JSON,
    Boolean,
    TIMESTAMP,
    func,
)
from sqlalchemy.orm import relationship
from .database import Base  # Importando o Base da database.py


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)

    # Relacionamento com eventos e notificações
    events = relationship("Event", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Event(Base):
    __tablename__ = "events"
    event_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    event_type = Column(String(100))
    event_data = Column(JSON)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    # Relacionamento com o usuário
    user = relationship("User", back_populates="events")
    notifications = relationship("Notification", back_populates="event")


class Notification(Base):
    __tablename__ = "notifications"
    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    event_id = Column(Integer, ForeignKey("events.event_id"))
    is_read = Column(Boolean, default=False)

    # Relacionamento com usuário e eventos
    user = relationship("User", back_populates="notifications")
    event = relationship("Event", back_populates="notifications")

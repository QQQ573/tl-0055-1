from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, index=True, nullable=False)
    store_code = Column(String, index=True, nullable=False)
    complaint_type = Column(String, nullable=False)
    handler = Column(String, nullable=False)
    has_compensation = Column(Boolean, default=False)
    compensation_type = Column(String, nullable=True)
    compensation_amount = Column(Float, default=0.0)
    closing_remark = Column(String, nullable=True)
    is_closed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    images = relationship("TicketImage", back_populates="ticket", cascade="all, delete-orphan")


class TicketImage(Base):
    __tablename__ = "ticket_images"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="images")

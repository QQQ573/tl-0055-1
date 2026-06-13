from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from . import models, schemas


def get_tickets(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    brand: Optional[str] = None,
    is_closed: Optional[bool] = None
):
    query = db.query(models.Ticket).filter(models.Ticket.deleted_at.is_(None))

    if brand:
        query = query.filter(models.Ticket.brand == brand)
    if is_closed is not None:
        query = query.filter(models.Ticket.is_closed == is_closed)

    total = query.count()
    items = query.order_by(models.Ticket.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    total_pages = (total + page_size - 1) // page_size

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def get_ticket(db: Session, ticket_id: int):
    return db.query(models.Ticket).filter(
        models.Ticket.id == ticket_id,
        models.Ticket.deleted_at.is_(None)
    ).first()


def create_ticket(db: Session, ticket: schemas.TicketCreate):
    db_ticket = models.Ticket(**ticket.model_dump())
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def update_ticket(db: Session, ticket_id: int, ticket: schemas.TicketUpdate):
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    for key, value in ticket.model_dump().items():
        setattr(db_ticket, key, value)
    db_ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def soft_delete_ticket(db: Session, ticket_id: int):
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    db_ticket.deleted_at = datetime.utcnow()
    db.commit()
    return db_ticket


def add_ticket_image(db: Session, ticket_id: int, filename: str, original_name: str, file_path: str):
    db_image = models.TicketImage(
        ticket_id=ticket_id,
        filename=filename,
        original_name=original_name,
        file_path=file_path
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image


def get_ticket_image(db: Session, image_id: int):
    return db.query(models.TicketImage).filter(models.TicketImage.id == image_id).first()

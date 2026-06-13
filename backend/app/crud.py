from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from . import models, schemas

SLA_HOURS_CONFIG: Dict[str, float] = {
    "餐凉": 4.0,
    "漏配酱包": 8.0,
    "等待过久": 2.0,
    "其他": 6.0
}

STATUS_FLOW = {
    "pending": ["processing"],
    "processing": ["review"],
    "review": ["closed", "processing"],
    "closed": []
}

STATUS_NAMES = {
    "pending": "待受理",
    "processing": "处理中",
    "review": "待复核",
    "closed": "已结案"
}

ACTION_NAMES = {
    "accept": "受理",
    "process": "开始处理",
    "review": "提交复核",
    "close": "结案",
    "reject": "驳回",
    "create": "创建工单",
    "update": "更新工单",
    "delete": "删除工单",
    "upload_image": "上传图片",
    "delete_image": "删除图片"
}


def get_sla_hours(complaint_type: str) -> float:
    return SLA_HOURS_CONFIG.get(complaint_type, SLA_HOURS_CONFIG["其他"])


def calculate_sla_status(ticket: models.Ticket) -> tuple[bool, Optional[float]]:
    if ticket.status == "processing" or ticket.status == "closed":
        return False, None
    
    sla_hours = get_sla_hours(ticket.complaint_type)
    elapsed_hours = (datetime.utcnow() - ticket.created_at).total_seconds() / 3600
    remaining = sla_hours - elapsed_hours
    
    if remaining < 0:
        return True, 0.0
    return False, round(remaining, 1)


def get_tickets(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    brand: Optional[str] = None,
    is_closed: Optional[bool] = None,
    status: Optional[str] = None
):
    query = db.query(models.Ticket).filter(models.Ticket.deleted_at.is_(None))

    if brand:
        query = query.filter(models.Ticket.brand == brand)
    if is_closed is not None:
        query = query.filter(models.Ticket.is_closed == is_closed)
    if status:
        query = query.filter(models.Ticket.status == status)

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


def create_ticket(db: Session, ticket: schemas.TicketCreate, operator: str = "系统", client_ip: str = None):
    db_ticket = models.Ticket(
        **ticket.model_dump(),
        status="pending",
        status_updated_at=datetime.utcnow()
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    log = models.TicketOperationLog(
        ticket_id=db_ticket.id,
        operator=operator,
        action="create",
        changes=ticket.model_dump(),
        client_ip=client_ip,
        remark="创建工单"
    )
    db.add(log)
    db.commit()
    
    return db_ticket


def update_ticket(db: Session, ticket_id: int, ticket: schemas.TicketUpdate, operator: str = "系统", client_ip: str = None):
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    
    changes = {}
    for key, value in ticket.model_dump().items():
        old_value = getattr(db_ticket, key)
        if old_value != value:
            changes[key] = {"old": old_value, "new": value}
        setattr(db_ticket, key, value)
    db_ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    
    if changes:
        log = models.TicketOperationLog(
            ticket_id=ticket_id,
            operator=operator,
            action="update",
            changes=changes,
            client_ip=client_ip,
            remark="更新工单"
        )
        db.add(log)
        db.commit()
    
    return db_ticket


def soft_delete_ticket(db: Session, ticket_id: int, operator: str = "系统", client_ip: str = None):
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    db_ticket.deleted_at = datetime.utcnow()
    db.commit()
    
    log = models.TicketOperationLog(
        ticket_id=ticket_id,
        operator=operator,
        action="delete",
        changes={"deleted_at": datetime.utcnow().isoformat()},
        client_ip=client_ip,
        remark="删除工单"
    )
    db.add(log)
    db.commit()
    
    return db_ticket


def transition_status(db: Session, ticket_id: int, action: str, operator: str = "系统", 
                     client_ip: str = None, rejected_reason: str = None) -> tuple[bool, str]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return False, "工单不存在"
    
    current_status = db_ticket.status
    allowed_next = STATUS_FLOW.get(current_status, [])
    
    if action == "accept" and current_status == "pending":
        new_status = "processing"
    elif action == "process" and current_status in ["pending", "review"]:
        new_status = "processing"
    elif action == "review" and current_status == "processing":
        new_status = "review"
    elif action == "close" and current_status == "review":
        new_status = "closed"
    elif action == "reject":
        if current_status != "review":
            return False, "只有待复核状态才能驳回"
        if not rejected_reason:
            return False, "驳回时必须填写驳回原因"
        new_status = "processing"
    else:
        return False, f"不允许从{STATUS_NAMES.get(current_status, current_status)}执行此操作"
    
    old_status = db_ticket.status
    db_ticket.status = new_status
    db_ticket.status_updated_at = datetime.utcnow()
    db_ticket.is_closed = (new_status == "closed")
    
    if action == "reject":
        db_ticket.rejected_reason = rejected_reason
    elif action == "close":
        db_ticket.closing_remark = rejected_reason or "已结案"
    
    db.commit()
    db.refresh(db_ticket)
    
    remark = f"状态变更: {STATUS_NAMES.get(old_status, old_status)} → {STATUS_NAMES.get(new_status, new_status)}"
    if rejected_reason:
        remark += f"，驳回原因: {rejected_reason}"
    
    log = models.TicketOperationLog(
        ticket_id=ticket_id,
        operator=operator,
        action=action,
        changes={
            "status": {"old": old_status, "new": new_status},
            "action": ACTION_NAMES.get(action, action)
        },
        client_ip=client_ip,
        remark=remark
    )
    db.add(log)
    db.commit()
    
    return True, "状态变更成功"


def add_ticket_image(db: Session, ticket_id: int, filename: str, original_name: str, 
                    file_path: str, operator: str = "系统", client_ip: str = None):
    db_image = models.TicketImage(
        ticket_id=ticket_id,
        filename=filename,
        original_name=original_name,
        file_path=file_path
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    
    log = models.TicketOperationLog(
        ticket_id=ticket_id,
        operator=operator,
        action="upload_image",
        changes={"filename": filename, "original_name": original_name},
        client_ip=client_ip,
        remark=f"上传图片: {original_name}"
    )
    db.add(log)
    db.commit()
    
    return db_image


def get_ticket_image(db: Session, image_id: int):
    return db.query(models.TicketImage).filter(models.TicketImage.id == image_id).first()


def delete_ticket_image(db: Session, image_id: int, operator: str = "系统", client_ip: str = None):
    db_image = get_ticket_image(db, image_id)
    if not db_image:
        return None
    
    ticket_id = db_image.ticket_id
    original_name = db_image.original_name
    
    db.delete(db_image)
    db.commit()
    
    log = models.TicketOperationLog(
        ticket_id=ticket_id,
        operator=operator,
        action="delete_image",
        changes={"image_id": image_id, "original_name": original_name},
        client_ip=client_ip,
        remark=f"删除图片: {original_name}"
    )
    db.add(log)
    db.commit()
    
    return db_image


def get_operation_logs(db: Session, ticket_id: int, action_filter: Optional[str] = None) -> List[models.TicketOperationLog]:
    query = db.query(models.TicketOperationLog).filter(
        models.TicketOperationLog.ticket_id == ticket_id
    )
    
    if action_filter:
        query = query.filter(models.TicketOperationLog.action == action_filter)
    
    return query.order_by(models.TicketOperationLog.created_at.desc()).all()

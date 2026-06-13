from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
from datetime import datetime

from .database import get_db, engine, Base, settings
from . import crud, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="400热线工单管理系统",
    description="肯德基、麦当劳、华莱士投诉工单管理系统，支持状态机流转和操作日志",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/tickets", response_model=schemas.TicketListResponse, tags=["工单管理"])
def read_tickets(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    brand: Optional[str] = Query(None, description="品牌筛选"),
    is_closed: Optional[bool] = Query(None, description="是否结案筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取工单列表，按日期倒序，支持品牌、结案状态和状态筛选
    """
    return crud.get_tickets(db, page=page, page_size=page_size, brand=brand, is_closed=is_closed, status=status)


@app.get("/tickets/{ticket_id}", response_model=schemas.TicketResponse, tags=["工单管理"])
def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    获取单个工单详情
    """
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    is_sla_breached, sla_hours_remaining = crud.calculate_sla_status(db_ticket)
    db_ticket.is_sla_breached = is_sla_breached
    db_ticket.sla_hours_remaining = sla_hours_remaining
    
    return db_ticket


@app.post("/tickets", response_model=schemas.TicketResponse, tags=["工单管理"])
def create_ticket(ticket: schemas.TicketCreate, request: Request, db: Session = Depends(get_db)):
    """
    创建新工单
    """
    client_ip = get_client_ip(request)
    operator = ticket.handler or "系统"
    return crud.create_ticket(db=db, ticket=ticket, operator=operator, client_ip=client_ip)


@app.put("/tickets/{ticket_id}", response_model=schemas.TicketResponse, tags=["工单管理"])
def update_ticket(ticket_id: int, ticket: schemas.TicketUpdate, request: Request, db: Session = Depends(get_db)):
    """
    更新工单
    """
    client_ip = get_client_ip(request)
    db_ticket = crud.update_ticket(db=db, ticket_id=ticket_id, ticket=ticket, operator="系统", client_ip=client_ip)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return db_ticket


@app.delete("/tickets/{ticket_id}", tags=["工单管理"])
def delete_ticket(ticket_id: int, request: Request, db: Session = Depends(get_db)):
    """
    软删除工单（保留 deleted_at 标记）
    """
    client_ip = get_client_ip(request)
    db_ticket = crud.soft_delete_ticket(db=db, ticket_id=ticket_id, operator="系统", client_ip=client_ip)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return {"message": "工单已删除", "deleted_at": db_ticket.deleted_at}


@app.post("/tickets/{ticket_id}/transition", tags=["状态流转"])
def transition_ticket_status(
    ticket_id: int,
    transition: schemas.StatusTransitionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    工单状态流转
    流程: 待受理 → 处理中 → 待复核 → 已结案
    驳回: 仅允许从待复核退回处理中，需要填写驳回原因
    """
    client_ip = get_client_ip(request)
    operator = transition.action
    success, message = crud.transition_status(
        db=db, 
        ticket_id=ticket_id, 
        action=transition.action,
        operator=operator,
        client_ip=client_ip,
        rejected_reason=transition.rejected_reason
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}


@app.get("/tickets/{ticket_id}/logs", response_model=List[schemas.OperationLogResponse], tags=["操作日志"])
def get_ticket_operation_logs(
    ticket_id: int,
    action: Optional[str] = Query(None, description="动作类型筛选"),
    db: Session = Depends(get_db)
):
    """
    获取工单操作日志时间线
    """
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    return crud.get_operation_logs(db, ticket_id=ticket_id, action_filter=action)


@app.get("/statuses", tags=["基础数据"])
def get_statuses():
    """
    获取状态列表和当前状态配置
    """
    return {
        "statuses": [
            {"value": "pending", "label": "待受理", "color": "info"},
            {"value": "processing", "label": "处理中", "color": "warning"},
            {"value": "review", "label": "待复核", "color": "primary"},
            {"value": "closed", "label": "已结案", "color": "success"}
        ],
        "flow": crud.STATUS_FLOW,
        "names": crud.STATUS_NAMES
    }


@app.get("/sla-config", tags=["基础数据"])
def get_sla_config():
    """
    获取 SLA 配置（按投诉类型）
    """
    return {
        "sla_hours": crud.SLA_HOURS_CONFIG,
        "descriptions": {
            "餐凉": "4小时响应时限",
            "漏配酱包": "8小时响应时限",
            "等待过久": "2小时响应时限",
            "其他": "6小时响应时限（默认）"
        }
    }


@app.post("/tickets/{ticket_id}/images", tags=["工单管理"])
async def upload_ticket_image(
    ticket_id: int,
    files: List[UploadFile] = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    为工单上传图片附件
    """
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")

    client_ip = get_client_ip(request) if request else "unknown"
    uploaded_images = []
    for file in files:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="只允许上传图片文件")

        file_ext = os.path.splitext(file.filename)[1]
        new_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(settings.UPLOAD_DIR, new_filename)

        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        db_image = crud.add_ticket_image(
            db=db,
            ticket_id=ticket_id,
            filename=new_filename,
            original_name=file.filename or new_filename,
            file_path=f"/uploads/{new_filename}",
            operator="系统",
            client_ip=client_ip
        )
        uploaded_images.append(db_image)

    return {"uploaded": len(uploaded_images), "images": uploaded_images}


@app.get("/brands", tags=["基础数据"])
def get_brands():
    """
    获取可选品牌列表
    """
    return {"brands": ["肯德基", "麦当劳", "华莱士"]}


@app.get("/complaint-types", tags=["基础数据"])
def get_complaint_types():
    """
    获取可选投诉类型
    """
    return {"types": ["餐凉", "漏配酱包", "等待过久", "食物变质", "服务态度", "其他"]}


@app.get("/compensation-types", tags=["基础数据"])
def get_compensation_types():
    """
    获取可选补偿类型
    """
    return {"types": ["优惠券", "代金券", "退款", "赠品", "其他"]}


@app.get("/actions", tags=["基础数据"])
def get_action_types():
    """
    获取操作日志动作类型
    """
    return {"actions": crud.ACTION_NAMES}


@app.get("/", tags=["系统"])
def root():
    return {
        "name": "400热线工单管理系统",
        "version": "2.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

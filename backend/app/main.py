from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
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
    description="肯德基、麦当劳、华莱士投诉工单管理系统",
    version="1.0.0"
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


@app.get("/tickets", response_model=schemas.TicketListResponse, tags=["工单管理"])
def read_tickets(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    brand: Optional[str] = Query(None, description="品牌筛选"),
    is_closed: Optional[bool] = Query(None, description="是否结案筛选"),
    db: Session = Depends(get_db)
):
    """
    获取工单列表，按日期倒序，支持品牌和结案状态筛选
    """
    return crud.get_tickets(db, page=page, page_size=page_size, brand=brand, is_closed=is_closed)


@app.get("/tickets/{ticket_id}", response_model=schemas.TicketResponse, tags=["工单管理"])
def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    获取单个工单详情
    """
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return db_ticket


@app.post("/tickets", response_model=schemas.TicketResponse, tags=["工单管理"])
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    """
    创建新工单
    """
    return crud.create_ticket(db=db, ticket=ticket)


@app.put("/tickets/{ticket_id}", response_model=schemas.TicketResponse, tags=["工单管理"])
def update_ticket(ticket_id: int, ticket: schemas.TicketUpdate, db: Session = Depends(get_db)):
    """
    更新工单
    """
    db_ticket = crud.update_ticket(db=db, ticket_id=ticket_id, ticket=ticket)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return db_ticket


@app.delete("/tickets/{ticket_id}", tags=["工单管理"])
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    软删除工单（保留 deleted_at 标记）
    """
    db_ticket = crud.soft_delete_ticket(db=db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")
    return {"message": "工单已删除", "deleted_at": db_ticket.deleted_at}


@app.post("/tickets/{ticket_id}/images", tags=["工单管理"])
async def upload_ticket_image(
    ticket_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    为工单上传图片附件
    """
    db_ticket = crud.get_ticket(db, ticket_id=ticket_id)
    if db_ticket is None:
        raise HTTPException(status_code=404, detail="工单不存在")

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
            file_path=f"/uploads/{new_filename}"
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


@app.get("/", tags=["系统"])
def root():
    return {
        "name": "400热线工单管理系统",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }

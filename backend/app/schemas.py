from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Optional, List


class TicketImageBase(BaseModel):
    filename: str
    original_name: str
    file_path: str


class TicketImageResponse(TicketImageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    brand: str = Field(..., description="品牌名称，如肯德基、麦当劳、华莱士")
    store_code: str = Field(..., description="门店编号")
    complaint_type: str = Field(..., description="投诉类型，如餐凉、漏配酱包、等待过久")
    handler: str = Field(..., description="处理人")
    has_compensation: bool = Field(default=False, description="是否补偿券")
    compensation_type: Optional[str] = Field(None, description="补偿类型")
    compensation_amount: float = Field(default=0.0, description="补偿金额")
    closing_remark: Optional[str] = Field(None, description="结案备注")
    is_closed: bool = Field(default=False, description="是否结案")

    @model_validator(mode='after')
    def check_compensation_type_when_amount_positive(self):
        if self.compensation_amount > 0 and not self.compensation_type:
            raise ValueError('补偿金额大于0时必须选择补偿类型')
        return self


class TicketCreate(TicketBase):
    pass


class TicketUpdate(TicketBase):
    pass


class TicketResponse(TicketBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    images: List[TicketImageResponse] = []

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

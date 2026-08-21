from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.audit_log import ExpenseAction
from app.models.expense import Currency, ExpenseCategory, ExpenseStatus

class ExpenseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    details: Optional[str] = Field(default=None)
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: Currency
    category: ExpenseCategory

    model_config = ConfigDict(extra="forbid")

class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=150)
    details: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    currency: Optional[Currency] = None
    category: Optional[ExpenseCategory] = None

    model_config = ConfigDict(extra="forbid")

class ExpenseResponse(BaseModel):
    id: int
    title: str
    details: Optional[str]
    amount: Decimal
    currency: Currency
    category: ExpenseCategory
    status: ExpenseStatus
    employee_id: int
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    paid_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ExpenseAuditResponse(BaseModel):
    id: int
    expense_id: int
    user_id: int
    action: ExpenseAction
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

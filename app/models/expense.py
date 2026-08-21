import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.audit_log import ExpenseAudit

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone

from app.db.base import Base


class ExpenseStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ExpenseCategory(str, enum.Enum):
    TRAVEL = "travel"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    OFFICE = "office"
    OTHER = "other"


class Currency(str, enum.Enum):
    EUR = "EUR"
    UAH = "UAH"
    USD = "USD"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(
            Currency,
            name="currency",
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ), nullable=False
    )
    category: Mapped[ExpenseCategory] = mapped_column(
        Enum(
            ExpenseCategory,
            name="expense_category",
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ), nullable=False
    )
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(
            ExpenseStatus,
            name="expense_status",
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ), nullable=False, default=ExpenseStatus.DRAFT
    )
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped["User"] = relationship(back_populates="expenses")
    audit_logs: Mapped[list["ExpenseAudit"]] = relationship(back_populates="expense", cascade="all, delete-orphan")

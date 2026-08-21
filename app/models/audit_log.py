import enum
from datetime import datetime
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.expense import Expense
    from app.models.user import User

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExpenseAction(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ExpenseAudit(Base):
    __tablename__ = "expense_audits"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[ExpenseAction] = mapped_column(
        Enum(
            ExpenseAction,
            name="expense_actions",
            values_callable=lambda enum_class: [
                member.value for member in enum_class
            ],
        ), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    expense: Mapped["Expense"] = relationship(back_populates="audit_logs")
    user: Mapped["User"] = relationship()

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.models.audit_log import ExpenseAction, ExpenseAudit
from app.models.expense import Expense, ExpenseCategory, ExpenseStatus
from app.models.user import User, UserRole
from app.schemas.expense import ExpenseAuditResponse, ExpenseCreate, ExpenseResponse, ExpenseUpdate


router = APIRouter(
    prefix="/expenses",
    tags=["expenses"]
)


def add_audit(db: Session, expense_id: int, user_id: int, action: ExpenseAction):
    db.add(ExpenseAudit(expense_id=expense_id, user_id=user_id, action=action))


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(expense_data: ExpenseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.EMPLOYEE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only employees can create expenses")

    expense = Expense(
        title=expense_data.title,
        details=expense_data.details,
        amount=expense_data.amount,
        currency=expense_data.currency,
        category=expense_data.category,
        employee_id=current_user.id,
        status=ExpenseStatus.DRAFT,
    )

    db.add(expense)
    db.flush()

    add_audit(db, expense.id, current_user.id, ExpenseAction.CREATED)

    db.commit()
    db.refresh(expense)

    return expense


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    expense_status: Optional[ExpenseStatus] = Query(default=None, alias="status"),
    category: Optional[ExpenseCategory] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    statement = select(Expense)

    if current_user.role == UserRole.EMPLOYEE:
        statement = statement.where(Expense.employee_id == current_user.id)
    elif current_user.role not in (UserRole.MANAGER, UserRole.ACCOUNTANT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if expense_status is not None:
        statement = statement.where(Expense.status == expense_status)

    if category is not None:
        statement = statement.where(Expense.category == category)

    statement = statement.order_by(Expense.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    return list(db.scalars(statement).all())


@router.get("/{expense_id}/audit", response_model=list[ExpenseAuditResponse])
def get_expense_audit(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)

    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if current_user.role == UserRole.EMPLOYEE and expense.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    statement = select(ExpenseAudit).where(ExpenseAudit.expense_id == expense_id).order_by(ExpenseAudit.created_at.asc())

    return list(db.scalars(statement).all())


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)

    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if current_user.role == UserRole.EMPLOYEE and expense.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if current_user.role not in (UserRole.EMPLOYEE, UserRole.MANAGER, UserRole.ACCOUNTANT):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return expense


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(expense_id: int, expense_data: ExpenseUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)

    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if current_user.role != UserRole.EMPLOYEE or expense.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if expense.status != ExpenseStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft expenses can be edited")

    update_data = expense_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field != "details" and value is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{field} cannot be null")
        setattr(expense, field, value)

    add_audit(db, expense.id, current_user.id, ExpenseAction.UPDATED)

    db.commit()
    db.refresh(expense)

    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)

    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if current_user.role != UserRole.EMPLOYEE or expense.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if expense.status != ExpenseStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft expenses can be deleted")

    db.delete(expense)
    db.commit()


@router.post("/{expense_id}/submit", response_model=ExpenseResponse)
def submit_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)

    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if current_user.role != UserRole.EMPLOYEE or expense.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if expense.status != ExpenseStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only draft expenses can be submitted")

    expense.status = ExpenseStatus.SUBMITTED
    expense.submitted_at = datetime.now(timezone.utc)

    add_audit(db, expense.id, current_user.id, ExpenseAction.SUBMITTED)

    db.commit()
    db.refresh(expense)

    return expense


@router.post("/{expense_id}/approve", response_model=ExpenseResponse)
def approve_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")

    expense = db.get(Expense, expense_id)

    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if expense.status != ExpenseStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only submitted expenses can be approved")

    expense.status = ExpenseStatus.APPROVED
    expense.approved_at = datetime.now(timezone.utc)

    add_audit(db, expense.id, current_user.id, ExpenseAction.APPROVED)

    db.commit()
    db.refresh(expense)

    return expense


@router.post("/{expense_id}/reject", response_model=ExpenseResponse)
def reject_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required")

    expense = db.get(Expense, expense_id)

    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if expense.status != ExpenseStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only submitted expenses can be rejected")

    expense.status = ExpenseStatus.REJECTED

    add_audit(db, expense.id, current_user.id, ExpenseAction.REJECTED)

    db.commit()
    db.refresh(expense)

    return expense


@router.post("/{expense_id}/pay", response_model=ExpenseResponse)
def pay_expense(expense_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.ACCOUNTANT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accountant access required")

    expense = db.get(Expense, expense_id)

    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if expense.status != ExpenseStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only approved expenses can be paid")

    expense.status = ExpenseStatus.PAID
    expense.paid_at = datetime.now(timezone.utc)

    add_audit(db, expense.id, current_user.id, ExpenseAction.PAID)

    db.commit()
    db.refresh(expense)

    return expense

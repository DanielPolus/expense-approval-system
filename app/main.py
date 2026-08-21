from fastapi import FastAPI
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.routers import auth, expenses

app = FastAPI(
    title="Expense Approval System",
)

app.include_router(auth.router)
app.include_router(expenses.router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/health/database")
def database_health(db: Session = Depends(get_db)) -> dict[str, str]:
    result = db.execute(text("SELECT 1")).scalar()
    if result == 1:
        return {"status": "ok", "database": "connected"}
    else:
        return {"status": "error", "database": "unavailable"}

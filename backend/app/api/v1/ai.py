
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.storage.db import SessionLocal
from app.services.ai_service import ai_reroster_suggest, ai_ask
router = APIRouter()
class AIRerosterRequest(BaseModel):
    flight_no: str
class AIAskRequest(BaseModel):
    question: str
class AIDisruptionRequest(BaseModel):
    flight_no: str
    disruption_type: str
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.post("/reroster_suggest")
def reroster_suggest(req: AIRerosterRequest, db: Session = Depends(get_db)):
    return ai_reroster_suggest(db, req.flight_no)
@router.post("/handle_disruption")
def handle_disruption(req: AIDisruptionRequest, db: Session = Depends(get_db)):
    from app.services.ai_service import ai_handle_disruption
    return ai_handle_disruption(db, req.flight_no, req.disruption_type)
@router.post("/ask")
def ai_ask_endpoint(req: AIAskRequest, db: Session = Depends(get_db)):
    return {"answer": ai_ask(db, req.question)}

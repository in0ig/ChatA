from fastapi import APIRouter, HTTPException
from typing import List, Dict
from src.services.session_service import session_service
from src.models.session_model import SessionModel, SessionCreate, SessionUpdate

router = APIRouter(tags=["Sessions"])

@router.get("", response_model=List[SessionModel])
def get_all_sessions():
    try:
        return session_service.get_all_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get all sessions: {str(e)}")

@router.post("", response_model=SessionModel)
def create_session(session_data: SessionCreate):
    try:
        return session_service.create_session(session_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.put("/{session_id}", response_model=SessionModel)
def update_session(session_id: str, session_data: SessionUpdate):
    try:
        updated_session = session_service.update_session(session_id, session_data)
        if not updated_session:
            raise HTTPException(status_code=404, detail="Session not found")
        return updated_session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

@router.delete("/{session_id}")
def delete_session(session_id: str):
    try:
        success = session_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
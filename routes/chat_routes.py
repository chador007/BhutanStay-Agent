from fastapi import APIRouter, HTTPException

from models.schemas import ChatRequest, ChatResponse
from services.chat_service import handle_chat

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):

    try:

        answer = handle_chat(
            request.session_id,
            request.message
        )

        return ChatResponse(
            session_id=request.session_id,
            response=answer
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
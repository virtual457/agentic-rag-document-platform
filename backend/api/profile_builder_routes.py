"""
Profile Builder Chat API Routes

WebSocket and REST endpoints for the Profile Builder Agent
"""
from fastapi import APIRouter, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import json
import asyncio

from src.auth import get_current_active_user, UserInDB
from src.profile.builder import (
    ProfileBuilderAgent,
    ProfileBuilderInput,
    EntityConfirmation,
    ProfileBuilderResponse
)
from src.auth.database import mongodb

router = APIRouter(prefix="/api/profile/builder", tags=["Profile Builder"])

# Global agent instance (singleton for now)
_agent: Optional[ProfileBuilderAgent] = None


def get_agent() -> ProfileBuilderAgent:
    """Get or create the Profile Builder Agent"""
    global _agent
    
    if _agent is None:
        # Initialize with MongoDB connection
        _agent = ProfileBuilderAgent(
            mongodb=mongodb.db,
            chromadb=None,  # TODO: Add ChromaDB
            verbose=True
        )
    
    return _agent


# ============== REST Endpoints ==============

@router.post("/chat", response_model=ProfileBuilderResponse)
async def chat(
    message: str,
    session_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Send a message to the Profile Builder Agent.
    
    The agent will autonomously:
    - Extract entities from your text
    - Ask clarifying questions if needed
    - Present entities for confirmation
    
    Args:
        message: Your message (can be resume text, experience description, etc.)
        session_id: Optional session ID to continue a conversation
        
    Returns:
        Agent's response with any entities for confirmation
    """
    try:
        agent = get_agent()
        
        response = agent.process_input(ProfileBuilderInput(
            user_id=current_user.user_id,
            session_id=session_id,
            message=message
        ))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {str(e)}"
        )


@router.post("/chat/confirm", response_model=ProfileBuilderResponse)
async def confirm_entity(
    confirmation: EntityConfirmation,
    session_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Confirm, edit, or skip an entity.
    
    After the agent presents an entity for confirmation, use this endpoint
    to respond with your decision.
    
    Args:
        confirmation: Your confirmation (confirm/edit/skip)
        session_id: Session ID from the chat
        
    Returns:
        Agent's next response
    """
    try:
        agent = get_agent()
        
        response = agent.confirm_entity(session_id, confirmation)
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Confirmation error: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get current session state.
    
    Returns the current state of a profile builder session including
    pending entities, confirmed entities, and conversation history.
    """
    agent = get_agent()
    state = agent.get_session_state(session_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify user owns this session
    if state.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "session_id": state.session_id,
        "pending_entities": [e.model_dump() for e in state.pending_entities],
        "confirmed_entities": [e.model_dump() for e in state.confirmed_entities],
        "saved_count": len(state.saved_entities),
        "message_count": len(state.messages),
        "created_at": state.created_at.isoformat(),
        "updated_at": state.updated_at.isoformat()
    }


# ============== Streaming Endpoint ==============

@router.post("/chat/stream")
async def chat_stream(
    message: str,
    session_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Stream the agent's thinking process.
    
    Returns a Server-Sent Events stream showing the agent's
    thoughts and actions in real-time.
    """
    
    async def event_generator():
        try:
            agent = get_agent()
            
            # Send start event
            yield f"data: {json.dumps({'event': 'start', 'message': 'Agent thinking...'})}\n\n"
            
            # Process (this is synchronous for now, will add streaming later)
            response = agent.process_input(ProfileBuilderInput(
                user_id=current_user.user_id,
                session_id=session_id,
                message=message
            ))
            
            # Send thinking events (simulated for now)
            yield f"data: {json.dumps({'event': 'thinking', 'thought': 'Analyzing your input...'})}\n\n"
            await asyncio.sleep(0.1)
            
            yield f"data: {json.dumps({'event': 'action', 'action': response.action})}\n\n"
            await asyncio.sleep(0.1)
            
            # Send final response
            yield f"data: {json.dumps({'event': 'complete', 'response': response.model_dump()})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# ============== WebSocket Endpoint ==============

@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str
):
    """
    WebSocket endpoint for real-time chat.
    
    Enables bidirectional communication for:
    - Sending messages
    - Receiving agent responses
    - Real-time entity confirmations
    """
    await websocket.accept()
    
    agent = get_agent()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type", "message")
            
            if message_type == "message":
                # Process user message
                response = agent.process_input(ProfileBuilderInput(
                    user_id=data.get("user_id", "anonymous"),
                    session_id=session_id,
                    message=data.get("message", "")
                ))
                
                await websocket.send_json({
                    "type": "response",
                    "data": response.model_dump()
                })
                
            elif message_type == "confirm":
                # Handle entity confirmation
                confirmation = EntityConfirmation(
                    entity_id=data.get("entity_id"),
                    action=data.get("action"),
                    edited_data=data.get("edited_data")
                )
                
                response = agent.confirm_entity(session_id, confirmation)
                
                await websocket.send_json({
                    "type": "response", 
                    "data": response.model_dump()
                })
                
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })


# ============== Simple Test Endpoint (No Auth) ==============

@router.post("/test")
async def test_chat(message: str, session_id: Optional[str] = None):
    """
    Test endpoint without authentication.
    
    Use this for testing the agent without logging in.
    """
    try:
        agent = get_agent()
        
        response = agent.process_input(ProfileBuilderInput(
            user_id="test_user",
            session_id=session_id,
            message=message
        ))
        
        return response.model_dump()
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "Agent failed. Check server logs."
        }

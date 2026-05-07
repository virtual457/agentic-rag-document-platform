"""
Pydantic Models for Profile Builder Agent
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from datetime import datetime


class EntityType(str, Enum):
    """Types of profile entities"""
    WORK_EXPERIENCE = "work_experience"
    PROJECT = "project"
    EDUCATION = "education"
    SKILL = "skill"
    CERTIFICATION = "certification"
    ACHIEVEMENT = "achievement"
    PERSONAL_INFO = "personal_info"


class ExtractedEntity(BaseModel):
    """An entity extracted from user input"""
    id: str = Field(description="Unique identifier for this entity")
    entity_type: str = Field(description="Type of entity")
    data: Dict[str, Any] = Field(description="Structured data for this entity")
    raw_text: str = Field(default="", description="Original text this was extracted from")
    confidence: float = Field(default=0.9, ge=0, le=1, description="Confidence score 0-1")
    needs_clarification: bool = Field(default=False, description="Whether agent needs more info")
    clarification_question: Optional[str] = Field(default=None, description="Question to ask user")
    field_to_update: Optional[str] = Field(default=None, description="Which field the answer will fill")


class ConversationMessage(BaseModel):
    """A message in the conversation"""
    role: Literal["user", "assistant", "system"] = Field(description="Who sent this message")
    content: str = Field(description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ProfileBuilderState(BaseModel):
    """Current state of the profile builder conversation"""
    session_id: str = Field(description="Unique session identifier")
    user_id: str = Field(description="User ID")
    
    # Compressed context (NEW - replaces sending full message history)
    context: str = Field(
        default="Session started. User building profile. No entities added yet.",
        description="Compressed running context (max 500 tokens) - sent to Gemini instead of full chat history"
    )
    
    # Conversation (for UI display only - NOT sent to Gemini)
    messages: List[ConversationMessage] = Field(default_factory=list)
    
    # Extracted entities
    pending_entities: List[ExtractedEntity] = Field(
        default_factory=list, 
        description="Entities waiting for user confirmation"
    )
    confirmed_entities: List[ExtractedEntity] = Field(
        default_factory=list,
        description="Entities confirmed by user"
    )
    saved_entities: List[str] = Field(
        default_factory=list,
        description="IDs of entities saved to database"
    )
    
    # Current entity being processed
    current_entity_id: Optional[str] = Field(default=None, description="ID of entity currently being worked on")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============== Request/Response Models ==============

class ProfileBuilderInput(BaseModel):
    """Input to the profile builder"""
    user_id: str = Field(description="User ID")
    session_id: Optional[str] = Field(default=None, description="Session ID (for continuing)")
    message: str = Field(description="User's message/input text")
    

class EntityConfirmation(BaseModel):
    """User's response to entity confirmation"""
    entity_id: str = Field(description="ID of entity being confirmed")
    action: Literal["confirm", "edit", "skip"] = Field(description="User's action")
    edited_data: Optional[Dict[str, Any]] = Field(default=None, description="Edited data if action=edit")


class ProfileBuilderResponse(BaseModel):
    """Response from the profile builder"""
    session_id: str
    
    # What the agent wants to show/ask
    message: str = Field(description="Agent's message to display")
    action: str = Field(description="What action the agent took")
    
    # Current entity being worked on (for card display)
    current_entity: Optional[ExtractedEntity] = Field(default=None, description="Entity currently being processed")
    
    # ALL pending entities (so frontend can track/update them)
    pending_entities: List[ExtractedEntity] = Field(default_factory=list, description="All pending entities")
    
    # Progress counts
    pending_count: int = Field(default=0)
    confirmed_count: int = Field(default=0)
    saved_count: int = Field(default=0)
    
    # State
    waiting_for_user: bool = Field(default=False)
    is_complete: bool = Field(default=False)
    
    # If asking a question, which entity/field it's about
    question_for_entity_id: Optional[str] = Field(default=None)
    question_for_field: Optional[str] = Field(default=None)

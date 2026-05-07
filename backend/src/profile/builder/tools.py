"""
LangChain Tools for Profile Builder Agent

These tools allow the ReAct agent to:
1. Extract entities from text
2. Ask clarifying questions
3. Update entities with new information
4. Present entities for confirmation
5. Save entities to MongoDB + ChromaDB
"""
import os
import json
import uuid
from typing import Dict, Any, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aro.llm_adapter import LLMAdapter
from datetime import datetime

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from .models import (
    ExtractedEntity, 
    EntityType,
)


# ============== Tool Input Schemas ==============

class ExtractEntitiesInput(BaseModel):
    """Input for extract_entities tool"""
    text: str = Field(description="Raw text from user to extract entities from")


class AskUserInput(BaseModel):
    """Input for ask_user tool"""
    entity: Dict[str, Any] = Field(description="The entity object that needs clarification")
    question: str = Field(description="Question to ask the user")
    field_to_update: str = Field(description="Which field in the entity this answer will update")
    context: str = Field(description="Why you're asking this question")


class UpdateEntityInput(BaseModel):
    """Input for update_entity tool"""
    entity_id: str = Field(description="ID of entity to update - USE THE UUID FROM extract_entities RESULT (e.g., '6f4d1033'), NOT company name!")
    field: str = Field(description="Field name to update")
    value: Any = Field(description="New value for the field")


class ConfirmEntityInput(BaseModel):
    """Input for confirm_entity tool"""
    entity_id: str = Field(description="ID of entity to confirm - USE THE UUID FROM extract_entities RESULT (e.g., '6f4d1033'), NOT company/project name!")
    entity_type: str = Field(description="Type of entity (work_experience, project, etc)")
    summary: str = Field(description="Human readable summary of the entity")
    data: Dict[str, Any] = Field(description="Structured entity data")


class SaveEntityInput(BaseModel):
    """Input for save_entity tool"""
    entity: Dict[str, Any] = Field(description="The complete entity object to save (must include id, entity_type, data)")
    user_id: str = Field(description="User ID to save for")


# ============== Tools ==============

class ExtractEntitiesTool(BaseTool):
    """Extract structured entities from user's raw text."""
    name: str = "extract_entities"
    description: str = """Extract structured profile entities from user's text.
    
    Use when user pastes resume, describes work history, mentions projects/education/skills.
    Returns list of entities - some may need clarification before confirming.
    """
    args_schema: Type[BaseModel] = ExtractEntitiesInput
    llm: Any = None
    
    def _run(self, text: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        print(f"\n🔍 EXTRACT_ENTITIES TOOL")
        print(f"   Text length: {len(text)} chars")
        print(f"   Text preview: {text[:100]}...")
        
        # Get existing entities from session state (passed via tool context)
        # For now, we'll update the agent to pass this
        
        extraction_prompt = f"""Analyze this text and intelligently extract OR UPDATE profile entities.

You will receive text in this format:
EXISTING ENTITIES: [list of entities already extracted]

NEW TEXT: [new text from user]

Your task:
1. Parse the EXISTING ENTITIES to understand what's already been extracted
2. Analyze the NEW TEXT
3. Decide for each piece of information:
   - Is this UPDATING an existing entity? → Return UPDATED entity with same ID
   - Is this a COMPLETELY NEW entity? → Return NEW entity with new ID
   - Is this a DUPLICATE? → Skip it

DUPLICATE DETECTION:
- Same company + role + dates = duplicate work_experience
- Same project name = duplicate project  
- Same certification name = duplicate certification
- Same institution + degree = duplicate education

UPDATE vs NEW:
- If user says "I also did X at LSEG" and LSEG work_experience exists → UPDATE existing
- If user says "I worked at Google" and no Google work_experience → NEW entity

INPUT TEXT:
{text}

ENTITY TYPES AND REQUIRED STRUCTURE:

1. work_experience:
   - company: string (required)
   - role: string (required)
   - start_date: string (format: "Month YYYY" or "YYYY")
   - end_date: string (format: "Month YYYY" or "YYYY" or "Present")
   - achievements: array of strings (each achievement as separate item)
   - technologies: array of strings (each tech as separate item)

2. project:
   - name: string
   - description: string
   - technologies: array of strings
   - achievements: array of strings

3. education:
   - institution: string
   - degree: string
   - field: string
   - gpa: string
   - start_date: string
   - end_date: string

4. skill:
   - category: string
   - skills: array of strings

5. certification:
   - name: string
   - issuer: string
   - date: string

CRITICAL PARSING RULES:
- achievements MUST be an array where each bullet point or achievement is a separate string
- technologies MUST be an array where each technology is a separate string
- DO NOT put entire paragraphs into start_date or end_date fields
- Extract dates like "June 2024", "August 2024", "2024-08" into proper date fields
- Split comma-separated or line-separated lists into proper arrays
- Remove bullet points, dashes, and numbering from achievements/tech items
- Each array item should be a clean, standalone sentence or phrase

EXAMPLE PARSING:
Input: "I worked from June 2024 to August 2024. During this time I: - Developed pipeline - Built APIs - Optimized queries. Used Java, Python, AWS."
Output:
{{
  "start_date": "June 2024",
  "end_date": "August 2024",
  "achievements": ["Developed pipeline", "Built APIs", "Optimized queries"],
  "technologies": ["Java", "Python", "AWS"]
}}

Return JSON array with these fields:
[
  {{
    "entity_type": "work_experience",
    "entity_id": "abc123",  // Include existing ID if updating, omit if new
    "is_update": true,  // true if updating existing, false if new
    "data": {{
      "company": "LSEG",
      "role": "Software Engineer Intern",
      "start_date": "June 2024",
      "end_date": "August 2024",
      "achievements": ["Achievement 1", "Achievement 2"],
      "technologies": ["Java", "Python"]
    }},
    "confidence": 0.95,
    "needs_clarification": false,
    "clarification_question": null,
    "field_to_update": null
  }}
]"""

        try:
            if self.llm:
                response = self.llm.generate_json(extraction_prompt, max_tokens=4000)
            else:
                response = []
            
            entities = []
            for item in response:
                # Handle field_to_update - convert list to comma-separated string
                field_to_update = item.get("field_to_update")
                if isinstance(field_to_update, list):
                    field_to_update = ",".join(field_to_update)
                
                # Check if this is an update or new entity
                is_update = item.get("is_update", False)
                entity_id = item.get("entity_id") if is_update else str(uuid.uuid4())[:8]
                
                entity = ExtractedEntity(
                    id=entity_id,
                    entity_type=item.get("entity_type", "skill"),
                    data=item.get("data", {}),
                    raw_text=text[:500],
                    confidence=item.get("confidence", 0.8),
                    needs_clarification=item.get("needs_clarification", False),
                    clarification_question=item.get("clarification_question"),
                    field_to_update=field_to_update
                )
                entities.append({
                    **entity.model_dump(),
                    "is_update": is_update
                })
            
            print(f"   ✅ Extracted {len(entities)} entities")
            
            return json.dumps({
                "success": True,
                "entities_found": len(entities),
                "entities": entities
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return json.dumps({"success": False, "error": str(e), "entities": []})


class AskUserTool(BaseTool):
    """Ask user a clarifying question about an entity."""
    name: str = "ask_user"
    description: str = """Ask user a clarifying question to fill missing entity data.
    
    Use when an entity needs_clarification=true.
    Pass the complete entity object along with the question.
    """
    args_schema: Type[BaseModel] = AskUserInput
    
    def _run(
        self,
        entity: Dict[str, Any],
        question: str,
        field_to_update: str,
        context: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        return json.dumps({
            "success": True,
            "action": "ask_user",
            "entity": entity,
            "question": question,
            "field_to_update": field_to_update,
            "context": context,
            "waiting_for_response": True
        })


class UpdateEntityTool(BaseTool):
    """Update an entity field with user's answer."""
    name: str = "update_entity"
    description: str = """Update an entity's field with new information from user.
    
    IMPORTANT: Use the entity UUID from extract_entities result (like '6f4d1033'), NOT company/project name!
    Example: If extract_entities returned id='6f4d1033', use entity_id='6f4d1033' here.
    
    Use after user answers a clarifying question.
    """
    args_schema: Type[BaseModel] = UpdateEntityInput
    
    # Reference to session state - will be set by agent
    session_state: Any = None
    
    def _run(
        self,
        entity_id: str,
        field: str,
        value: Any,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        # This will be handled by the agent's parse logic
        return json.dumps({
            "success": True,
            "action": "update_entity",
            "entity_id": entity_id,
            "field": field,
            "value": value
        })


class ConfirmEntityTool(BaseTool):
    """Present entity to user for confirmation."""
    name: str = "confirm_entity"
    description: str = """Show extracted entity to user for confirmation.
    
    CRITICAL: Use the entity UUID from extract_entities (like '6f4d1033'), NOT company/project name!
    When extract_entities returns {{"id": "6f4d1033", ...}}, you MUST use entity_id="6f4d1033".
    
    Use ONLY when entity is complete.
    Shows entity card with Confirm/Edit/Skip buttons.
    """
    args_schema: Type[BaseModel] = ConfirmEntityInput
    
    def _run(
        self,
        entity_id: str,
        entity_type: str,
        summary: str,
        data: Dict[str, Any],
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        print(f"\n✅ CONFIRM_ENTITY TOOL")
        print(f"   Entity ID: {entity_id}")
        print(f"   Type: {entity_type}")
        
        return json.dumps({
            "success": True,
            "action": "confirm_entity",
            "entity_id": entity_id,
            "entity_type": entity_type,
            "summary": summary,
            "data": data,
            "waiting_for_confirmation": True
        })


class SaveEntityTool(BaseTool):
    """Save confirmed entity to database."""
    name: str = "save_entity"
    description: str = """Save entity to MongoDB and ChromaDB.
    
    Use ONLY after user confirms. Never save without confirmation.
    Pass the complete entity object including id, entity_type, and data.
    """
    args_schema: Type[BaseModel] = SaveEntityInput
    mongodb: Any = None
    chromadb: Any = None
    
    def _run(
        self,
        entity: Dict[str, Any],
        user_id: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        print(f"\n💾 SAVE_ENTITY TOOL")
        print(f"   Entity ID: {entity.get('id')}")
        print(f"   Entity Type: {entity.get('entity_type')}")
        print(f"   User ID: {user_id}")
        
        try:
            # Extract fields from entity object
            entity_id = entity.get("id")
            entity_type = entity.get("entity_type")
            data = entity.get("data", {})
            
            if not entity_id or not entity_type:
                return json.dumps({
                    "success": False, 
                    "error": "Entity must include 'id' and 'entity_type' fields"
                })
            
            mongo_id = None
            chroma_id = None
            
            if self.mongodb is not None:
                doc = {
                    "user_id": user_id,
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "data": data,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                result = self.mongodb.profile_entities.insert_one(doc)
                mongo_id = str(result.inserted_id)
            
            if self.chromadb is not None:
                text = self._create_embedding_text(entity_type, data)
                self.chromadb.add(
                    documents=[text],
                    metadatas=[{
                        "user_id": user_id,
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                    }],
                    ids=[f"{user_id}_{entity_id}"]
                )
                chroma_id = f"{user_id}_{entity_id}"
            
            print(f"   ✅ Saved to MongoDB: {mongo_id}")
            print(f"   ✅ Saved to ChromaDB: {chroma_id}")
            
            return json.dumps({
                "success": True,
                "action": "saved",
                "entity": entity,
                "mongo_id": mongo_id,
                "chroma_id": chroma_id
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return json.dumps({"success": False, "error": str(e)})
    
    def _create_embedding_text(self, entity_type: str, data: Dict[str, Any]) -> str:
        if entity_type == "work_experience":
            return f"Work: {data.get('role', '')} at {data.get('company', '')}. {'. '.join(data.get('achievements', []))}"
        elif entity_type == "project":
            return f"Project: {data.get('name', '')}. {data.get('description', '')}. Tech: {', '.join(data.get('technologies', []))}"
        elif entity_type == "education":
            return f"Education: {data.get('degree', '')} from {data.get('institution', '')}"
        elif entity_type == "skill":
            return f"Skills - {data.get('category', '')}: {', '.join(data.get('skills', []))}"
        return json.dumps(data)


# ============== Tool Factory ==============

class ProfileBuilderTools:
    """Factory for creating profile builder tools"""
    
    def __init__(self, llm=None, mongodb=None, chromadb=None):
        self.llm = llm
        self.mongodb = mongodb
        self.chromadb = chromadb
    
    def get_tools(self) -> List[BaseTool]:
        extract_tool = ExtractEntitiesTool()
        extract_tool.llm = self.llm
        
        ask_tool = AskUserTool()
        update_tool = UpdateEntityTool()
        confirm_tool = ConfirmEntityTool()
        
        save_tool = SaveEntityTool()
        save_tool.mongodb = self.mongodb
        save_tool.chromadb = self.chromadb
        
        return [extract_tool, ask_tool, update_tool, confirm_tool, save_tool]

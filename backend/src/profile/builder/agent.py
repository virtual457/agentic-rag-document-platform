"""
Profile Builder ReAct Agent

Flow:
1. User provides text → Extract entities
2. For each entity:
   - If needs_clarification → Ask question → User answers → Update entity → Show card
   - If complete → Show card for confirmation
3. User confirms → Save to DB
"""
import os
import sys
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from aro.model_config import ModelConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from .tools import ProfileBuilderTools
from .models import (
    ProfileBuilderState,
    ProfileBuilderInput,
    ProfileBuilderResponse,
    ConversationMessage,
    ExtractedEntity,
    EntityConfirmation
)


SYSTEM_PROMPT = """You are a Profile Builder Assistant helping users build their professional profile.

WORKFLOW:
1. When user provides text → call extract_entities with BOTH:
   - The new text from user
   - Existing entities from SESSION STATE (if any)
   Then STOP
2. Process entities ONE at a time:
   - If needs_clarification=true → call ask_user, then STOP
   - If complete → call confirm_entity, then STOP
3. When user answers → call confirm_entity, then STOP
4. After user confirms → call save_entity ONCE, then STOP

EXISTING ENTITIES:
- You'll see "EXISTING ENTITIES (for duplicate detection): [...]" in context
- When calling extract_entities, include this info in the text parameter
- Format the text like:
  "EXISTING ENTITIES: {json from context}\n\nNEW TEXT: {user's message}"
- This allows the extraction LLM to detect duplicates and merge data

STOPPING RULES - CRITICAL:
- After calling extract_entities → STOP immediately
- After calling ask_user → STOP and wait
- After calling confirm_entity → STOP and wait
- After calling save_entity → STOP immediately
- NEVER call the same tool twice in a row
- NEVER call more than 2 tools per turn

For confirm_entity:
- DO NOT ask "Shall I confirm?"
- JUST CALL confirm_entity then STOP
- UI shows card automatically

For save_entity - use complete entity object:
{
  "entity": {"id": "abc123", "entity_type": "certification", "data": {...}},
  "user_id": "user123"
}
"""


class ProfileBuilderAgent:
    def __init__(self, mongodb=None, chromadb=None, verbose: bool = True):
        self.verbose = verbose
        self.mongodb = mongodb
        self.chromadb = chromadb
        
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY required")
        
        # Enable detailed LangChain logging
        import langchain
        langchain.debug = True  # Shows full prompt/response chain
        
        self.llm = ChatGoogleGenerativeAI(
            model=ModelConfig.LANGCHAIN_MODEL,  # Centralized config!
            google_api_key=api_key,
            temperature=0.3,
            verbose=True,  # Enable LLM logging
        )
        
        tool_factory = ProfileBuilderTools(
            llm=self._create_extraction_llm(),
            mongodb=mongodb,
            chromadb=chromadb
        )
        self.tools = tool_factory.get_tools()
        
        self.agent = create_react_agent(model=self.llm, tools=self.tools)
        self.sessions: Dict[str, ProfileBuilderState] = {}
        self.recursion_limit = 10
        
        # Track pending questions: session_id -> {entity_id, field_to_update}
        self.pending_questions: Dict[str, Dict] = {}
    
    def _create_extraction_llm(self):
        from aro.llm_adapter import create_llm_adapter
        return create_llm_adapter("gemini")
    
    def _get_or_create_session(self, user_id: str, session_id: Optional[str] = None) -> ProfileBuilderState:
        if session_id and session_id in self.sessions:
            return self.sessions[session_id]
        
        new_session_id = session_id or str(uuid.uuid4())[:8]
        state = ProfileBuilderState(session_id=new_session_id, user_id=user_id)
        self.sessions[new_session_id] = state
        return state
    
    def _find_entity(self, state: ProfileBuilderState, entity_id: str) -> Optional[ExtractedEntity]:
        """Find entity in pending list"""
        for e in state.pending_entities:
            if e.id == entity_id:
                return e
        return None
    
    def _get_current_entity(self, state: ProfileBuilderState) -> Optional[ExtractedEntity]:
        """Get the current entity being processed"""
        if state.current_entity_id:
            return self._find_entity(state, state.current_entity_id)
        return None
    
    def _update_context(self, state: ProfileBuilderState, user_message: str, action: str, agent_response: str):
        """Update compressed context after each turn (keeps tokens constant)"""
        
        # Build context update
        entities_summary = []
        if state.pending_entities:
            for e in state.pending_entities[:3]:  # Max 3 for brevity
                entities_summary.append(f"{e.entity_type}: {e.data.get('company', e.data.get('name', 'pending'))}")
        
        new_context_piece = f"""Last turn: User said '{user_message[:80]}...', Agent action: {action}, Response: '{agent_response[:60]}...'
Pending entities: {', '.join(entities_summary) if entities_summary else 'none'}
Saved count: {len(state.saved_entities)}"""
        
        # Append to context
        updated_context = f"{state.context}\n{new_context_piece}"
        
        # If context too long, compress with Gemini
        MAX_CONTEXT_CHARS = 2000  # ~500 tokens
        if len(updated_context) > MAX_CONTEXT_CHARS:
            print(f"\n🗃️  Context too long ({len(updated_context)} chars), compressing...")
            
            compression_prompt = f"""Compress this session context to max 400 tokens while keeping critical info:

{updated_context}

Focus on:
- Number and types of entities (work_experience, projects, education, etc.)
- What's saved vs pending
- What user is currently working on
- Next expected action

DO NOT include:
- Full conversation verbatim
- Detailed entity data
- Repetitive information

Return ONLY the compressed context summary (plain text, no markdown):"""
            
            try:
                compressed = self.llm.invoke([HumanMessage(content=compression_prompt)]).content
                state.context = compressed.strip()
                print(f"   ✅ Compressed to {len(state.context)} chars (~{len(state.context)//4} tokens)")
            except Exception as e:
                print(f"   ⚠️  Compression failed: {e}")
                # Fallback: Keep recent info only
                lines = updated_context.split('\n')
                state.context = '\n'.join(lines[-10:])  # Last 10 lines
        else:
            state.context = updated_context
        
        state.updated_at = datetime.utcnow()
    
    def process_input(self, input_data: ProfileBuilderInput) -> ProfileBuilderResponse:
        """Process user input using COMPRESSED CONTEXT (not full chat history)"""
        print(f"\n{'='*60}")
        print(f"🤖 AGENT - process_input()")
        print(f"User: {input_data.user_id}, Session: {input_data.session_id}")
        print(f"Message: {input_data.message[:100]}...")
        print(f"{'='*60}\n")
        
        state = self._get_or_create_session(input_data.user_id, input_data.session_id)
        
        # Save message for UI display only (NOT sent to Gemini)
        state.messages.append(ConversationMessage(role="user", content=input_data.message))
        
        # Build prompt with COMPRESSED CONTEXT (not full chat history!)
        print("\n📝 Building prompt with COMPRESSED CONTEXT:")
        print(f"   Current context length: {len(state.context)} chars (~{len(state.context)//4} tokens)")
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            SystemMessage(content=f"""RUNNING CONTEXT (Session summary - DO NOT repeat this in responses):
{state.context}

ENTITIES STATUS:
- Pending: {len(state.pending_entities)}
- Confirmed: {len(state.confirmed_entities)}
- Saved: {len(state.saved_entities)}
"""),
            HumanMessage(content=input_data.message)
        ]
        
        print(f"   Total messages to agent: {len(messages)}")
        print(f"   Estimated total tokens: ~{sum(len(str(m.content))//4 for m in messages)}\n")
        
        # Run agent with recursion limit
        config = {"recursion_limit": self.recursion_limit}
        
        print(f"\n{'🔵'*30}")
        print("🤖 LANGCHAIN REACT AGENT STARTING")
        print(f"{'🔵'*30}")
        print(f"Messages to agent: {len(messages)}")
        for i, msg in enumerate(messages, 1):
            msg_type = type(msg).__name__
            content_preview = str(msg.content)[:100] if hasattr(msg, 'content') else str(msg)[:100]
            print(f"  [{i}] {msg_type}: {content_preview}...")
        print(f"{'='*60}\n")
        
        result = self.agent.invoke({"messages": messages}, config=config)
        
        print(f"\n{'🟢'*30}")
        print("✅ LANGCHAIN AGENT COMPLETED")
        print(f"{'🟢'*30}")
        print(f"Result messages: {len(result.get('messages', []))}")
        print(f"{'='*60}\n")
        
        # Parse result
        output = ""
        action_taken = "thinking"
        waiting_for_user = False
        question_entity_id = None
        question_field = None
        
        print("\n" + "="*60)
        print("🔍 PARSING AGENT RESULT (ReAct Loop)")
        print("="*60)
        
        for idx, msg in enumerate(result.get("messages", []), 1):
            msg_type = type(msg).__name__
            print(f"\n[{idx}] Message Type: {msg_type}")
            
            # Print content for ALL message types (handle both string and list)
            if hasattr(msg, 'content'):
                content = msg.content
                
                # Handle different content formats
                if isinstance(content, list):
                    # Extract text from list of parts
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict) and 'text' in part:
                            text_parts.append(part['text'])
                        elif isinstance(part, str):
                            text_parts.append(part)
                    content_str = ' '.join(text_parts)[:300] if text_parts else "(no text)"
                elif isinstance(content, str):
                    content_str = content[:300]
                else:
                    content_str = str(content)[:300]
                
                print(f"  💬 Content: {content_str}...")
            
            # Log AI message specifics
            if msg_type == "AIMessage" or (hasattr(msg, 'type') and msg.type == "ai"):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"  🔧 Has tool_calls: {len(msg.tool_calls)}")
                else:
                    print(f"  🔧 Has tool_calls: 0 (just text response)")
            
            # Tool calls
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                print("  ⚙️  TOOL CALLS DETECTED:")
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    
                    print(f"\n  🔧 Tool: {tool_name}")
                    print(f"     Args: {json.dumps(tool_args, indent=6)[:300]}...")
                    
                    print(f"\n🔧 TOOL CALL: {tool_name}")
                    print(f"   Args: {json.dumps(tool_args, indent=2)[:200]}...")
                    
                    if tool_name == "ask_user":
                        action_taken = "ask_user"
                        output = tool_args.get("question", "")
                        waiting_for_user = True
                        
                        # Entity might be JSON string or dict - handle both
                        entity_obj = tool_args.get("entity", {})
                        if isinstance(entity_obj, str):
                            try:
                                entity_obj = json.loads(entity_obj)
                            except:
                                entity_obj = {}
                        
                        entity_id = entity_obj.get("id")
                        state.current_entity_id = entity_id
                        
                    elif tool_name == "save_entity":
                        action_taken = "saved"
            
            # Tool results
            if hasattr(msg, 'type') and msg.type == "tool":
                print("  📤 TOOL RESULT:")
                try:
                    content = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
                    print(f"     Content: {content[:200]}...")
                    obs = json.loads(content)
                    
                    # Extract entities result - add to pending or update existing
                    if obs.get("entities"):
                        for e_data in obs["entities"]:
                            is_update = e_data.get("is_update", False)
                            
                            entity = ExtractedEntity(
                                id=e_data.get("id", str(uuid.uuid4())[:8]),
                                entity_type=e_data.get("entity_type", "skill"),
                                data=e_data.get("data", {}),
                                raw_text=e_data.get("raw_text", ""),
                                confidence=e_data.get("confidence", 0.8),
                                needs_clarification=e_data.get("needs_clarification", False),
                                clarification_question=e_data.get("clarification_question"),
                                field_to_update=e_data.get("field_to_update")
                            )
                            
                            if is_update:
                                # Replace existing entity with same ID
                                existing = self._find_entity(state, entity.id)
                                if existing:
                                    state.pending_entities.remove(existing)
                                    print(f"   🔄 UPDATING existing entity: {entity.id}")
                                state.pending_entities.append(entity)
                            else:
                                # Add new entity
                                print(f"   ➕ ADDING new entity: {entity.id}")
                                state.pending_entities.append(entity)
                        
                        # Set first entity as current
                        if state.pending_entities and not state.current_entity_id:
                            state.current_entity_id = state.pending_entities[0].id
                    
                    # Confirm result
                    if obs.get("action") == "confirm_entity":
                        entity_id = obs.get("entity_id")
                        state.current_entity_id = entity_id
                        action_taken = "confirm_entity"  # FIX: Update action_taken!
                    
                    # Save result
                    if obs.get("action") == "saved" and obs.get("success"):
                        saved_entity = obs.get("entity", {})
                        entity_id = saved_entity.get("id")
                        if entity_id:
                            state.saved_entities.append(entity_id)
                        
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # AI response
            if hasattr(msg, 'type') and msg.type == "ai" and hasattr(msg, 'content'):
                if isinstance(msg.content, str) and msg.content:
                    print(f"  🤖 AI RESPONSE:")
                    print(f"     {msg.content[:150]}...")
                    output = msg.content
        
        if output:
            state.messages.append(ConversationMessage(role="assistant", content=output))
        
        # UPDATE CONTEXT for next turn (compress session state)
        self._update_context(state, input_data.message, action_taken, output)
        
        # Get current entity for display
        current_entity = self._get_current_entity(state)
        
        print(f"\n📤 RESPONSE:")
        print(f"   Action: {action_taken}")
        print(f"   Current Entity: {current_entity.id if current_entity else 'None'}")
        print(f"   Pending: {len(state.pending_entities)}, Confirmed: {len(state.confirmed_entities)}, Saved: {len(state.saved_entities)}")
        print(f"{'='*60}\n")
        
        return ProfileBuilderResponse(
            session_id=state.session_id,
            message=output or "Processing...",
            action=action_taken,
            current_entity=current_entity,
            pending_entities=[e.model_copy() for e in state.pending_entities],
            pending_count=len(state.pending_entities),
            confirmed_count=len(state.confirmed_entities),
            saved_count=len(state.saved_entities),
            waiting_for_user=waiting_for_user,
            is_complete=False,
            question_for_entity_id=question_entity_id,
            question_for_field=question_field
        )
    
    def confirm_entity(self, session_id: str, confirmation: EntityConfirmation) -> ProfileBuilderResponse:
        if session_id not in self.sessions:
            return ProfileBuilderResponse(
                session_id=session_id,
                message="Session not found.",
                action="error",
                pending_entities=[],
                is_complete=False
            )
        
        state = self.sessions[session_id]
        entity = self._find_entity(state, confirmation.entity_id)
        
        if not entity:
            return ProfileBuilderResponse(
                session_id=session_id,
                message="Entity not found.",
                action="error",
                pending_entities=[e.model_copy() for e in state.pending_entities],
                is_complete=False
            )
        
        if confirmation.action == "confirm":
            state.pending_entities.remove(entity)
            state.confirmed_entities.append(entity)
            state.current_entity_id = None
            
            # Provide complete entity object
            entity_obj = {"id": entity.id, "entity_type": entity.entity_type, "data": entity.data}
            save_message = f"""User confirmed {entity.entity_type}.
Entity: {json.dumps(entity_obj, indent=2)}
User ID: {state.user_id}
Use save_entity tool."""
            
            return self.process_input(ProfileBuilderInput(
                user_id=state.user_id,
                session_id=session_id,
                message=save_message
            ))
        
        elif confirmation.action == "edit":
            if confirmation.edited_data:
                entity.data = confirmation.edited_data
            state.pending_entities.remove(entity)
            state.confirmed_entities.append(entity)
            state.current_entity_id = None
            
            # Provide complete entity object
            entity_obj = {"id": entity.id, "entity_type": entity.entity_type, "data": entity.data}
            save_message = f"""User edited {entity.entity_type}.
Entity: {json.dumps(entity_obj, indent=2)}
User ID: {state.user_id}
Use save_entity tool."""
            
            return self.process_input(ProfileBuilderInput(
                user_id=state.user_id,
                session_id=session_id,
                message=save_message
            ))
        
        elif confirmation.action == "skip":
            state.pending_entities.remove(entity)
            state.current_entity_id = None
            
            if state.pending_entities:
                state.current_entity_id = state.pending_entities[0].id
                return self.process_input(ProfileBuilderInput(
                    user_id=state.user_id,
                    session_id=session_id,
                    message="User skipped. Process next entity."
                ))
            else:
                return ProfileBuilderResponse(
                    session_id=session_id,
                    message="All done! Add more or go to Generate.",
                    action="complete",
                    pending_entities=[],
                    pending_count=0,
                    confirmed_count=len(state.confirmed_entities),
                    saved_count=len(state.saved_entities),
                    is_complete=True
                )
        
        return ProfileBuilderResponse(
            session_id=session_id,
            message="Unknown action.",
            action="error",
            pending_entities=[e.model_copy() for e in state.pending_entities],
            is_complete=False
        )
    
    def get_session_state(self, session_id: str) -> Optional[ProfileBuilderState]:
        return self.sessions.get(session_id)

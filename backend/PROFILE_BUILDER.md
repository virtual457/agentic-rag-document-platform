# Profile Builder - LangChain ReAct Agent

## 🎯 What It Does

The Profile Builder is an **autonomous AI agent** that helps users build their professional profile through conversation. Unlike hardcoded logic, the agent **decides on its own** what to do next.

## 🏗️ Architecture

```
User Input
    ↓
┌─────────────────────────────────────────┐
│          ReAct Agent (LangChain)         │
│                                          │
│  Thought: "User provided work history"   │
│  Action: extract_entities                │
│  Observation: Found 2 work experiences   │
│                                          │
│  Thought: "Need user to confirm LSEG"    │
│  Action: confirm_entity                  │
│  Observation: Waiting for user           │
│                                          │
│  [User confirms]                         │
│                                          │
│  Thought: "User confirmed, save it"      │
│  Action: save_entity                     │
│  Observation: Saved to MongoDB           │
└─────────────────────────────────────────┘
    ↓
Response to Frontend
```

## 🔧 Tools Available to Agent

| Tool | Purpose | When Agent Uses It |
|------|---------|-------------------|
| `extract_entities` | Parse user text into structured entities | When user provides new text about themselves |
| `ask_user` | Ask clarifying question | When entity is missing critical info |
| `confirm_entity` | Show entity to user for verification | Before saving any entity |
| `save_entity` | Store to MongoDB + ChromaDB | After user confirms |
| `request_more_info` | Prompt for more details | When profile section is incomplete |

## 📁 File Structure

```
backend/src/profile/builder/
├── __init__.py          # Exports
├── models.py            # Pydantic models (entities, state, requests)
├── tools.py             # LangChain tools the agent can use
└── agent.py             # The ReAct agent itself

backend/api/
└── profile_builder_routes.py   # FastAPI endpoints
```

## 🚀 API Endpoints

### Chat with Agent
```bash
POST /api/profile/builder/test
?message=I worked at Google for 5 years as a SWE
```

### With Authentication
```bash
POST /api/profile/builder/chat
Authorization: Bearer <token>
Body: { "message": "...", "session_id": "optional" }
```

### Confirm Entity
```bash
POST /api/profile/builder/chat/confirm
Body: {
  "entity_id": "abc123",
  "action": "confirm",  # or "edit" or "skip"
  "session_id": "xyz789",
  "edited_data": {}     # if action=edit
}
```

### Streaming (SSE)
```bash
POST /api/profile/builder/chat/stream
?message=...
```

### WebSocket
```javascript
ws://localhost:8000/api/profile/builder/ws/{session_id}

// Send message
{ "type": "message", "user_id": "...", "message": "..." }

// Confirm entity
{ "type": "confirm", "entity_id": "...", "action": "confirm" }
```

## 🧪 Testing

```bash
# Install dependencies first
cd backend
pip install -r requirements.txt

# Run test (no server needed)
python test_profile_builder.py

# Test API endpoint (server must be running)
python test_profile_builder.py --api
```

## 💡 How It's Different

### Old Approach (Hardcoded)
```python
def process(text):
    entities = extract(text)  # Always extract
    for e in entities:
        show_to_user(e)       # Always show
        if user_confirms:
            save(e)           # Always save
```

### New Approach (Agent Decides)
```
Agent thinks: "User gave me their resume text"
Agent decides: "I should extract entities"
Agent observes: "Found 3 entities"
Agent thinks: "First entity has missing dates"
Agent decides: "I should ask user for dates"
Agent observes: "User provided dates"
Agent thinks: "Now I can confirm with user"
Agent decides: "Show entity for confirmation"
...
```

The agent uses **reasoning** to decide what to do, not a fixed script.

## 🔄 Session Management

Sessions are stored in memory (will migrate to Redis/MongoDB later):

```python
sessions = {
    "session_123": ProfileBuilderState(
        user_id="user_456",
        messages=[...],
        pending_entities=[...],
        confirmed_entities=[...],
        saved_entities=[...]
    )
}
```

## 🎨 Frontend Integration

The response structure is designed for easy frontend consumption:

```json
{
  "session_id": "abc123",
  "message": "I found your LSEG experience. Is this correct?",
  "action": "confirm_entity",
  "entity_for_confirmation": {
    "id": "ent_001",
    "entity_type": "work_experience",
    "data": {
      "company": "LSEG",
      "role": "Senior SWE",
      "achievements": ["Built pipeline", "Reduced latency"]
    },
    "confidence": 0.95
  },
  "pending_count": 2,
  "confirmed_count": 0,
  "waiting_for_user": true,
  "is_complete": false
}
```

Frontend just needs to:
1. Display `message`
2. If `entity_for_confirmation` exists, show confirmation card
3. When user clicks Confirm/Edit/Skip, call `/chat/confirm`

## 📝 Next Steps

1. **Add ChromaDB integration** - Store entities for RAG search
2. **Add streaming** - Show agent's thinking in real-time
3. **Add persistence** - Move sessions to MongoDB
4. **Frontend chat UI** - Build the React interface

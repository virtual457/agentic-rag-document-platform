# 🔐 Authentication System Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Setup MongoDB Atlas

1. **Create Account**: Go to https://www.mongodb.com/cloud/atlas/register
2. **Create Cluster**:
   - Choose **FREE** M0 tier
   - Select closest region
   - Name: `lmaro-cluster`

3. **Create Database User**:
   - Go to "Database Access"
   - Click "Add New Database User"
   - Username: `lmaro_admin`
   - Password: Generate strong password (save it!)
   - Role: "Read and write to any database"

4. **Configure Network Access**:
   - Go to "Network Access"
   - Click "Add IP Address"
   - Select "Allow Access from Anywhere" (`0.0.0.0/0`)
   - (For development only - restrict in production!)

5. **Get Connection String**:
   - Click "Connect" → "Connect your application"
   - Driver: Python, Version: 3.12 or later
   - Copy connection string:
   ```
   mongodb+srv://lmaro_admin:<password>@lmaro-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### 3. Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Copy from example
cp .env.example .env
```

Edit `.env` and add your values:

```env
# LLM Provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here

# MongoDB Atlas (IMPORTANT: Replace <password> with actual password!)
MONGODB_URI=mongodb+srv://lmaro_admin:YOUR_PASSWORD_HERE@lmaro-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=lmaro_db

# JWT Secret (generate random string)
SECRET_KEY=change-this-to-something-very-random-and-secure
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# ChromaDB Path
CHROMADB_PATH=./chromadb_store
```

**Generate Secret Key** (run in Python):
```python
import secrets
print(secrets.token_urlsafe(32))
# Use this output for SECRET_KEY
```

### 4. Start Backend Server

```bash
cd backend
python main.py
```

You should see:
```
✓ Connected to MongoDB: lmaro_db
✓ Database indexes created
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Test Authentication

Open new terminal:
```bash
cd backend
python test_auth.py
```

Expected output:
```
=== Testing Health Endpoint ===
Status: 200
✓ MongoDB connected

=== Testing User Registration ===
✓ User registered successfully!

=== Testing User Login ===
✓ Login successful!

✓ All tests completed!
```

### 6. Test in Browser

1. **API Docs**: http://localhost:8000/docs
2. **Try Registration**:
   - Click "POST /api/auth/register"
   - Click "Try it out"
   - Fill in user data:
   ```json
   {
     "username": "chandan",
     "email": "chandan@example.com",
     "password": "password123",
     "full_name": "Chandan Gowda"
   }
   ```
   - Click "Execute"
   - You'll get a JWT token!

3. **Test Protected Route**:
   - Copy the `access_token` from registration response
   - Click "Authorize" button (top right)
   - Paste token
   - Now try "GET /api/auth/me"

## 🗄️ Database Structure

### MongoDB Collections

```javascript
// users collection
{
  "username": "chandan",
  "email": "chandan@example.com",
  "full_name": "Chandan Gowda",
  "hashed_password": "$2b$12$...",
  "created_at": "2024-01-01T00:00:00",
  "is_active": true
}

// resumes collection (coming soon)
{
  "username": "chandan",
  "job_id": "job1",
  "resume_data": {...},
  "created_at": "2024-01-01T00:00:00"
}

// jobs collection (coming soon)
{
  "job_id": "job1",
  "company": "Google",
  "role": "SWE",
  "jd_text": "..."
}
```

### ChromaDB Structure (Local)

```
chromadb_store/
├── chandan/              # User-specific vector DB
│   ├── chroma.sqlite3
│   └── [embedding data]
├── john/
│   ├── chroma.sqlite3
│   └── [embedding data]
```

## 🔧 API Endpoints

### Public Endpoints (No Auth Required)

```bash
POST   /api/auth/register     # Register new user
POST   /api/auth/login        # Login (get JWT token)
GET    /health                # Health check
```

### Protected Endpoints (Requires JWT Token)

```bash
GET    /api/auth/me           # Get current user info
POST   /api/auth/logout       # Logout (client deletes token)
```

### Usage Example (cURL)

```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'

# Response includes access_token
# {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...", "user": {...}}

# 2. Use token for protected routes
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

## 🐛 Troubleshooting

### "Could not connect to MongoDB"
- Check `MONGODB_URI` in `.env`
- Replace `<password>` with actual password
- Check IP whitelist in MongoDB Atlas

### "Duplicate key error"
- User already exists
- Try different username/email
- Or use login endpoint instead

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Permission denied on port 8000"
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8000   # Windows
```

## 🚀 Next Steps

1. ✅ User auth working!
2. 🔄 Next: Add ChromaDB + RAG system
3. 🔄 Then: Protect existing resume endpoints
4. 🔄 Finally: Build frontend login/register pages

## 📚 Resources

- [FastAPI OAuth2](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [MongoDB Python Driver](https://pymongo.readthedocs.io/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)

"""
Profile management API routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import Optional
import json

from src.auth import get_current_active_user, UserInDB, user_auth_manager
from src.auth.models import ProfileUpdateRequest, ProfileCompletionStatus
from src.profile.analyzer import ProfileAnalyzer
from aro.llm_adapter import create_llm_adapter

router = APIRouter(prefix="/api/profile", tags=["Profile Management"])

# Initialize LLM for profile analysis
llm = create_llm_adapter("gemini")
profile_analyzer = ProfileAnalyzer(llm)


@router.get("/me")
async def get_my_profile(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user's profile data
    
    Returns profile with completion status
    """
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "profile": current_user.profile.model_dump(),
        "profile_completion": current_user.profile_completion.model_dump()
    }


@router.get("/completion")
async def get_profile_completion(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get profile completion status only
    
    Returns completion percentage, status, and feedback
    """
    return current_user.profile_completion.model_dump()


@router.post("/update")
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update user profile and optionally analyze completeness
    
    - **profile_data**: Profile data (full or partial update)
    - **analyze**: Whether to run LLM analysis (default: true)
    
    Returns updated profile with new completion status
    """
    try:
        # Merge with existing profile
        existing_profile = current_user.profile.model_dump()
        
        # Deep merge the profile data
        for key, value in request.profile_data.items():
            if key in existing_profile:
                if isinstance(value, dict):
                    existing_profile[key].update(value)
                else:
                    existing_profile[key] = value
        
        # Update in database
        from bson import ObjectId
        user_auth_manager.db.users.update_one(
            {"_id": ObjectId(current_user.user_id)},
            {"$set": {"profile": existing_profile}}
        )
        
        # Analyze if requested
        if request.analyze:
            analysis_result = profile_analyzer.analyze_profile(existing_profile)
            
            # Update completion status in database
            user_auth_manager.db.users.update_one(
                {"_id": ObjectId(current_user.user_id)},
                {"$set": {"profile_completion": analysis_result}}
            )
            
            return {
                "message": "Profile updated and analyzed",
                "profile": existing_profile,
                "completion": analysis_result
            }
        else:
            return {
                "message": "Profile updated (not analyzed)",
                "profile": existing_profile
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.post("/upload-resume")
async def upload_resume_file(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Upload resume file (PDF/DOCX) and extract data using LLM
    
    The LLM will:
    1. Extract structured data from resume
    2. Populate user profile
    3. Analyze completeness
    
    Returns extracted profile with completion status
    """
    try:
        # Read file content
        content = await file.read()
        
        # TODO: Parse PDF/DOCX (using python-docx, PyPDF2)
        # For now, return placeholder
        
        return {
            "message": "Resume upload feature coming soon!",
            "filename": file.filename,
            "size": len(content)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume upload failed: {str(e)}"
        )


@router.post("/analyze")
async def analyze_current_profile(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Analyze current profile completeness using LLM
    
    Returns:
    - Completion percentage (0-100)
    - Status (incomplete/needs_improvement/ready)
    - Specific feedback on what's missing
    - Suggested next steps
    """
    try:
        profile_data = current_user.profile.model_dump()
        
        # Run LLM analysis
        analysis_result = profile_analyzer.analyze_profile(profile_data)
        
        # Update in database
        from bson import ObjectId
        user_auth_manager.db.users.update_one(
            {"_id": ObjectId(current_user.user_id)},
            {"$set": {"profile_completion": analysis_result}}
        )
        
        return analysis_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile analysis failed: {str(e)}"
        )


@router.get("/status")
async def get_profile_status(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Quick status check
    
    Returns simple status without full analysis
    """
    completion = current_user.profile_completion
    
    return {
        "percentage": completion.percentage,
        "status": completion.status,
        "message": profile_analyzer.get_status_message(completion.status),
        "color": profile_analyzer.get_completion_color(completion.percentage)
    }

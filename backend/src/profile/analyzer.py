"""
Profile Analyzer - LLM-powered profile completion assessment
"""
import json
from typing import Dict, Any
from datetime import datetime


class ProfileAnalyzer:
    """Analyzes user profile completeness using LLM"""
    
    def __init__(self, llm_adapter):
        """
        Initialize analyzer with LLM adapter
        
        Args:
            llm_adapter: LLM adapter instance (from aro.llm_adapter)
        """
        self.llm = llm_adapter
    
    def analyze_profile(self, profile_data: dict) -> Dict[str, Any]:
        """
        Analyze profile completeness using LLM
        
        Args:
            profile_data: User profile dictionary
            
        Returns:
            {
                "percentage": 75,
                "status": "needs_improvement",
                "feedback": "Profile is good but needs more project details...",
                "missing_sections": ["projects", "certifications"],
                "last_analyzed": "2024-01-01T00:00:00"
            }
        """
        
        prompt = self._build_analysis_prompt(profile_data)
        
        try:
            # Call LLM for analysis
            response = self.llm.generate(
                prompt=prompt,
                max_tokens=1000,
                response_format="json"
            )
            
            # Parse LLM response
            analysis = json.loads(response)
            
            # Validate and normalize
            result = {
                "percentage": min(100, max(0, analysis.get("percentage", 0))),
                "status": self._determine_status(analysis.get("percentage", 0)),
                "feedback": analysis.get("feedback", ""),
                "missing_sections": analysis.get("missing_sections", []),
                "last_analyzed": datetime.utcnow()
            }
            
            return result
            
        except Exception as e:
            print(f"⚠️ Profile analysis failed: {e}")
            # Return conservative estimate on error
            return {
                "percentage": 0,
                "status": "incomplete",
                "feedback": "Unable to analyze profile. Please try again.",
                "missing_sections": [],
                "last_analyzed": datetime.utcnow()
            }
    
    def _build_analysis_prompt(self, profile_data: dict) -> str:
        """Build prompt for LLM analysis"""
        
        prompt = f"""You are a professional resume analyzer. Analyze the completeness of this user profile for generating tailored resumes.

USER PROFILE:
{json.dumps(profile_data, indent=2)}

ANALYSIS CRITERIA:
- Personal Info (name, email, phone, location): 15%
- Education (degrees, institutions, dates): 15%
- Work Experience (roles, companies, dates, achievements): 35%
- Skills (technical skills, tools, frameworks): 15%
- Projects (descriptions, technologies, outcomes): 15%
- Certifications & Achievements: 5%

RESPONSE FORMAT (JSON only):
{{
    "percentage": <0-100>,
    "feedback": "<specific feedback on what's good and what's missing>",
    "missing_sections": ["<list of missing or incomplete sections>"],
    "strengths": ["<what's complete and well-detailed>"],
    "next_steps": "<what user should add next for best improvement>"
}}

RULES:
1. Be specific about what's missing
2. Percentage must reflect actual completeness
3. Empty sections = 0% for that section
4. Vague/incomplete sections = partial credit
5. Well-detailed sections = full credit

Analyze the profile and respond with JSON only:"""

        return prompt
    
    def _determine_status(self, percentage: int) -> str:
        """
        Determine profile status based on percentage
        
        Args:
            percentage: Completion percentage (0-100)
            
        Returns:
            Status string
        """
        if percentage >= 90:
            return "ready"  # Ready to generate high-quality resumes
        elif percentage >= 60:
            return "needs_improvement"  # Can generate but needs more data
        else:
            return "incomplete"  # Not enough data to generate
    
    def get_completion_color(self, percentage: int) -> str:
        """Get color for completion percentage (for UI)"""
        if percentage >= 90:
            return "var(--google-green)"  # Green
        elif percentage >= 60:
            return "var(--google-yellow)"  # Yellow
        else:
            return "var(--google-red)"  # Red
    
    def get_status_message(self, status: str) -> str:
        """Get user-friendly status message"""
        messages = {
            "ready": "✓ Profile is ready for resume generation",
            "needs_improvement": "⚠️ Profile needs more details for better results",
            "incomplete": "⚠️ Profile is incomplete - add more information"
        }
        return messages.get(status, "Unknown status")

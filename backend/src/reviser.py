"""
Reviser - Improves resume based on feedback
"""
import json
from typing import Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aro.llm_adapter import LLMAdapter


class Reviser:
    def __init__(self, llm: LLMAdapter, debug: bool = False):
        self.llm = llm
        self.debug = debug
    
    def revise(
        self,
        current_resume: Dict[str, Any],
        jd_text: str,
        user_profile: Dict[str, Any],
        feedback: str,
        revision_type: str = "evaluation"  # "evaluation" or "factuality"
    ) -> Dict[str, Any]:
        """
        Revise resume based on feedback
        
        Args:
            current_resume: Current resume JSON
            jd_text: Job description
            user_profile: User profile
            feedback: Feedback from evaluator or factuality checker
            revision_type: Type of revision needed
        
        Returns:
            Improved resume JSON
        """
        prompt = self._build_prompt(current_resume, jd_text, user_profile, feedback, revision_type)
        
        if self.debug:
            print("\n" + "="*60)
            print(f"DEBUG: REVISER PROMPT ({revision_type})")
            print("="*60)
            print(f"Prompt length: {len(prompt)} characters (~{len(prompt)//4} tokens)")
            print("="*60 + "\n")
        
        # Needs tokens for large profile + revised resume output
        # Use high-quality model for strategic improvement
        revised_resume = self.llm.generate_json(prompt, max_tokens=10000, task="revision")
        return revised_resume
    
    def _build_prompt(
        self,
        current_resume: Dict[str, Any],
        jd_text: str,
        user_profile: Dict[str, Any],
        feedback: str,
        revision_type: str
    ) -> str:
        """Build revision prompt"""
        
        profile_str = json.dumps(user_profile, indent=2)
        resume_str = json.dumps(current_resume, indent=2)
        
        if revision_type == "evaluation":
            focus = "JD alignment and relevance"
            instruction = "Improve the resume to better match the job requirements"
        else:  # factuality
            focus = "factual accuracy"
            instruction = "Fix any inaccuracies or fabrications. Use ONLY real data from profile"
        
        prompt = f"""You are an expert resume writer. Revise this resume to improve {focus}.

JOB DESCRIPTION:
{jd_text}

USER PROFILE (SOURCE OF TRUTH):
{profile_str}

CURRENT RESUME:
{resume_str}

FEEDBACK TO ADDRESS:
{feedback}

TASK: {instruction}

CRITICAL REQUIREMENTS:
1. Summary: 520-570 characters with **bold** markers
2. Skills: Exactly 7 categories, 70-95 chars each
3. Experience:
   - LSEG: Exactly 5 bullets (150-200 chars, **bold**)
   - Infosys: Exactly 4 bullets (150-200 chars, **bold**)
4. Projects: Exactly 3 projects, 2 bullets each (max 200 chars, **bold**)
5. Use ONLY real metrics and technologies from user profile
6. DO NOT fabricate or exaggerate

Return ONLY the complete revised resume JSON in the same format:
{{
  "header": {{"title": "..."}},
  "summary": "...",
  "skills": [...],
  "experience": [...],
  "projects": [...]
}}"""
        
        return prompt

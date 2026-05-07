"""
Factuality Checker - Verifies resume claims against user profile
"""
import json
from typing import Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aro.llm_adapter import LLMAdapter


class FactualityChecker:
    def __init__(self, llm: LLMAdapter, debug: bool = False):
        self.llm = llm
        self.debug = debug
    
    def check(
        self, 
        resume_json: Dict[str, Any], 
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if resume claims are factual based on user profile
        
        Args:
            resume_json: Generated resume
            user_profile: Original user data
        
        Returns:
            {
                "is_factual": bool,
                "factuality_score": 0-100,
                "issues": [...],
                "summary_check": {...},
                "experience_check": {...},
                "projects_check": {...},
                "skills_check": {...}
            }
        """
        prompt = self._build_prompt(resume_json, user_profile)
        
        if self.debug:
            print("\n" + "="*60)
            print("DEBUG: FACTUALITY CHECKER PROMPT")
            print("="*60)
            print(f"Prompt length: {len(prompt)} characters (~{len(prompt)//4} tokens)")
            print("="*60 + "\n")
        
        # Needs ~10000 tokens for large profile + detailed output
        # Use standard flash model for critical verification
        result = self.llm.generate_json(prompt, max_tokens=10000, task="factuality")
        return result
    
    def _build_prompt(self, resume_json: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """Build factuality check prompt"""
        
        profile_str = json.dumps(user_profile, indent=2)
        resume_str = json.dumps(resume_json, indent=2)
        
        prompt = f"""You are a strict factuality checker. Verify if ALL resume claims are accurate against the user's actual profile.

USER'S ACTUAL PROFILE (SOURCE OF TRUTH):
{profile_str}

GENERATED RESUME (TO VERIFY):
{resume_str}

Check EVERY claim for accuracy:

1. SUMMARY
   - GPA matches profile exactly?
   - Degree and university correct?
   - Years of experience accurate?
   - Technologies actually used?
   - Metrics are real (not inflated)?

2. WORK EXPERIENCE  
   - Company names, titles, dates match?
   - Metrics match profile (7.5M records, 40%, etc.)?
   - Technologies actually used at those companies?
   - Achievements based on real work?
   - NO fabricated claims?

3. PROJECTS
   - Project names exist in profile?
   - Technologies match what was actually used?
   - Metrics accurate (1.5M params, 16.67 FPS, etc.)?
   - GitHub URLs would be correct?

4. SKILLS
   - Every listed skill is in user's profile?
   - No false expertise claims?
   - Skill categories accurate?

Be EXTREMELY CRITICAL. Flag:
- ANY metric that doesn't match profile
- ANY technology not in user's stack
- ANY project that doesn't exist
- ANY exaggeration or inflation

Return ONLY this JSON:
{{
  "is_factual": true/false,
  "factuality_score": 0-100,
  "issues": ["Issue 1", "Issue 2", ...],
  "summary_check": {{
    "is_accurate": true/false,
    "issues": ["Specific issue 1", ...]
  }},
  "experience_check": {{
    "is_accurate": true/false,
    "issues": ["Specific issue 1", ...]
  }},
  "projects_check": {{
    "is_accurate": true/false,
    "issues": ["Specific issue 1", ...]
  }},
  "skills_check": {{
    "is_accurate": true/false,
    "issues": ["Specific issue 1", ...]
  }}
}}

If everything is accurate, return empty arrays for issues."""
        
        return prompt

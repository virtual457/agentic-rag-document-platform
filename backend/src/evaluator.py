"""
Evaluator - Scores resume against JD with detailed feedback
"""
import re
import json
from typing import Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aro.llm_adapter import LLMAdapter


class Evaluator:
    def __init__(self, llm: LLMAdapter, debug: bool = False):
        self.llm = llm
        self.debug = debug
    
    def evaluate(
        self, 
        resume_json: Dict[str, Any], 
        jd_text: str
    ) -> Dict[str, Any]:
        """
        Evaluate resume against JD
        
        Args:
            resume_json: Generated resume JSON
            jd_text: Job description
        
        Returns:
            {
                "total_score": 0-100,
                "keyword_score": 0-35,
                "llm_score": 0-65,
                "section_scores": {...},
                "feedback": "...",
                "section_feedback": {...}
            }
        """
        # Keyword matching (35 points)
        keyword_score = self._calculate_keyword_match(resume_json, jd_text)
        
        # LLM evaluation (65 points) with section breakdown
        llm_result = self._llm_evaluate(resume_json, jd_text)
        
        return {
            "total_score": keyword_score + llm_result['score'],
            "keyword_score": keyword_score,
            "llm_score": llm_result['score'],
            "section_scores": llm_result['section_scores'],
            "feedback": llm_result['feedback'],
            "section_feedback": llm_result['section_feedback']
        }
    
    def _calculate_keyword_match(self, resume_json: Dict[str, Any], jd_text: str) -> float:
        """Calculate keyword match score (0-35)"""
        jd_keywords = set()
        patterns = [
            r'\b(Python|Java|JavaScript|TypeScript|Go|C\+\+|C#|SQL|Ruby|Rust)\b',
            r'\b(React|Next\.js|Django|Flask|FastAPI|Spring|Node\.js|Express)\b',
            r'\b(AWS|Azure|GCP|Kubernetes|Docker|Lambda|EC2|S3|SQS)\b',
            r'\b(MySQL|PostgreSQL|MongoDB|Redis|DynamoDB)\b',
            r'\b(Machine Learning|Deep Learning|PyTorch|TensorFlow|AI)\b',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, jd_text, re.IGNORECASE)
            jd_keywords.update([m.lower() for m in matches])
        
        resume_text = json.dumps(resume_json).lower()
        resume_keywords = set()
        for keyword in jd_keywords:
            if keyword.lower() in resume_text:
                resume_keywords.add(keyword)
        
        if not jd_keywords:
            return 35.0
        
        match_ratio = len(resume_keywords) / len(jd_keywords)
        score = match_ratio * 35
        
        return round(score, 2)
    
    def _llm_evaluate(self, resume_json: Dict[str, Any], jd_text: str) -> Dict[str, Any]:
        """LLM-based evaluation (0-65 points) with detailed section feedback"""
        
        prompt = f"""You are an expert resume evaluator. Score this resume against the job description.

JOB DESCRIPTION:
{jd_text}

RESUME:
{json.dumps(resume_json, indent=2)}

Evaluate critically on these criteria:

1. EXPERIENCE RELEVANCE (25 points)
   - Do work bullets highlight JD-relevant achievements?
   - Are metrics compelling and specific?
   - Is the language tailored to this role?

2. SKILLS ALIGNMENT (20 points)
   - Are all key JD technologies present?
   - Are skills organized by importance to role?
   - Any critical missing skills?

3. PROJECTS RELEVANCE (15 points)
   - Do projects demonstrate required skills?
   - Are the right projects selected?
   - Do project bullets show depth?

4. PRESENTATION QUALITY (5 points)
   - Is summary compelling and concise?
   - Are bold markers used effectively?
   - Professional writing quality?

Be CRITICAL and SPECIFIC in feedback. Point out what's missing, what could be stronger, and what's done well.

Return ONLY this JSON:
{{
  "score": 0-65,
  "section_scores": {{
    "experience": 0-25,
    "skills": 0-20,
    "projects": 0-15,
    "presentation": 0-5
  }},
  "feedback": "Overall assessment (2-3 sentences)",
  "section_feedback": {{
    "experience": "What's good and what needs improvement",
    "skills": "What's good and what needs improvement",
    "projects": "What's good and what needs improvement",
    "presentation": "What's good and what needs improvement"
  }}
}}"""
        
        if self.debug:
            print("\n" + "="*60)
            print("DEBUG: EVALUATOR PROMPT")
            print("="*60)
            print(f"Prompt length: {len(prompt)} characters (~{len(prompt)//4} tokens)")
            print("="*60 + "\n")
        
        # Increased to 6000 for detailed feedback
        # Use fast model (flash-lite) for scoring - 10 RPM vs 5 RPM!
        result = self.llm.generate_json(prompt, max_tokens=6000, task="evaluation")
        return result

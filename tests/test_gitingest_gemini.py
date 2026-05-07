# test_gitingest_gemini.py
"""
Test: Use GitIngest to get repo content, then analyze with Gemini
"""

import requests
from google import genai
import os

def test_gitingest_with_gemini():
    """
    Test GitIngest → Gemini pipeline
    """
    
    print("=" * 70)
    print("TEST: GitIngest + Gemini Analysis")
    print("=" * 70)
    
    # ===== STEP 1: Fetch repo via GitIngest =====
    print("\n[1] Fetching repository via GitIngest...")
    
    username = "virtual457"
    repo_name = "llm-multi-agent-resume-optimizer"
    gitingest_url = f"https://gitingest.com/{username}/{repo_name}"
    
    print(f"   URL: {gitingest_url}")
    print(f"   Fetching... (this may take 10-30 seconds)")
    
    try:
        response = requests.get(gitingest_url, timeout=60)
        
        if response.status_code == 200:
            repo_content = response.text
            print(f"\n✅ Success! Got repository content")
            print(f"   Total size: {len(repo_content):,} characters")
            print(f"   Estimated tokens: ~{len(repo_content.split()):,}")
            
            # Show preview
            print(f"\n   Preview (first 500 chars):")
            print(f"   {repo_content[:500]}...")
            
        else:
            print(f"\n❌ GitIngest failed: HTTP {response.status_code}")
            print(f"   Message: {response.text[:200]}")
            return
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out (repo might be too large)")
        return
    except Exception as e:
        print(f"\n❌ Error fetching from GitIngest: {e}")
        return
    
    # ===== STEP 2: Smart filtering (reduce size) =====
    print("\n[2] Filtering content for Gemini...")
    
    # Only send first 100,000 characters to save costs
    # (Full repo is too expensive!)
    max_chars = 100000
    
    if len(repo_content) > max_chars:
        filtered_content = repo_content[:max_chars]
        print(f"   ⚠️  Repo is large, using first {max_chars:,} chars only")
    else:
        filtered_content = repo_content
        print(f"   ✅ Using full content ({len(repo_content):,} chars)")
    
    estimated_tokens = len(filtered_content.split())
    estimated_cost = estimated_tokens * 0.0001
    
    print(f"   Estimated tokens to send: ~{estimated_tokens:,}")
    print(f"   Estimated cost: ~${estimated_cost:.2f}")
    
    # ===== STEP 3: Send to Gemini =====
    print("\n[3] Sending to Gemini for analysis...")
    
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBambOdpGWOFXunpdpD9TBIlxWpLQwVZVw')
    
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
Analyze this complete GitHub repository and create a professional summary 
suitable for a resume or portfolio.

CRITICAL: This is the ACTUAL repository content from GitIngest.
DO NOT hallucinate. Use ONLY information present in the content below.

REPOSITORY CONTENT:
{filtered_content}

Based on the ACTUAL code and files above, provide:

1. PROJECT DESCRIPTION (2-3 sentences)
   - What does this project do?
   - What problem does it solve?

2. KEY FEATURES (5 bullet points)
   - List the main capabilities
   - Focus on impressive/unique features

3. TECHNOLOGIES USED
   - Programming languages
   - Frameworks/libraries
   - Tools and platforms

4. ARCHITECTURE
   - How is the project structured?
   - What patterns are used?

5. NOTABLE IMPLEMENTATIONS
   - Any impressive algorithms/optimizations?
   - Performance improvements?
   - Scale/metrics?

Keep it concise, professional, and suitable for a technical resume.
"""
        
        print("   Waiting for Gemini response... (30-60 seconds)")
        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'max_output_tokens': 2000}
        )
        
        print("\n✅ Got Gemini analysis!")
        
        print("\n" + "=" * 70)
        print("GEMINI'S ANALYSIS OF LMARO (based on actual code):")
        print("=" * 70)
        print(response.text)
        print("=" * 70)
        
        # ===== STEP 4: Verification =====
        print("\n[4] Verification check...")
        
        response_lower = response.text.lower()
        
        # Check if Gemini mentioned actual LMARO components
        lmaro_terms = ['generator', 'evaluator', 'factuality', 'reviser', 'renderer', 
                       'fastapi', 'gemini', 'next.js', 'sse', 'streaming']
        
        found_terms = [term for term in lmaro_terms if term in response_lower]
        
        print(f"\n   Found {len(found_terms)}/{len(lmaro_terms)} LMARO-specific terms:")
        print(f"   {', '.join(found_terms)}")
        
        if len(found_terms) >= 5:
            print("\n   ✅ HIGH CONFIDENCE: Gemini analyzed actual code")
            print("      Response contains many specific LMARO components")
        elif len(found_terms) >= 2:
            print("\n   ⚠️  MEDIUM CONFIDENCE: Some specific terms found")
            print("      Could be from actual analysis or educated guess")
        else:
            print("\n   ❌ LOW CONFIDENCE: Very few specific terms")
            print("      Response seems generic")
        
    except Exception as e:
        print(f"\n❌ Gemini analysis failed: {e}")
        return
    
    # ===== CONCLUSION =====
    print("\n" + "=" * 70)
    print("TEST COMPLETE - GitIngest + Gemini Pipeline Works!")
    print("=" * 70)
    print("\n✅ We can use GitIngest to:")
    print("   1. Fetch entire repo content (no GitHub API needed!)")
    print("   2. Send to Gemini for intelligent analysis")
    print("   3. Generate professional project summaries")
    print("\n⚠️  Cost consideration:")
    print(f"   - This test cost: ~${estimated_cost:.2f}")
    print(f"   - For 25 repos: ~${estimated_cost * 25:.2f}")
    print("\n💡 Recommendation:")
    print("   Use GitIngest + smart filtering (first 100K chars only)")
    print("   This gives us the best parts without excessive costs")
    print("=" * 70)


if __name__ == "__main__":
    test_gitingest_with_gemini()

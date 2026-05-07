# test_gemini_github_url.py
"""
Test: Can Gemini directly access GitHub URLs?
Strict test - verify if Gemini can actually read the repo
"""

from google import genai
import os

def test_gemini_with_github_url():
    """
    Test if Gemini can access GitHub repos via URL alone
    """
    
    print("=" * 70)
    print("TEST: Can Gemini Access GitHub URLs Directly?")
    print("=" * 70)
    
    # ===== STEP 1: Setup Gemini =====
    print("\n[1] Setting up Gemini client...")
    
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBambOdpGWOFXunpdpD9TBIlxWpLQwVZVw')
    
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini: {e}")
        return
    
    # ===== STEP 2: Test with GitHub repo URL - STRICT PROMPT =====
    print("\n[2] Testing with GitHub repository URL...")
    
    github_url = "https://github.com/virtual457/llm-multi-agent-resume-optimizer"
    
    print(f"   Sending URL: {github_url}")
    
    prompt = f"""
CRITICAL INSTRUCTIONS - READ CAREFULLY:

1. I am giving you this GitHub repository URL: {github_url}

2. Your task: ACCESS and READ this repository, then provide EXACT details.

3. DO NOT HALLUCINATE. DO NOT GUESS. DO NOT MAKE UP INFORMATION.

4. If you CANNOT access this repository, say EXACTLY: "I cannot access this repository"

5. If you CAN access it, provide ONLY VERIFIED information:
   - Project name (exact)
   - Main programming languages used (verify from actual files)
   - Number of files in the root directory
   - List the top-level folders/directories
   - Technologies mentioned in README (exact quotes)
   - At least 3 specific file names you can see

6. VERIFICATION: To prove you actually accessed it, tell me:
   - What is the EXACT first line of the README.md file?
   - How many stars does this repo have?
   - When was the last commit? (exact date)

DO NOT respond with generic information about resume optimizers.
DO NOT guess based on the repository name.
ONLY provide information you can VERIFY by accessing the actual repository.

Can you access this repository? If yes, provide the verified details above.
"""
    
    print("\n   Sending STRICT verification prompt...")
    
    # ===== STEP 3: Send to Gemini =====
    print("\n[3] Waiting for Gemini's response...")
    
    try:
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'max_output_tokens': 2000}
        )
        
        print("\n✅ Got response from Gemini!")
        print("\n" + "=" * 70)
        print("GEMINI'S RESPONSE:")
        print("=" * 70)
        print(response.text)
        print("=" * 70)
        
        # ===== STEP 4: Analyze the response =====
        print("\n[4] Analyzing response for verification...")
        
        response_lower = response.text.lower()
        response_text = response.text
        
        # Strict checks
        can_access = False
        provides_specifics = False
        
        if "cannot access" in response_lower or "can't access" in response_lower:
            print("\n❌ CLEAR ANSWER: Gemini explicitly says it CANNOT access")
            can_access = False
            
        elif "don't have access" in response_lower or "unable to access" in response_lower:
            print("\n❌ CLEAR ANSWER: Gemini says it doesn't have access")
            can_access = False
            
        elif "i am unable" in response_lower or "i do not have the ability" in response_lower:
            print("\n❌ CLEAR ANSWER: Gemini cannot access external URLs")
            can_access = False
            
        else:
            # Check if it provides specific details
            has_specific_files = any(x in response_text for x in ['.py', '.js', '.md', '.txt', '.json'])
            has_exact_quote = '```' in response_text or '"' in response_text
            has_numbers = any(char.isdigit() for char in response_text)
            
            if has_specific_files or has_exact_quote or has_numbers:
                print("\n⚠️  UNCLEAR: Gemini provided some specific details")
                print("   This could mean:")
                print("   - It CAN access and read the repo ✅")
                print("   - OR it's hallucinating based on the repo name ❌")
                provides_specifics = True
            else:
                print("\n❌ Gemini gave vague/generic response")
        
        # Final determination
        print("\n" + "=" * 70)
        print("FINAL DETERMINATION:")
        print("=" * 70)
        
        if not can_access and not provides_specifics:
            print("❌ Gemini CANNOT access GitHub URLs directly")
            print("   We need to use GitHub API to fetch content ourselves")
            
        elif provides_specifics:
            print("⚠️  NEEDS MANUAL VERIFICATION")
            print("   Read the response above and check:")
            print("   1. Did it quote the exact first line of README?")
            print("   2. Did it list actual file names you can verify?")
            print("   3. Did it provide repo stats (stars, last commit)?")
            print("   ")
            print("   If YES → Gemini can access GitHub! ✅")
            print("   If NO → Gemini is hallucinating ❌")
        
    except Exception as e:
        print(f"\n❌ Request failed: {e}")
        return
    
    # ===== CONCLUSION =====
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nWhat we learned:")
    print("  1. Can Gemini access GitHub URLs? (See determination above)")
    print("  2. Do we need GitHub API? (If Gemini can't access, then YES)")
    print("=" * 70)


if __name__ == "__main__":
    test_gemini_with_github_url()

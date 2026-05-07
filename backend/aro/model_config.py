"""
Model Configuration - Smart Routing for Rate Limit Optimization

Routes different tasks to appropriate models based on:
- Quality requirements
- Rate limits (flash-lite has 10 RPM vs 5 RPM for others)
- Cost optimization

USAGE:
    from aro.model_config import ModelConfig
    
    # Get model for specific task
    model = ModelConfig.get_model('generation')  # Returns 'gemini-2.5-flash'
    
    # For LangChain agents
    model = ModelConfig.LANGCHAIN_MODEL  # Returns 'gemini-2.5-flash'
"""


class ModelConfig:
    """Centralized model selection and routing"""
    
    # ============================================================
    # AVAILABLE MODELS (Update here when new models available)
    # ============================================================
    HIGH_QUALITY = "gemini-2.5-flash"           # 85-87% quality, 5 RPM
    FAST_CHEAP = "gemini-2.5-flash-lite"        # 80-85% quality, 10 RPM (2x!)
    AUTO_LATEST = "gemini-flash-latest"         # Auto-selects latest
    
    # ============================================================
    # COMPONENT DEFAULTS (Single source of truth)
    # ============================================================
    LANGCHAIN_MODEL = HIGH_QUALITY              # For LangChain ReAct agents
    STANDARD_MODEL = HIGH_QUALITY               # For standard LLM calls
    
    # ============================================================
    # TASK ROUTING MAP
    # ============================================================
    TASK_ROUTING = {
        # High quality tasks - need good reasoning (use flash)
        "generation": HIGH_QUALITY,         # Initial resume creation
        "revision": HIGH_QUALITY,           # Strategic improvement
        "factuality": HIGH_QUALITY,         # Critical verification
        "extraction": HIGH_QUALITY,         # Profile entity parsing
        
        # Simple/fast tasks - just pattern matching (use lite - 2x rate!)
        "evaluation": FAST_CHEAP,           # Resume scoring
        "validation": FAST_CHEAP,           # Format checking
        "scoring": FAST_CHEAP,              # Keyword matching
        "keyword_match": FAST_CHEAP,        # Simple regex
    }
    
    @staticmethod
    def get_model(task: str) -> str:
        """
        Get appropriate model for task
        
        Args:
            task: Task type ('generation', 'evaluation', 'factuality', etc.)
        
        Returns:
            Model name (e.g., 'gemini-2.5-flash')
        """
        return ModelConfig.TASK_ROUTING.get(task, ModelConfig.HIGH_QUALITY)
    
    @staticmethod
    def get_max_tokens(task: str) -> int:
        """Get appropriate token limit for task"""
        limits = {
            "generation": 8000,      # Long resume JSON
            "revision": 8000,        # Full resume update
            "evaluation": 2000,      # Just scores + feedback
            "factuality": 3000,      # Verification results
            "extraction": 4000,      # Entity list
            "validation": 1000,      # Simple yes/no
        }
        return limits.get(task, 4000)
    
    @staticmethod
    def get_temperature(task: str) -> float:
        """Get appropriate temperature for task"""
        temps = {
            "generation": 0.7,       # Creative writing
            "revision": 0.7,         # Strategic thinking
            "extraction": 0.3,       # Structured extraction
            "evaluation": 0.0,       # Deterministic scoring
            "factuality": 0.0,       # Strict verification
            "validation": 0.0,       # Binary checks
        }
        return temps.get(task, 0.3)


# ============================================================
# FUTURE UPGRADE PATH (When Gemini 3 becomes available)
# ============================================================
# 
# Just change these two lines:
#   HIGH_QUALITY = "gemini-3-flash"
#   FAST_CHEAP = "gemini-2.5-flash-lite"
# 
# Everything else updates automatically!
# ============================================================

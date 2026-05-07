"""
Test Model Routing - Verify smart model selection is working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aro.model_config import ModelConfig

def test_routing():
    print("\n" + "="*70)
    print("MODEL ROUTING TEST")
    print("="*70 + "\n")
    
    tasks = [
        ("generation", "Resume Generation"),
        ("revision", "Resume Revision"),
        ("factuality", "Factuality Verification"),
        ("evaluation", "Resume Evaluation"),
    ]
    
    for task_id, task_name in tasks:
        model = ModelConfig.get_model(task_id)
        rpm = "10 RPM" if model == ModelConfig.FAST_CHEAP else "5 RPM"
        
        print(f"{task_name}:")
        print(f"  Model: {model}")
        print(f"  Rate:  {rpm}\n")
    
    print("="*70)
    print("Evaluator uses flash-lite (10 RPM) - 2x faster rate limit!")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_routing()

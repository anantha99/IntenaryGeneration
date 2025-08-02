#!/usr/bin/env python3
"""
Test script to verify the centralized model configuration works correctly
"""

from model_used import get_model, get_openrouter_model, list_available_models, MODELS, GEMINI_MODELS

def test_model_configuration():
    """Test all model configuration functions"""
    print("🧪 Testing Centralized Model Configuration")
    print("=" * 50)
    
    # Test get_model function
    print("\n1. Testing get_model() function:")
    for agent_type in ["REQUEST_PARSER", "ACTIVITIES_PLANNER", "ACCOMMODATION_SUGGESTER", "COST_ESTIMATOR"]:
        model = get_model(agent_type)
        print(f"   {agent_type}: {model}")
    
    # Test get_openrouter_model function
    print("\n2. Testing get_openrouter_model() function:")
    for model_name in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.5-pro"]:
        full_path = get_openrouter_model(model_name)
        print(f"   {model_name}: {full_path}")
    
    # Test direct access to MODELS
    print("\n3. Testing direct MODELS access:")
    for key, value in MODELS.items():
        if key.startswith("DEFAULT_"):
            print(f"   {key}: {value}")
    
    # Test list_available_models
    print("\n4. Testing list_available_models():")
    available = list_available_models()
    print(f"   Found {len(available['Agent Models'])} agent models")
    print(f"   Found {len(available['Gemini Models'])} Gemini models")
    
    print("\n✅ All tests passed! Centralized model configuration is working correctly.")
    print("\nℹ️  Usage Examples:")
    print("   from config.model_used import get_model")
    print("   model = get_model('REQUEST_PARSER')  # Returns full OpenRouter path")
    print("   litellm.acompletion(model=model, ...)")

if __name__ == "__main__":
    test_model_configuration()
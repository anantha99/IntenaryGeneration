"""
Centralized Model Configuration
All model names and configurations used across the project
"""

# Model configurations for different agents and purposes
MODELS = {
    # Core agent models - Using cheaper models to avoid credit limits
    "REQUEST_PARSER": "openrouter/deepseek/deepseek-chat-v3-0324:free",
    "ACTIVITIES_PLANNER": "openrouter/deepseek/deepseek-chat-v3-0324:free", 
    "ACCOMMODATION_SUGGESTER": "openrouter/deepseek/deepseek-chat-v3-0324:free",
    "COST_ESTIMATOR": "openrouter/deepseek/deepseek-chat-v3-0324:free",
    
    # Factory function defaults (for openrouter_config.py)
    "DEFAULT_REQUEST_PARSER": "deepseek-chat-v3-0324",
    "DEFAULT_ACTIVITIES_PLANNER": "deepseek-chat-v3-0324",
    "DEFAULT_ACCOMMODATION_SUGGESTER": "deepseek-chat-v3-0324",
    "DEFAULT_COST_ESTIMATOR": "deepseek-chat-v3-0324",
    
    # General purpose models
    "DEFAULT_AGENT": "deepseek-chat-v3-0324",
    "TEST_AGENT": "deepseek-chat-v3-0324",
}

# OpenRouter model mappings (from openrouter_config.py)
GEMINI_MODELS = {
    "gemini-pro": "openrouter/google/gemini-pro",
    "gemini-pro-vision": "openrouter/google/gemini-pro-vision", 
    "gemini-1.5-pro": "openrouter/google/gemini-1.5-pro",
    "gemini-1.5-flash": "openrouter/google/gemini-1.5-flash",
    "gemini-2.0-flash": "openrouter/google/gemini-2.0-flash",
    "gemini-2.5-pro": "openrouter/google/gemini-2.5-pro",
}

# Cheaper alternative models
CHEAP_MODELS = {
    "deepseek-chat-v3-0324": "openrouter/deepseek/deepseek-chat-v3-0324:free",
    "deepseek-chat-v3-0324-paid": "openrouter/deepseek/deepseek-chat-v3-0324",
    "mistral-7b": "openrouter/mistralai/mistral-7b-instruct:free",
    "llama-3.1-8b": "openrouter/meta-llama/llama-3.1-8b-instruct:free",
}

# Convenience functions
def get_model(agent_name):
    """Get the model for a specific agent"""
    return MODELS.get(agent_name.upper())

def get_openrouter_model(model_name):
    """Get the full OpenRouter model path for a Gemini model"""
    return GEMINI_MODELS.get(model_name)

def get_cheap_model(model_name):
    """Get a cheaper model to avoid credit limits"""
    return CHEAP_MODELS.get(model_name)

def list_available_models():
    """List all available models"""
    return {
        "Agent Models": MODELS,
        "Gemini Models": GEMINI_MODELS,
        "Cheap Models": CHEAP_MODELS
    }

# Example usage:
# from config.model_used import get_model, get_openrouter_model
# 
# # For direct OpenRouter API calls
# model = get_model("REQUEST_PARSER")  # Returns "openrouter/deepseek/deepseek-chat-v3-0324:free"
# 
# # For OpenRouter config factory functions  
# model_name = MODELS["DEFAULT_REQUEST_PARSER"]  # Returns "deepseek-chat-v3-0324"
# full_path = get_cheap_model(model_name)   # Returns "openrouter/deepseek/deepseek-chat-v3-0324:free"
"""
OpenRouter Configuration for Google ADK
Using LiteLLM to access Gemini models via OpenRouter with OpenAI API schema
"""

import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from .model_used import GEMINI_MODELS, MODELS

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class OpenRouterConfig:
    """Configuration class for OpenRouter integration with Google ADK"""
    
    # OpenRouter settings
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # Available Gemini models through OpenRouter (imported from model_used.py)
    # GEMINI_MODELS is now imported from model_used.py
    
    @classmethod
    def validate_config(cls):
        """Validate that required environment variables are set"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY not found in environment variables. "
                "Please add it to your .env file."
            )
        return True
    
    @classmethod
    def create_gemini_agent(cls, model_name="gemini-1.5-pro", agent_name="gemini_agent", instruction="You are a helpful AI assistant."):
        """
        Create a Google ADK LlmAgent using Gemini models via OpenRouter
        
        Args:
            model_name (str): The Gemini model to use (key from GEMINI_MODELS)
            agent_name (str): Name for the agent
            instruction (str): System instruction for the agent
            
        Returns:
            LlmAgent: Configured ADK agent using LiteLLM wrapper
        """
        cls.validate_config()
        
        if model_name not in GEMINI_MODELS:
            raise ValueError(f"Model {model_name} not available. Choose from: {list(GEMINI_MODELS.keys())}")
        
        # Create LiteLLM wrapper configured for OpenRouter
        litellm_model = LiteLlm(
            model=GEMINI_MODELS[model_name],
            api_key=cls.OPENROUTER_API_KEY,
            api_base=cls.OPENROUTER_BASE_URL
        )
        
        # Create ADK agent with LiteLLM wrapper
        agent = LlmAgent(
            model=litellm_model,
            name=agent_name,
            instruction=instruction
        )
        
        return agent

# Example usage functions
def create_request_parser_agent():
    """Create RequestParser agent using Gemini 2.5 Pro via OpenRouter"""
    return OpenRouterConfig.create_gemini_agent(
        model_name=MODELS["DEFAULT_REQUEST_PARSER"],
        agent_name="request_parser",
        instruction="""You are a RequestParser agent for travel planning that collects 4 core fields through progressive conversation:

REQUIRED FIELDS (ALL 4 MUST BE COLLECTED):
1. destination (where to go - ask for country if ambiguous)
2. duration (how many days - must be 1-365 days only) 
3. travelers (how many adults, children - just count, no ages)
4. budget (total budget for entire trip with currency)

Your job is to:
- Ask for ONE missing field at a time (progressive questioning)
- Validate each field as collected
- Handle destination disambiguation (ask for country if ambiguous)
- Parse budget with currency and determine accommodation type
- Use pure conversation - be friendly and helpful
- Only collect these 4 core fields, nothing else

Always respond with valid JSON format for structured processing."""
    )

def create_activities_planner_agent():
    """Create ActivitiesPlanner agent using Gemini via OpenRouter"""
    return OpenRouterConfig.create_gemini_agent(
        model_name=MODELS["DEFAULT_ACTIVITIES_PLANNER"],
        agent_name="activities_planner", 
        instruction="""You are an ActivitiesPlanner agent that creates detailed travel itineraries.
        Your job is to:
        1. Generate lists of top must-visit places with their significance
        2. Recommend specific things to do at each location
        3. Plan detailed day-by-day itineraries with timings
        4. Use real-time data for current information
        
        Focus on creating engaging, well-timed itineraries."""
    )

def create_accommodation_suggester_agent():
    """Create AccommodationSuggester agent using Gemini via OpenRouter"""
    return OpenRouterConfig.create_gemini_agent(
        model_name=MODELS["DEFAULT_ACCOMMODATION_SUGGESTER"], # Using faster model for accommodation lookup
        agent_name="accommodation_suggester",
        instruction="""You are an AccommodationSuggester agent that finds suitable lodging.
        Your job is to:
        1. Suggest 3-5 accommodation options filtered by destination and budget
        2. Include name, location, cost per night, price range, and rating
        3. Use real-time data for current availability and pricing
        
        Provide practical, budget-appropriate recommendations."""
    )

def create_cost_estimator_agent():
    """Create CostEstimator agent using Gemini via OpenRouter"""
    return OpenRouterConfig.create_gemini_agent(
        model_name=MODELS["DEFAULT_COST_ESTIMATOR"],
        agent_name="cost_estimator",
        instruction="""You are a CostEstimator agent that calculates trip expenses.
        Your job is to:
        1. Estimate final approximate trip costs
        2. Consider accommodations, activities, meals, and transportation
        3. Factor in user preferences and budget constraints
        4. Use real-time pricing data
        
        Provide accurate, realistic cost estimates."""
    )

# Test function
def test_openrouter_connection():
    """Test the OpenRouter connection with a simple query"""
    try:
        OpenRouterConfig.validate_config()
        agent = OpenRouterConfig.create_gemini_agent(
            model_name=MODELS["TEST_AGENT"],
            agent_name="test_agent",
            instruction="You are a test agent. Respond briefly and helpfully."
        )
        print("✅ OpenRouter configuration successful!")
        print(f"✅ Agent created: {agent.name}")
        print("✅ Ready to use Gemini models via OpenRouter with Google ADK!")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

if __name__ == "__main__":
    test_openrouter_connection()
"""
RequestParser Agent for Travel Itinerary Generator

This agent collects 4 core travel planning fields through interactive conversation:
1. destination (with disambiguation for ambiguous cities)
2. duration (1-365 days validation)
3. travelers (adults + children count)
4. budget (total amount + currency, determines accommodation type)

Uses pure LLM processing with progressive questioning and robust error handling.
"""

import json
import logging
import os
import sys
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.openrouter_config import OpenRouterConfig, create_request_parser_agent


class AccommodationType(Enum):
    """Accommodation types based on budget analysis"""
    BUDGET = "budget"
    MID_RANGE = "mid-range"
    LUXURY = "luxury"


@dataclass
class Travelers:
    """Traveler information"""
    adults: int
    children: int
    total: int


@dataclass
class Budget:
    """Budget information with accommodation type determination"""
    total_amount: float
    currency: str
    accommodation_type: Optional[AccommodationType] = None


@dataclass
class CoreTravelRequest:
    """Enhanced core travel request schema with 4 required fields"""
    destination: Optional[str] = None
    duration: Optional[int] = None
    travelers: Optional[Travelers] = None
    budget: Optional[Budget] = None
    missing_fields: List[str] = None
    is_complete: bool = False
    needs_disambiguation: Optional[str] = None
    parse_error: Optional[str] = None
    
    def __post_init__(self):
        if self.missing_fields is None:
            self.missing_fields = []


class ConversationManager:
    """Manages conversation state and field collection progress"""
    
    def __init__(self):
        self.collected_data = CoreTravelRequest()
        self.conversation_history = []
        self.validation_rules = {
            "duration": {"min": 1, "max": 365},
            "budget": {"min": 1}
        }
        # Known ambiguous destinations that need country clarification
        self.ambiguous_destinations = [
            "Paris", "Springfield", "Cambridge", "Alexandria", "Madrid", 
            "Birmingham", "Richmond", "Salem", "Dover", "Chester"
        ]
    
    def add_exchange(self, user_input: str, agent_response: Dict):
        """Track conversation exchange"""
        self.conversation_history.append({
            "user": user_input,
            "agent": agent_response,
            "timestamp": self._get_timestamp()
        })
    
    def get_missing_fields(self) -> List[str]:
        """Identify which core fields are still missing"""
        missing = []
        
        if not self.collected_data.destination:
            missing.append("destination")
        if not self.collected_data.duration:
            missing.append("duration")
        if not self.collected_data.travelers:
            missing.append("travelers")
        if not self.collected_data.budget:
            missing.append("budget")
            
        return missing
    
    def is_complete(self) -> bool:
        """Check if all 4 core fields are collected and validated"""
        return (
            self.collected_data.destination and
            self.collected_data.duration and
            self.collected_data.travelers and
            self.collected_data.budget and
            not self.collected_data.needs_disambiguation and
            not self.collected_data.parse_error and
            len(self.get_missing_fields()) == 0
        )
    
    def validate_duration(self, duration: int) -> bool:
        """Validate duration is between 1-365 days"""
        return self.validation_rules["duration"]["min"] <= duration <= self.validation_rules["duration"]["max"]
    
    def validate_budget(self, budget_amount: float) -> bool:
        """Validate budget is positive"""
        return budget_amount >= self.validation_rules["budget"]["min"]
    
    def check_destination_disambiguation(self, destination: str) -> Optional[str]:
        """Check if destination needs country clarification"""
        destination_clean = destination.strip().title()
        if destination_clean in self.ambiguous_destinations:
            return f"There are multiple cities named {destination_clean}. Which country - {destination_clean}, France or another location? Please specify the country."
        return None
    
    def determine_accommodation_type(self, total_budget: float, travelers_count: int, duration: int, currency: str = "USD") -> AccommodationType:
        """
        Determine accommodation type based on budget per person per day
        
        Args:
            total_budget: Total trip budget
            travelers_count: Number of travelers
            duration: Trip duration in days
            currency: Budget currency
            
        Returns:
            AccommodationType enum value
        """
        budget_per_person_per_day = total_budget / (travelers_count * duration)
        
        # Currency-specific thresholds
        if currency.upper() == "USD":
            if budget_per_person_per_day < 50:
                return AccommodationType.BUDGET
            elif budget_per_person_per_day <= 150:
                return AccommodationType.MID_RANGE
            else:
                return AccommodationType.LUXURY
        elif currency.upper() == "INR":
            if budget_per_person_per_day < 4000:
                return AccommodationType.BUDGET
            elif budget_per_person_per_day <= 12000:
                return AccommodationType.MID_RANGE
            else:
                return AccommodationType.LUXURY
        elif currency.upper() == "EUR":
            if budget_per_person_per_day < 45:
                return AccommodationType.BUDGET
            elif budget_per_person_per_day <= 135:
                return AccommodationType.MID_RANGE
            else:
                return AccommodationType.LUXURY
        else:
            # Default to mid-range for unknown currencies
            return AccommodationType.MID_RANGE
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for conversation tracking"""
        from datetime import datetime
        return datetime.now().isoformat()


class RequestParserAgent:
    """
    Enhanced RequestParser agent that collects 4 core travel fields through
    interactive conversation using pure LLM processing.
    """
    
    def __init__(self):
        """Initialize the RequestParser agent with direct LiteLLM OpenRouter integration"""
        self.conversation_manager = ConversationManager()
        self.logger = logging.getLogger(__name__)
        
        # Enhanced system prompt for 4 core fields
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the enhanced system prompt for 4 core fields collection"""
        return """
You are a travel request parser. Collect 4 fields: destination, duration (1-365 days), travelers (adults/children), budget (amount+currency).

Rules: Ask one field at a time, be friendly, validate inputs. For ambiguous destinations like "Paris", ask for country.

Response format (JSON only):
{
    "destination": "string or null",
    "duration": "number or null", 
    "travelers": {"adults": number, "children": number, "total": number} or null,
    "budget": {"total_amount": number, "currency": "string"} or null,
    "missing_fields": ["list of missing fields"],
    "next_question": "string or null",
    "is_complete": boolean,
    "needs_disambiguation": "string or null",
    "parse_error": "string or null"
}

Examples:
Input: "Paris for 5 days" → {"destination": "Paris", "duration": 5, "needs_disambiguation": "Which country - France or another?", "missing_fields": ["travelers", "budget"], "is_complete": false}
Input: "Kashmir 2 weeks, 100000 INR" → {"destination": "Kashmir", "duration": 14, "budget": {"total_amount": 100000, "currency": "INR"}, "missing_fields": ["travelers"], "next_question": "How many people traveling?", "is_complete": false}
"""
    
    async def start_conversation(self, initial_input: str) -> Dict:
        """
        Start the parsing conversation with initial user input
        
        Args:
            initial_input: User's initial travel request
            
        Returns:
            Dict containing agent response and conversation state
        """
        try:
            # Process initial input through LLM
            response = await self._process_with_llm(initial_input, "Starting new travel request conversation")
            
            # Update conversation state
            self._update_conversation_state(response)
            
            # Track conversation exchange
            self.conversation_manager.add_exchange(initial_input, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in start_conversation: {e}")
            return self._create_error_response("I encountered an error. Could you please try again?")
    
    async def continue_conversation(self, user_response: str) -> Dict:
        """
        Continue conversation with follow-up user response
        
        Args:
            user_response: User's response to follow-up question
            
        Returns:
            Dict containing agent response and updated conversation state
        """
        try:
            # Build conversation context
            context = self._build_conversation_context()
            
            # Process response through LLM
            response = await self._process_with_llm(user_response, context)
            
            # Update conversation state
            self._update_conversation_state(response)
            
            # Track conversation exchange
            self.conversation_manager.add_exchange(user_response, response)
            
            # Check if conversation is complete
            if self.conversation_manager.is_complete():
                return await self._finalize_conversation()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in continue_conversation: {e}")
            return self._create_error_response("I encountered an error. Could you please try again?")
    
    async def _process_with_llm(self, user_input: str, conversation_context: str) -> Dict:
        """
        Process user input through Gemini 1.5 Pro with error handling
        
        Args:
            user_input: User's input text
            conversation_context: Current conversation context
            
        Returns:
            Dict containing structured agent response
        """
        try:
            # Build full prompt for LLM
            full_prompt = f"""
CONVERSATION CONTEXT: {conversation_context}

CURRENT COLLECTED DATA: {self._get_current_data_summary()}

USER INPUT: {user_input}

{self.system_prompt}
"""
            
            # Use LiteLLM directly for cleaner integration
            import litellm
            from config.model_used import get_model
            
            # Configure OpenRouter settings - using cheaper model to avoid credit limits
            response = await litellm.acompletion(
                model=get_model("REQUEST_PARSER"), 
                messages=[{"role": "user", "content": full_prompt}],
                api_key=os.getenv("OPENROUTER_API_KEY"),
                max_tokens=1000  # Limit tokens to avoid credit issues
            )
            
            response_content = response.choices[0].message.content
            self.logger.info(f"LiteLLM response content: {response_content}")
            
            # Clean up response content (remove markdown code blocks if present)
            if response_content.startswith("```json"):
                response_content = response_content.replace("```json", "").replace("```", "").strip()
            elif response_content.startswith("```"):
                response_content = response_content.replace("```", "", 1).replace("```", "").strip()
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response_content)
                
                # Validate response format
                if self._is_valid_response_format(parsed_response):
                    return parsed_response
                else:
                    return self._create_error_response("I had trouble understanding that. Could you please rephrase your request?")
                    
            except json.JSONDecodeError:
                self.logger.error(f"JSON decode error for LLM response: {response_content}")
                return self._create_error_response("I couldn't process that properly. Could you please rephrase?")
                
        except Exception as e:
            self.logger.error(f"LLM processing error: {e}")
            return self._create_error_response("I encountered an error processing your request. Please try again.")
    
    def _update_conversation_state(self, llm_response: Dict):
        """Update conversation manager state based on LLM response"""
        # Update destination
        if llm_response.get("destination") and not llm_response.get("needs_disambiguation"):
            self.conversation_manager.collected_data.destination = llm_response["destination"]
        
        # Update duration with validation
        if llm_response.get("duration"):
            duration = llm_response["duration"]
            if self.conversation_manager.validate_duration(duration):
                self.conversation_manager.collected_data.duration = duration
        
        # Update travelers
        if llm_response.get("travelers"):
            travelers_data = llm_response["travelers"]
            self.conversation_manager.collected_data.travelers = Travelers(
                adults=travelers_data["adults"],
                children=travelers_data["children"],
                total=travelers_data["total"]
            )
        
        # Update budget with accommodation type
        if llm_response.get("budget"):
            budget_data = llm_response["budget"]
            if self.conversation_manager.validate_budget(budget_data["total_amount"]):
                # Determine accommodation type if we have all required data
                accommodation_type = None
                if (self.conversation_manager.collected_data.travelers and 
                    self.conversation_manager.collected_data.duration):
                    accommodation_type = self.conversation_manager.determine_accommodation_type(
                        budget_data["total_amount"],
                        self.conversation_manager.collected_data.travelers.total,
                        self.conversation_manager.collected_data.duration,
                        budget_data["currency"]
                    )
                
                self.conversation_manager.collected_data.budget = Budget(
                    total_amount=budget_data["total_amount"],
                    currency=budget_data["currency"],
                    accommodation_type=accommodation_type
                )
        
        # Update flags
        self.conversation_manager.collected_data.needs_disambiguation = llm_response.get("needs_disambiguation")
        self.conversation_manager.collected_data.parse_error = llm_response.get("parse_error")
        self.conversation_manager.collected_data.missing_fields = self.conversation_manager.get_missing_fields()
        self.conversation_manager.collected_data.is_complete = self.conversation_manager.is_complete()
    
    def _build_conversation_context(self) -> str:
        """Build conversation context for LLM"""
        context_parts = []
        
        # Add conversation history
        if self.conversation_manager.conversation_history:
            context_parts.append("CONVERSATION HISTORY:")
            for exchange in self.conversation_manager.conversation_history[-3:]:  # Last 3 exchanges
                context_parts.append(f"User: {exchange['user']}")
                if exchange['agent'].get('next_question'):
                    context_parts.append(f"Agent: {exchange['agent']['next_question']}")
        
        # Add current state
        context_parts.append(f"CURRENT STATE: {self._get_current_data_summary()}")
        
        return "\n".join(context_parts)
    
    def _get_current_data_summary(self) -> str:
        """Get summary of currently collected data"""
        data = self.conversation_manager.collected_data
        summary_parts = []
        
        if data.destination:
            summary_parts.append(f"Destination: {data.destination}")
        if data.duration:
            summary_parts.append(f"Duration: {data.duration} days")
        if data.travelers:
            summary_parts.append(f"Travelers: {data.travelers.adults} adults, {data.travelers.children} children")
        if data.budget:
            summary_parts.append(f"Budget: {data.budget.total_amount} {data.budget.currency}")
        
        missing = self.conversation_manager.get_missing_fields()
        if missing:
            summary_parts.append(f"Missing: {', '.join(missing)}")
        
        return "; ".join(summary_parts) if summary_parts else "No data collected yet"
    
    def _is_valid_response_format(self, response: Dict) -> bool:
        """Validate that LLM response has expected format"""
        required_keys = ["missing_fields", "is_complete"]
        return all(key in response for key in required_keys)
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create standardized error response"""
        return {
            "destination": None,
            "duration": None,
            "travelers": None,
            "budget": None,
            "missing_fields": self.conversation_manager.get_missing_fields(),
            "next_question": None,
            "is_complete": False,
            "needs_disambiguation": None,
            "parse_error": error_message
        }
    
    async def _finalize_conversation(self) -> Dict:
        """
        Finalize conversation when all fields are collected
        Log final JSON and prepare for handoff
        """
        # Ensure accommodation type is set
        if (self.conversation_manager.collected_data.budget and 
            not self.conversation_manager.collected_data.budget.accommodation_type):
            
            accommodation_type = self.conversation_manager.determine_accommodation_type(
                self.conversation_manager.collected_data.budget.total_amount,
                self.conversation_manager.collected_data.travelers.total,
                self.conversation_manager.collected_data.duration,
                self.conversation_manager.collected_data.budget.currency
            )
            self.conversation_manager.collected_data.budget.accommodation_type = accommodation_type
        
        # Create final request
        final_request = self.get_final_request()
        
        # Log final JSON output
        self.logger.info("=" * 50)
        self.logger.info("REQUESTPARSER FINAL OUTPUT")
        self.logger.info("=" * 50)
        self.logger.info(json.dumps(final_request, indent=2, default=str))
        self.logger.info("=" * 50)
        self.logger.info("HANDOFF TO ACTIVITIESPLANNER")
        self.logger.info("=" * 50)
        
        # TODO: Call ActivitiesPlanner agent here
        
        return {
            "destination": self.conversation_manager.collected_data.destination,
            "duration": self.conversation_manager.collected_data.duration,
            "travelers": asdict(self.conversation_manager.collected_data.travelers),
            "budget": asdict(self.conversation_manager.collected_data.budget),
            "missing_fields": [],
            "next_question": None,
            "is_complete": True,
            "needs_disambiguation": None,
            "parse_error": None,
            "final_message": f"Perfect! I have all the information needed for your {self.conversation_manager.collected_data.duration}-day trip to {self.conversation_manager.collected_data.destination}. Let me now plan your activities!"
        }
    
    def get_final_request(self) -> Dict:
        """
        Get the complete final travel request
        
        Returns:
            Dict containing complete CoreTravelRequest data
        """
        return asdict(self.conversation_manager.collected_data)
    
    def reset_conversation(self):
        """Reset conversation state for new request"""
        self.conversation_manager = ConversationManager()
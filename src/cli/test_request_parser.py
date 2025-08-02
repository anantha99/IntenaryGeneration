"""
CLI interface for testing the RequestParser agent
Allows interactive testing of the conversation flow
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agents.request_parser import RequestParserAgent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('request_parser_test.log')
    ]
)


class RequestParserCLI:
    """CLI interface for RequestParser agent testing"""
    
    def __init__(self):
        self.agent = None
        self.logger = logging.getLogger(__name__)
    
    async def initialize_agent(self):
        """Initialize the RequestParser agent"""
        try:
            self.agent = RequestParserAgent()
            print("✅ RequestParser agent initialized successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            self.logger.error(f"Agent initialization error: {e}")
            return False
    
    async def run_interactive_session(self):
        """Run an interactive conversation session"""
        print("\n" + "="*60)
        print("🤖 REQUESTPARSER AGENT - INTERACTIVE TEST")
        print("="*60)
        print("This agent will help you plan your trip by collecting:")
        print("1. 🌍 Destination (where you want to go)")
        print("2. ⏰ Duration (how many days)")
        print("3. 👥 Travelers (adults and children)")
        print("4. 💰 Budget (total amount with currency)")
        print("\nType 'quit' to exit, 'reset' to start over")
        print("="*60)
        
        conversation_active = True
        first_input = True
        
        while conversation_active:
            try:
                # Get user input
                if first_input:
                    user_input = input("\n🚀 Tell me about your travel plans: ").strip()
                    first_input = False
                else:
                    user_input = input("\n💬 Your response: ").strip()
                
                # Handle special commands
                if user_input.lower() == 'quit':
                    print("\n👋 Thanks for testing the RequestParser agent!")
                    break
                elif user_input.lower() == 'reset':
                    self.agent.reset_conversation()
                    print("\n🔄 Conversation reset. Let's start over!")
                    first_input = True
                    continue
                elif not user_input:
                    print("⚠️ Please enter some text or 'quit' to exit.")
                    continue
                
                # Process user input
                if first_input or not hasattr(self, '_conversation_started'):
                    # First interaction
                    response = await self.agent.start_conversation(user_input)
                    self._conversation_started = True
                else:
                    # Continuing conversation
                    response = await self.agent.continue_conversation(user_input)
                
                # Display agent response
                self._display_agent_response(response)
                
                # Check if conversation is complete
                if response.get("is_complete"):
                    print("\n🎉 Trip planning information complete!")
                    print("📋 Final details collected:")
                    self._display_final_summary(response)
                    
                    # Ask if user wants to start a new conversation
                    new_conversation = input("\n🔄 Start a new trip plan? (y/n): ").strip().lower()
                    if new_conversation == 'y':
                        self.agent.reset_conversation()
                        first_input = True
                        self._conversation_started = False
                        print("\n🆕 Starting fresh conversation...")
                    else:
                        conversation_active = False
                
            except KeyboardInterrupt:
                print("\n\n👋 Conversation interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                self.logger.error(f"CLI session error: {e}")
    
    def _display_agent_response(self, response: dict):
        """Display the agent's response in a user-friendly format"""
        print("\n" + "-"*40)
        
        # Show error if present
        if response.get("parse_error"):
            print(f"❌ {response['parse_error']}")
            return
        
        # Show disambiguation request
        if response.get("needs_disambiguation"):
            print(f"🤔 {response['needs_disambiguation']}")
            return
        
        # Show next question
        if response.get("next_question"):
            print(f"🤖 {response['next_question']}")
        
        # Show final message if complete
        if response.get("final_message"):
            print(f"✅ {response['final_message']}")
        
        # Show progress
        self._show_progress(response)
    
    def _show_progress(self, response: dict):
        """Show collection progress"""
        collected = []
        
        if response.get("destination"):
            collected.append(f"🌍 {response['destination']}")
        if response.get("duration"):
            collected.append(f"⏰ {response['duration']} days")
        if response.get("travelers"):
            travelers = response["travelers"]
            collected.append(f"👥 {travelers['total']} people ({travelers['adults']} adults, {travelers['children']} children)")
        if response.get("budget"):
            budget = response["budget"]
            collected.append(f"💰 {budget['total_amount']} {budget['currency']}")
            if budget.get("accommodation_type"):
                accommodation_type = budget["accommodation_type"]
                if hasattr(accommodation_type, 'value'):
                    collected.append(f"🏨 {accommodation_type.value.title()} accommodation")
                else:
                    collected.append(f"🏨 {str(accommodation_type).title()} accommodation")
        
        if collected:
            print(f"\n📝 Collected so far: {' | '.join(collected)}")
        
        missing = response.get("missing_fields", [])
        if missing:
            print(f"⏳ Still needed: {', '.join(missing)}")
    
    def _display_final_summary(self, response: dict):
        """Display final trip summary"""
        print("\n" + "="*50)
        print("🎯 TRIP SUMMARY")
        print("="*50)
        
        if response.get("destination"):
            print(f"🌍 Destination: {response['destination']}")
        if response.get("duration"):
            print(f"⏰ Duration: {response['duration']} days")
        if response.get("travelers"):
            travelers = response["travelers"]
            print(f"👥 Travelers: {travelers['total']} people")
            print(f"   - Adults: {travelers['adults']}")
            print(f"   - Children: {travelers['children']}")
        if response.get("budget"):
            budget = response["budget"]
            print(f"💰 Budget: {budget['total_amount']} {budget['currency']}")
            if budget.get("accommodation_type"):
                accommodation_type = budget["accommodation_type"]
                if hasattr(accommodation_type, 'value'):
                    print(f"🏨 Accommodation: {accommodation_type.value.title()}")
                else:
                    print(f"🏨 Accommodation: {str(accommodation_type).title()}")
        
        print("="*50)
    
    async def run_test_scenarios(self):
        """Run predefined test scenarios"""
        test_scenarios = [
            {
                "name": "Simple Kashmir Trip",
                "inputs": [
                    "I want to visit Kashmir for a weekend",
                    "2 adults",
                    "50000 rupees"
                ]
            },
            {
                "name": "Ambiguous Destination", 
                "inputs": [
                    "Paris vacation for 5 days with $2000",
                    "Paris, France",
                    "2 adults and 1 child"
                ]
            },
            {
                "name": "Complex Input",
                "inputs": [
                    "Family trip to Kerala for one week, budget around 80000 INR for 4 people"
                ]
            }
        ]
        
        print("\n" + "="*60)
        print("🧪 RUNNING TEST SCENARIOS")
        print("="*60)
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n📋 Test {i}: {scenario['name']}")
            print("-" * 40)
            
            # Reset agent for each scenario
            self.agent.reset_conversation()
            
            # Process inputs
            for j, user_input in enumerate(scenario['inputs']):
                print(f"\nUser Input {j+1}: {user_input}")
                
                if j == 0:
                    response = await self.agent.start_conversation(user_input)
                else:
                    response = await self.agent.continue_conversation(user_input)
                
                print("Agent Response:")
                self._display_agent_response(response)
                
                if response.get("is_complete"):
                    print("✅ Scenario completed successfully!")
                    break
            
            print("\n" + "="*40)


async def main():
    """Main CLI function"""
    cli = RequestParserCLI()
    
    # Initialize agent
    if not await cli.initialize_agent():
        return
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Run test scenarios
        await cli.run_test_scenarios()
    else:
        # Run interactive session
        await cli.run_interactive_session()


if __name__ == "__main__":
    # Check for .env file
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please create a .env file with your OPENROUTER_API_KEY")
        print("Copy from env.example and add your actual API key")
        sys.exit(1)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not found in .env file!")
        print("Please add your OpenRouter API key to the .env file")
        sys.exit(1)
    
    # Run the CLI
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"CLI fatal error: {e}")
        sys.exit(1)
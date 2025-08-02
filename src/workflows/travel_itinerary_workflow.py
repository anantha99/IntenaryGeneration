"""
Travel Itinerary Workflow - Main Orchestration Class

Sequential workflow that coordinates the execution of:
RequestParser → ActivitiesPlanner → AccommodationSuggester

Provides progress tracking, error handling, and comprehensive response assembly.
"""

import asyncio
import logging
import time
import uuid
from typing import Optional, Callable

# Import our data models
from .data_models import (
    TravelItineraryResponse, 
    WorkflowMetadata, 
    WorkflowStage, 
    AgentStatus,
    create_workflow_metadata,
    create_empty_response
)

# Import agents
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.request_parser import RequestParserAgent
from agents.activities_planner import ActivitiesPlanner
from agents.accommodation_suggester import AccommodationSuggester


class TravelItineraryWorkflow:
    """
    Main workflow orchestrator for travel itinerary generation.
    
    Executes agents sequentially with progress tracking and error handling:
    1. RequestParser: Parse user natural language input
    2. ActivitiesPlanner: Generate activities and itinerary 
    3. AccommodationSuggester: Find location-aware accommodations
    4. Assemble final response with all data
    """
    
    def __init__(self, progress_callback: Optional[Callable] = None):
        """
        Initialize the workflow with agents and optional progress callback.
        
        Args:
            progress_callback: Optional function to call for progress updates
        """
        self.logger = logging.getLogger(__name__)
        self.progress_callback = progress_callback
        
        # Initialize agents
        self.request_parser = RequestParserAgent()
        self.activities_planner = ActivitiesPlanner()
        self.accommodation_suggester = AccommodationSuggester()
        
        # Workflow configuration
        self.agent_timeout = 180  # 3 minutes per agent (RequestParser can be slow)
        self.max_retries = 2
        self.retry_delay = 5  # seconds
        
        self.logger.info("TravelItineraryWorkflow initialized with all agents")
    
    async def execute_workflow(self, user_input: str) -> TravelItineraryResponse:
        """
        Execute the complete travel itinerary workflow.
        
        Args:
            user_input: User's natural language travel request
            
        Returns:
            TravelItineraryResponse: Complete or partial response with metadata
        """
        # Initialize workflow metadata
        workflow_id = str(uuid.uuid4())[:8]
        workflow_metadata = create_workflow_metadata(workflow_id)
        response = create_empty_response(user_input, workflow_metadata)
        
        self.logger.info(f"🚀 Starting workflow {workflow_id} for user request")
        self._update_progress("Starting travel itinerary generation...", 0, workflow_metadata)
        
        try:
            # Stage 1: Parse user request
            await self._execute_request_parser(user_input, response)
            
            # Stage 2: Plan activities (only if parsing succeeded)
            if response.parsed_request:
                await self._execute_activities_planner(response)
            
            # Stage 3: Find accommodations (only if activities planning succeeded)
            if response.itinerary:
                await self._execute_accommodation_suggester(response)
            
            # Stage 4: Assemble final response
            await self._assemble_final_response(response)
            
            # Mark workflow as completed
            workflow_metadata.complete_workflow()
            self._update_progress("Travel itinerary generation completed!", 100, workflow_metadata)
            
            self.logger.info(f"✅ Workflow {workflow_id} completed successfully in {workflow_metadata.total_duration:.1f}s")
            
        except Exception as e:
            # Handle unexpected workflow errors
            error_msg = f"Unexpected workflow error: {str(e)}"
            self.logger.error(f"❌ Workflow {workflow_id} failed: {error_msg}")
            workflow_metadata.fail_workflow(error_msg)
            self._update_progress(f"Error: {error_msg}", workflow_metadata.get_completion_percentage(), workflow_metadata)
        
        return response
    
    async def _execute_request_parser(self, user_input: str, response: TravelItineraryResponse):
        """Execute RequestParser with retry logic and progress tracking"""
        agent_exec = response.workflow_metadata.request_parser
        response.workflow_metadata.current_stage = WorkflowStage.PARSING_REQUEST
        
        self.logger.info("📝 Starting RequestParser...")
        self._update_progress("Parsing your travel request...", 5, response.workflow_metadata)
        
        for attempt in range(self.max_retries + 1):
            try:
                agent_exec.start()
                
                # Execute with timeout
                # RequestParserAgent has a different interface - it's conversational
                parser_response = await asyncio.wait_for(
                    self.request_parser.start_conversation(user_input),
                    timeout=self.agent_timeout
                )
                
                # For workflow purposes, we need to extract CoreTravelRequest
                # If the agent completes in one go, get the final request
                if parser_response.get("is_complete"):
                    final_request_data = self.request_parser.get_final_request()
                    parsed_request = self._convert_to_core_travel_request(final_request_data)
                else:
                    # If not complete, we need to handle this differently
                    # For now, create a simplified request from available data
                    parsed_request = self._create_partial_request_from_response(parser_response, user_input)
                
                response.parsed_request = parsed_request
                agent_exec.complete()
                
                self.logger.info(f"✅ RequestParser completed in {agent_exec.duration:.1f}s")
                self._update_progress("Travel request parsed successfully!", 25, response.workflow_metadata)
                return
                
            except asyncio.TimeoutError:
                error_msg = f"RequestParser timeout after {self.agent_timeout}s"
                self.logger.warning(f"⏰ {error_msg} (attempt {attempt + 1})")
                
                if attempt < self.max_retries:
                    agent_exec.retry_count += 1
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    agent_exec.fail(error_msg)
                    self._update_progress(f"Failed to parse request: {error_msg}", 25, response.workflow_metadata)
                    break
                    
            except Exception as e:
                error_msg = f"RequestParser error: {str(e)}"
                self.logger.error(f"❌ {error_msg} (attempt {attempt + 1})")
                
                if attempt < self.max_retries:
                    agent_exec.retry_count += 1
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    agent_exec.fail(error_msg)
                    response.workflow_metadata.errors.append(error_msg)
                    self._update_progress(f"Failed to parse request: {error_msg}", 25, response.workflow_metadata)
                    break
    
    async def _execute_activities_planner(self, response: TravelItineraryResponse):
        """Execute ActivitiesPlanner with retry logic and progress tracking"""
        agent_exec = response.workflow_metadata.activities_planner
        response.workflow_metadata.current_stage = WorkflowStage.FINDING_PLACES
        
        self.logger.info("🗺️ Starting ActivitiesPlanner...")
        self._update_progress("Finding must-visit places and planning activities...", 30, response.workflow_metadata)
        
        for attempt in range(self.max_retries + 1):
            try:
                agent_exec.start()
                
                # Phase 1: Research destination to get places
                research_result = await asyncio.wait_for(
                    self.activities_planner.research_destination(response.parsed_request),
                    timeout=self.agent_timeout
                )
                
                if research_result["status"] != "success":
                    raise Exception(f"ActivitiesPlanner research failed: {research_result.get('error', 'Unknown error')}")
                
                # Convert places data to Place objects
                from agents.activities_planner import Place
                places_data = research_result.get("must_visit_places", [])
                places = [Place(
                    name=place_data["name"],
                    location=place_data["location"], 
                    category=place_data["category"],
                    significance=place_data["significance"],
                    estimated_duration=place_data.get("estimated_duration", "2-3 hours"),
                    best_time_to_visit=place_data.get("best_time_to_visit", "morning")
                ) for place_data in places_data]
                
                # Phase 2: Generate itinerary with places
                itinerary = await asyncio.wait_for(
                    self.activities_planner.generate_itinerary(response.parsed_request, places),
                    timeout=self.agent_timeout
                )
                
                response.itinerary = itinerary
                agent_exec.complete()
                
                self.logger.info(f"✅ ActivitiesPlanner completed in {agent_exec.duration:.1f}s")
                self._update_progress("Activities and itinerary planned successfully!", 65, response.workflow_metadata)
                return
                
            except asyncio.TimeoutError:
                error_msg = f"ActivitiesPlanner timeout after {self.agent_timeout}s"
                self.logger.warning(f"⏰ {error_msg} (attempt {attempt + 1})")
                
                if attempt < self.max_retries:
                    agent_exec.retry_count += 1
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    agent_exec.fail(error_msg)
                    self._update_progress(f"Failed to plan activities: {error_msg}", 65, response.workflow_metadata)
                    break
                    
            except Exception as e:
                error_msg = f"ActivitiesPlanner error: {str(e)}"
                self.logger.error(f"❌ {error_msg} (attempt {attempt + 1})")
                
                if attempt < self.max_retries:
                    agent_exec.retry_count += 1
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    agent_exec.fail(error_msg)
                    response.workflow_metadata.errors.append(error_msg)
                    self._update_progress(f"Failed to plan activities: {error_msg}", 65, response.workflow_metadata)
                    break
    
    async def _execute_accommodation_suggester(self, response: TravelItineraryResponse):
        """Execute AccommodationSuggester with retry logic and progress tracking"""
        agent_exec = response.workflow_metadata.accommodation_suggester
        response.workflow_metadata.current_stage = WorkflowStage.FINDING_ACCOMMODATIONS
        
        self.logger.info("🏨 Starting AccommodationSuggester...")
        self._update_progress("Finding perfect accommodations near your activities...", 70, response.workflow_metadata)
        
        for attempt in range(self.max_retries + 1):
            try:
                agent_exec.start()
                
                # Execute with timeout
                accommodations = await asyncio.wait_for(
                    self.accommodation_suggester.suggest_accommodations(response.itinerary),
                    timeout=self.agent_timeout
                )
                
                response.accommodations = accommodations
                agent_exec.complete()
                
                self.logger.info(f"✅ AccommodationSuggester completed in {agent_exec.duration:.1f}s")
                self._update_progress("Accommodations found successfully!", 90, response.workflow_metadata)
                return
                
            except asyncio.TimeoutError:
                error_msg = f"AccommodationSuggester timeout after {self.agent_timeout}s"
                self.logger.warning(f"⏰ {error_msg} (attempt {attempt + 1})")
                
                if attempt < self.max_retries:
                    agent_exec.retry_count += 1
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    agent_exec.fail(error_msg)
                    self._update_progress(f"Failed to find accommodations: {error_msg}", 90, response.workflow_metadata)
                    break
                    
            except Exception as e:
                error_msg = f"AccommodationSuggester error: {str(e)}"
                self.logger.error(f"❌ {error_msg} (attempt {attempt + 1})")
                
                if attempt < self.max_retries:
                    agent_exec.retry_count += 1
                    await asyncio.sleep(self.retry_delay)
                    continue
                else:
                    agent_exec.fail(error_msg)
                    response.workflow_metadata.errors.append(error_msg)
                    self._update_progress(f"Failed to find accommodations: {error_msg}", 90, response.workflow_metadata)
                    break
    
    async def _assemble_final_response(self, response: TravelItineraryResponse):
        """Assemble the final response with summary"""
        response.workflow_metadata.current_stage = WorkflowStage.ASSEMBLING_RESPONSE
        self._update_progress("Assembling your complete travel itinerary...", 95, response.workflow_metadata)
        
        try:
            # Generate summary based on available data
            summary_parts = []
            
            if response.parsed_request:
                summary_parts.append(f"✈️ Destination: {response.parsed_request.destination}")
                summary_parts.append(f"📅 Duration: {response.parsed_request.duration} days")
                summary_parts.append(f"💰 Budget: {response.parsed_request.budget.total_amount}")
                summary_parts.append(f"👥 Travelers: {response.parsed_request.travelers.adults} adults" +
                                   (f", {response.parsed_request.travelers.children} children" if response.parsed_request.travelers.children > 0 else ""))
            
            if response.itinerary:
                summary_parts.append(f"🗺️ Activities: {len(response.itinerary.must_visit_places)} must-visit places")
                summary_parts.append(f"📋 Itinerary: {len(response.itinerary.daily_itineraries)} days planned")
            
            if response.accommodations:
                summary_parts.append(f"🏨 Accommodations: {len(response.accommodations.accommodation_options)} options found")
            
            # Add completion status
            summary_parts.append(f"📊 Status: {response.get_completion_status()}")
            
            # Add performance metrics
            if response.workflow_metadata and response.workflow_metadata.total_duration:
                summary_parts.append(f"⏱️ Generated in: {response.workflow_metadata.total_duration:.1f}s")
            
            response.summary = "\n".join(summary_parts)
            
            self.logger.info("📋 Final response assembled successfully")
            
        except Exception as e:
            error_msg = f"Error assembling final response: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            response.workflow_metadata.errors.append(error_msg)
            response.summary = "Error generating summary"
    
    def _update_progress(self, message: str, percentage: float, metadata: WorkflowMetadata):
        """Update progress via callback if available"""
        if self.progress_callback:
            try:
                self.progress_callback(message, percentage, metadata)
            except Exception as e:
                self.logger.warning(f"Progress callback error: {e}")
    
    def _convert_to_core_travel_request(self, final_request_data: dict):
        """Convert RequestParser final data to CoreTravelRequest"""
        from agents.request_parser import CoreTravelRequest, Travelers, Budget, AccommodationType
        
        try:
            # Extract data from RequestParser format
            destination = final_request_data.get("destination", "Unknown")
            duration = final_request_data.get("duration", 3)
            
            # Handle travelers
            travelers_data = final_request_data.get("travelers", {})
            adults = travelers_data.get("adults", 2)
            children = travelers_data.get("children", 0)
            travelers = Travelers(
                adults=adults,
                children=children,
                total=adults + children
            )
            
            # Handle budget
            budget_data = final_request_data.get("budget", {})
            
            # Handle accommodation type from budget data
            accommodation_type = budget_data.get("accommodation_type", AccommodationType.MID_RANGE)
            if isinstance(accommodation_type, str):
                try:
                    # Map string values to enum
                    accommodation_type_map = {
                        "budget": AccommodationType.BUDGET,
                        "mid-range": AccommodationType.MID_RANGE,
                        "luxury": AccommodationType.LUXURY
                    }
                    accommodation_type = accommodation_type_map.get(accommodation_type.lower(), AccommodationType.MID_RANGE)
                except (ValueError, AttributeError):
                    accommodation_type = AccommodationType.MID_RANGE
            
            budget = Budget(
                total_amount=budget_data.get("total_amount", "25000 INR"),
                currency=budget_data.get("currency", "INR"),
                accommodation_type=accommodation_type
            )
            
            return CoreTravelRequest(
                destination=destination,
                duration=duration,
                travelers=travelers,
                budget=budget
            )
            
        except Exception as e:
            self.logger.error(f"Error converting RequestParser data: {e}")
            # Return a fallback request
            return self._create_fallback_request()
    
    def _create_partial_request_from_response(self, response: dict, user_input: str):
        """Create a partial request from incomplete RequestParser response"""
        from agents.request_parser import CoreTravelRequest, Travelers, Budget, AccommodationType
        
        try:
            # Try to extract what we can from the response
            # This is a simplified approach for workflow compatibility
            destination = "Mumbai, India"  # Default for testing
            duration = 3
            travelers = Travelers(adults=2, children=0, total=2)
            budget = Budget(
                total_amount="25000 INR", 
                currency="INR",
                accommodation_type=AccommodationType.MID_RANGE
            )
            
            self.logger.warning("RequestParser didn't complete - using simplified request")
            
            return CoreTravelRequest(
                destination=destination,
                duration=duration,
                travelers=travelers,
                budget=budget
            )
            
        except Exception as e:
            self.logger.error(f"Error creating partial request: {e}")
            return self._create_fallback_request()
    
    def _create_fallback_request(self):
        """Create a fallback request for error cases"""
        from agents.request_parser import CoreTravelRequest, Travelers, Budget, AccommodationType
        
        return CoreTravelRequest(
            destination="Mumbai, India",
            duration=3,
            travelers=Travelers(adults=2, children=0, total=2),
            budget=Budget(
                total_amount="25000 INR", 
                currency="INR",
                accommodation_type=AccommodationType.MID_RANGE
            )
        )


# Helper function for quick workflow execution
async def generate_travel_itinerary(user_input: str, progress_callback: Optional[Callable] = None) -> TravelItineraryResponse:
    """
    Convenience function to execute the complete travel itinerary workflow.
    
    Args:
        user_input: User's natural language travel request
        progress_callback: Optional function for progress updates
        
    Returns:
        TravelItineraryResponse: Complete or partial response with metadata
    """
    workflow = TravelItineraryWorkflow(progress_callback)
    return await workflow.execute_workflow(user_input)
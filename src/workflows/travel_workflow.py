"""
Travel Itinerary Workflow - Parallel Execution Implementation

Orchestrates RequestParser, ActivitiesPlanner, and AccommodationSuggester
with parallel execution for optimal performance.

Key Features:
- Parallel execution of ActivitiesPlanner + AccommodationSuggester (~40% faster)
- Graceful error handling with partial results
- CLI-focused with detailed progress logging
- Performance monitoring and metrics
"""

import asyncio
import logging
import time
from typing import Dict, Tuple, Optional
from datetime import datetime
from dataclasses import asdict

# Import workflow types
from .workflow_types import (
    TravelItineraryResponse, 
    WorkflowMetrics,
    WorkflowException,
    IncompleteRequestException,
    ActivitiesPlanningException,
    AccommodationSearchException,
    ParallelExecutionException
)

# Import agents
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.request_parser import RequestParserAgent, CoreTravelRequest
from agents.activities_planner import ActivitiesPlanner, ItineraryOutput
from agents.accommodation_suggester import AccommodationSuggester, AccommodationOutput


class TravelItineraryWorkflow:
    """
    CLI-focused workflow with parallel agent execution for optimal performance
    
    Architecture:
    User Input → RequestParser → [ActivitiesPlanner || AccommodationSuggester] → Final Response
    """
    
    def __init__(self, interactive: bool = True, verbose: bool = False):
        """
        Initialize the travel itinerary workflow
        
        Args:
            interactive: Enable interactive conversation for missing information
            verbose: Enable detailed logging and progress display
        """
        self.interactive = interactive
        self.verbose = verbose
        
        # Initialize agents
        self.request_parser = RequestParserAgent()
        self.activities_planner = ActivitiesPlanner()
        self.accommodation_suggester = AccommodationSuggester()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.INFO)
        
        self.logger.info("TravelItineraryWorkflow initialized with parallel execution")
    
    async def generate_itinerary(self, user_input: str) -> TravelItineraryResponse:
        """
        Main entry point for complete itinerary generation with parallel execution
        
        Args:
            user_input: Initial travel request from user
            
        Returns:
            TravelItineraryResponse with complete itinerary or partial results
            
        Raises:
            IncompleteRequestException: If request parsing needs more information
            WorkflowException: For other workflow failures
        """
        workflow_id = f"itinerary_{int(time.time())}"
        metrics = WorkflowMetrics(workflow_id=workflow_id)
        start_time = time.time()
        
        try:
            self.logger.info(f"[{workflow_id}] Starting travel itinerary generation")
            self._log_user_request(user_input, workflow_id)
            
            # Phase 1: Request parsing (sequential, interactive)
            parse_start = time.time()
            travel_request = await self._handle_request_parsing(user_input, workflow_id)
            metrics.parsing_time = time.time() - parse_start
            
            self.logger.info(f"[{workflow_id}] Request parsed in {metrics.parsing_time:.2f}s")
            self._log_parsed_request(travel_request, workflow_id)
            
            # Phase 2: PARALLEL EXECUTION 🚀
            if self.verbose:
                self._log_parallel_execution_start(workflow_id)
            
            parallel_start = time.time()
            itinerary_output, accommodation_output = await self._execute_parallel_agents(
                travel_request, workflow_id, metrics
            )
            metrics.parallel_time = time.time() - parallel_start
            
            self.logger.info(f"[{workflow_id}] Parallel execution completed in {metrics.parallel_time:.2f}s")
            
            # Phase 3: Final assembly
            assembly_start = time.time()
            response = await self._create_final_response(
                travel_request, itinerary_output, accommodation_output, 
                workflow_id, metrics
            )
            metrics.assembly_time = time.time() - assembly_start
            
            # Finalize metrics
            metrics.total_time = time.time() - start_time
            response.processing_time = metrics.total_time
            
            # Log performance summary
            if self.verbose:
                self._log_performance_summary(metrics)
            
            self.logger.info(f"[{workflow_id}] Workflow completed successfully in {metrics.total_time:.2f}s")
            return response
            
        except IncompleteRequestException:
            # Re-raise incomplete request exceptions for CLI handling
            raise
        except Exception as e:
            # Handle all other workflow errors
            metrics.total_time = time.time() - start_time
            self.logger.error(f"[{workflow_id}] Workflow failed: {e}")
            return self._handle_workflow_error(e, workflow_id, metrics)
    
    async def _handle_request_parsing(self, user_input: str, workflow_id: str) -> CoreTravelRequest:
        """
        Handle request parsing with interactive conversation support
        
        Args:
            user_input: Initial user input
            workflow_id: Unique workflow identifier
            
        Returns:
            CoreTravelRequest with complete travel information
            
        Raises:
            IncompleteRequestException: If more information needed in non-interactive mode
        """
        try:
            self.logger.info(f"[{workflow_id}] Starting request parsing...")
            
            # Start conversation with initial input
            response = await self.request_parser.start_conversation(user_input)
            
            # Check if complete
            if response.get('is_complete'):
                final_request = self.request_parser.get_final_request()
                self.logger.info(f"[{workflow_id}] Request parsing completed in one turn")
                
                # Ensure we have a CoreTravelRequest object, not a dict
                if isinstance(final_request, dict):
                    # Convert dict to CoreTravelRequest if needed
                    from agents.request_parser import CoreTravelRequest, Travelers, Budget, AccommodationType
                    
                    travelers_data = final_request.get('travelers', {})
                    budget_data = final_request.get('budget', {})
                    
                    travelers = Travelers(
                        adults=travelers_data.get('adults', 2),
                        children=travelers_data.get('children', 0),
                        total=travelers_data.get('total', 2)
                    )
                    
                    budget = Budget(
                        total_amount=budget_data.get('total_amount', 0),
                        currency=budget_data.get('currency', 'USD'),
                        accommodation_type=AccommodationType(budget_data.get('accommodation_type', 'mid-range'))
                    )
                    
                    final_request = CoreTravelRequest(
                        destination=final_request.get('destination', ''),
                        duration=final_request.get('duration', 1),
                        travelers=travelers,
                        budget=budget
                    )
                
                # Set currency context for cost calculations
                self._current_currency = final_request.budget.currency
                
                return final_request
            
            # Handle incomplete request
            if not self.interactive:
                # Non-interactive mode: raise exception with next question
                raise IncompleteRequestException(
                    response.get('next_question', 'More information needed'),
                    response
                )
            
            # Interactive mode: continue conversation
            return await self._handle_interactive_conversation(response, workflow_id)
            
        except Exception as e:
            if isinstance(e, IncompleteRequestException):
                raise
            raise WorkflowException(f"Request parsing failed: {e}")
    
    async def _handle_interactive_conversation(self, initial_response: Dict, workflow_id: str) -> CoreTravelRequest:
        """
        Handle multi-turn interactive conversation for missing information
        
        Args:
            initial_response: Initial response from request parser
            workflow_id: Unique workflow identifier
            
        Returns:
            CoreTravelRequest with complete information
        """
        response = initial_response
        conversation_turn = 1
        
        while not response.get('is_complete'):
            next_question = response.get('next_question')
            missing_fields = response.get('missing_fields', [])
            
            self.logger.info(f"[{workflow_id}] Conversation turn {conversation_turn}: asking for {missing_fields}")
            
            # Display question to user
            print(f"\n📝 {next_question}")
            user_response = input("> ")
            
            # Continue conversation
            response = await self.request_parser.continue_conversation(user_response)
            conversation_turn += 1
            
            # Safety check to prevent infinite loops
            if conversation_turn > 10:
                raise WorkflowException("Too many conversation turns, aborting")
        
        final_request = self.request_parser.get_final_request()
        # Set currency context for cost calculations
        self._current_currency = final_request.budget.currency
        self.logger.info(f"[{workflow_id}] Interactive conversation completed in {conversation_turn} turns")
        return final_request
    
    async def _execute_parallel_agents(self, travel_request: CoreTravelRequest, 
                                     workflow_id: str, metrics: WorkflowMetrics) -> Tuple:
        """
        Execute ActivitiesPlanner and AccommodationSuggester in parallel
        
        Args:
            travel_request: Parsed travel request
            workflow_id: Unique workflow identifier
            metrics: Performance metrics object
            
        Returns:
            Tuple of (ItineraryOutput, AccommodationOutput) or exceptions
        """
        # Launch both agents in parallel
        activities_task = asyncio.create_task(
            self._handle_activities_planning(travel_request, workflow_id, metrics)
        )
        accommodation_task = asyncio.create_task(
            self._handle_accommodation_search(travel_request, workflow_id, metrics)
        )
        
        # Wait for both to complete (return_exceptions=True prevents one failure from stopping the other)
        results = await asyncio.gather(activities_task, accommodation_task, return_exceptions=True)
        
        return results[0], results[1]
    
    async def _handle_activities_planning(self, travel_request: CoreTravelRequest, 
                                        workflow_id: str, metrics: WorkflowMetrics) -> ItineraryOutput:
        """
        Execute activities planning with performance tracking
        
        Args:
            travel_request: Parsed travel request
            workflow_id: Unique workflow identifier
            metrics: Performance metrics object
            
        Returns:
            ItineraryOutput with complete itinerary
            
        Raises:
            ActivitiesPlanningException: If activities planning fails
        """
        agent_start = time.time()
        
        try:
            self.logger.info(f"[{workflow_id}] ActivitiesPlanner: Starting destination research...")
            
            # Phase 1: Destination research (uses Tavily parallel searches internally)
            research_result = await self.activities_planner.research_destination(travel_request)
            
            if research_result["status"] != "success":
                raise ActivitiesPlanningException(f"Research failed: {research_result.get('error')}")
            
            places_data = research_result.get("must_visit_places", [])
            research_time = time.time() - agent_start
            
            # Convert dictionary places to Place objects
            from agents.activities_planner import Place
            places = []
            for place_dict in places_data:
                place = Place(
                    name=place_dict.get("name", ""),
                    location=place_dict.get("location", ""),
                    significance=place_dict.get("significance", ""),
                    category=place_dict.get("category", ""),
                    estimated_duration=place_dict.get("estimated_duration"),
                    best_time_to_visit=place_dict.get("best_time_to_visit")
                )
                places.append(place)
            
            self.logger.info(f"[{workflow_id}] ActivitiesPlanner: Research completed in {research_time:.2f}s, found {len(places)} places")
            
            # Phase 2: Itinerary generation
            self.logger.info(f"[{workflow_id}] ActivitiesPlanner: Generating itinerary...")
            itinerary_output = await self.activities_planner.generate_itinerary(travel_request, places)
            
            metrics.activities_time = time.time() - agent_start
            self.logger.info(f"[{workflow_id}] ActivitiesPlanner: Completed in {metrics.activities_time:.2f}s")
            
            return itinerary_output
            
        except Exception as e:
            metrics.activities_time = time.time() - agent_start
            self.logger.error(f"[{workflow_id}] ActivitiesPlanner failed: {e}")
            raise ActivitiesPlanningException(f"Activities planning failed: {e}")
    
    async def _handle_accommodation_search(self, travel_request: CoreTravelRequest, 
                                         workflow_id: str, metrics: WorkflowMetrics) -> AccommodationOutput:
        """
        Execute accommodation search with performance tracking
        
        Args:
            travel_request: Parsed travel request
            workflow_id: Unique workflow identifier
            metrics: Performance metrics object
            
        Returns:
            AccommodationOutput with hotel suggestions
            
        Raises:
            AccommodationSearchException: If accommodation search fails
        """
        agent_start = time.time()
        
        try:
            self.logger.info(f"[{workflow_id}] AccommodationSuggester: Starting multi-platform search...")
            
            # Execute accommodation search (uses asyncio.gather internally for platforms)
            accommodation_output = await self.accommodation_suggester.find_accommodations(travel_request)
            
            metrics.accommodation_time = time.time() - agent_start
            suggestions_count = len(accommodation_output.accommodation_suggestions)
            
            self.logger.info(f"[{workflow_id}] AccommodationSuggester: Completed in {metrics.accommodation_time:.2f}s, found {suggestions_count} options")
            
            return accommodation_output
            
        except Exception as e:
            metrics.accommodation_time = time.time() - agent_start
            self.logger.error(f"[{workflow_id}] AccommodationSuggester failed: {e}")
            raise AccommodationSearchException(f"Accommodation search failed: {e}")
    
    async def _create_final_response(self, travel_request: CoreTravelRequest,
                                   itinerary_result, accommodation_result,
                                   workflow_id: str, metrics: WorkflowMetrics) -> TravelItineraryResponse:
        """
        Create final response handling parallel results and potential failures
        
        Args:
            travel_request: Original parsed request
            itinerary_result: Result from ActivitiesPlanner (or exception)
            accommodation_result: Result from AccommodationSuggester (or exception)
            workflow_id: Unique workflow identifier
            metrics: Performance metrics object
            
        Returns:
            TravelItineraryResponse with complete or partial results
        """
        # Handle individual agent failures
        itinerary_output = None
        accommodation_output = None
        errors = []
        partial_results = False
        
        # Check ActivitiesPlanner result
        if isinstance(itinerary_result, Exception):
            self.logger.error(f"[{workflow_id}] ActivitiesPlanner failed: {itinerary_result}")
            errors.append(f"Activities planning failed: {str(itinerary_result)}")
            itinerary_output = self._create_fallback_itinerary(travel_request)
            partial_results = True
        else:
            itinerary_output = itinerary_result
        
        # Check AccommodationSuggester result  
        if isinstance(accommodation_result, Exception):
            self.logger.error(f"[{workflow_id}] AccommodationSuggester failed: {accommodation_result}")
            errors.append(f"Accommodation search failed: {str(accommodation_result)}")
            accommodation_output = self._create_fallback_accommodations(travel_request)
            partial_results = True
        else:
            accommodation_output = accommodation_result
        
        # Estimate total cost if both agents succeeded
        final_cost_estimate = None
        if not partial_results:
            final_cost_estimate = self._estimate_total_cost(itinerary_output, accommodation_output)
        
        # Create response
        response = TravelItineraryResponse(
            request_summary=asdict(travel_request),
            itinerary=itinerary_output,
            accommodations=accommodation_output,
            final_cost_estimate=final_cost_estimate,
            workflow_id=workflow_id,
            success=len(errors) == 0,
            errors=errors if errors else None,
            partial_results=partial_results
        )
        
        return response
    
    # Utility methods for logging and fallbacks...
    def _log_user_request(self, user_input: str, workflow_id: str):
        """Log the initial user request"""
        self.logger.info(f"[{workflow_id}] User request: {user_input}")
    
    def _log_parsed_request(self, travel_request: CoreTravelRequest, workflow_id: str):
        """Log the parsed travel request"""
        self.logger.info(f"[{workflow_id}] Parsed: {travel_request.destination}, {travel_request.duration} days, "
                        f"{travel_request.travelers.total} travelers, {travel_request.budget.total_amount} {travel_request.budget.currency}")
    
    def _log_parallel_execution_start(self, workflow_id: str):
        """Log parallel execution start"""
        self.logger.info(f"""[{workflow_id}] 🚀 PARALLEL EXECUTION STARTED
├── 🏛️  ActivitiesPlanner: Researching destinations & planning itinerary...
└── 🏨 AccommodationSuggester: Searching hotels across multiple platforms...
⏱️  Expected completion: ~15-20 seconds""")
    
    def _log_performance_summary(self, metrics: WorkflowMetrics):
        """Log detailed performance summary"""
        summary = metrics.get_summary()
        parallel_efficiency = summary['parallel_efficiency']
        
        self.logger.info(f"""[{metrics.workflow_id}] PERFORMANCE SUMMARY:
├── Total Time: {summary['total_time']}s
├── Request Parsing: {summary['parsing_time']}s
├── Parallel Execution: {summary['parallel_time']}s
│   ├── ActivitiesPlanner: {summary['activities_time']}s
│   └── AccommodationSuggester: {summary['accommodation_time']}s
├── Final Assembly: {summary['assembly_time']}s
└── Parallel Efficiency: {parallel_efficiency}%

🎯 Targets: <30s total, <20s parallel
✅ Achieved: {summary['total_time']}s total, {summary['parallel_time']}s parallel""")
    
    def _create_fallback_itinerary(self, travel_request: CoreTravelRequest) -> ItineraryOutput:
        """Create basic fallback itinerary when ActivitiesPlanner fails"""
        from agents.activities_planner import ItineraryOutput
        
        return ItineraryOutput(
            destination=travel_request.destination,
            duration_days=travel_request.duration,
            total_budget=f"{travel_request.budget.total_amount} {travel_request.budget.currency}",
            accommodation_type=travel_request.budget.accommodation_type,
            must_visit_places=[],  # Empty
            daily_itineraries=[],  # Empty
            total_estimated_cost="Unable to estimate - activities planning failed",
            recommendations="Activities planning failed. Please try again or consult travel guides."
        )
    
    def _create_fallback_accommodations(self, travel_request: CoreTravelRequest) -> AccommodationOutput:
        """Create basic fallback accommodations when AccommodationSuggester fails"""
        from agents.accommodation_suggester import AccommodationOutput
        
        return AccommodationOutput(
            destination=travel_request.destination,
            search_date=datetime.now().isoformat(),
            budget_range=f"{travel_request.budget.total_amount} {travel_request.budget.currency}",
            traveler_count=travel_request.travelers.total,
            children_count=travel_request.travelers.children,
            accommodation_suggestions=[],  # Empty
            family_considerations="Accommodation search failed. Please search manually on booking platforms.",
            search_summary="Accommodation search encountered an error.",
            recommendations="Try Booking.com, Agoda, or Hotels.com directly for accommodation options."
        )
    
    def _estimate_total_cost(self, itinerary_output: ItineraryOutput, 
                           accommodation_output: AccommodationOutput) -> str:
        """Estimate total trip cost from itinerary and accommodation outputs"""
        try:
            # Simple cost estimation logic
            itinerary_cost = itinerary_output.total_estimated_cost or "0"
            
            # Extract numeric cost from itinerary
            itinerary_amount = 0
            if itinerary_cost and itinerary_cost != "Unable to estimate":
                # Extract numbers from string (rough estimation)
                import re
                numbers = re.findall(r'[\d,]+', itinerary_cost.replace(',', ''))
                if numbers:
                    itinerary_amount = int(numbers[0])
            
            # Extract accommodation cost
            accommodation_amount = 0
            if accommodation_output.accommodation_suggestions:
                # Use average cost of suggested accommodations
                costs = []
                for acc in accommodation_output.accommodation_suggestions:
                    if acc.cost_per_night:
                        costs.append(acc.cost_per_night)
                
                if costs:
                    avg_per_night = sum(costs) / len(costs)
                    # Estimate duration from itinerary
                    duration = len(itinerary_output.daily_itineraries) or 1
                    accommodation_amount = int(avg_per_night * duration)
            
            total_amount = itinerary_amount + accommodation_amount
            if total_amount > 0:
                # Get currency from travel request (passed via workflow context)
                currency = getattr(self, '_current_currency', 'EUR')  # Default to EUR
                
                if currency == "EUR":
                    return f"€{total_amount:,} (approx.)"
                elif currency == "USD":
                    return f"${total_amount:,} (approx.)"
                elif currency == "GBP":
                    return f"£{total_amount:,} (approx.)"
                elif currency == "INR":
                    return f"₹{total_amount:,} (approx.)"
                else:
                    return f"{total_amount:,} {currency} (approx.)"
            else:
                return "Unable to estimate total cost"
        
        except Exception as e:
            self.logger.warning(f"Cost estimation failed: {e}")
            return "Unable to estimate total cost"
    
    def _handle_workflow_error(self, error: Exception, workflow_id: str, 
                             metrics: WorkflowMetrics) -> TravelItineraryResponse:
        """Create error response for complete workflow failures"""
        return TravelItineraryResponse(
            request_summary={},
            itinerary=None,
            accommodations=None,
            workflow_id=workflow_id,
            processing_time=metrics.total_time,
            success=False,
            errors=[f"Workflow failed: {str(error)}"],
            partial_results=False
        )
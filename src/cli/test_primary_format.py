#!/usr/bin/env python3
"""
Test script for the new primary schema output format

Tests the primary format output without full workflow execution.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cli.generate_itinerary import format_primary_output
from workflows.data_models import TravelItineraryResponse, WorkflowMetadata, AgentExecution
from agents.request_parser import CoreTravelRequest, Travelers, Budget, AccommodationType
from agents.activities_planner import Place, ItineraryOutput
from agents.accommodation_suggester import AccommodationOption, AccommodationOutput


def create_sample_response():
    """Create a sample TravelItineraryResponse for testing"""
    
    # Create sample parsed request
    travelers = Travelers(adults=2, children=1, total=3)
    budget = Budget(
        total_amount="25000 INR", 
        currency="INR",
        accommodation_type=AccommodationType.MID_RANGE
    )
    parsed_request = CoreTravelRequest(
        destination="Mumbai, India",
        duration=3,
        travelers=travelers,
        budget=budget
    )
    
    # Create sample places
    places = [
        Place(
            name="Gateway of India",
            location="Apollo Bandar, Mumbai",
            category="Historical Monument",
            significance="Iconic arch monument built in 1924, symbol of Mumbai and major tourist attraction",
            estimated_duration="2-3 hours"
        ),
        Place(
            name="Marine Drive",
            location="Netaji Subhash Chandra Bose Road, Mumbai",
            category="Scenic Drive",
            significance="Famous curved boulevard along the coast, known as Queen's Necklace for its beautiful night lighting",
            estimated_duration="1-2 hours"
        ),
        Place(
            name="Chhatrapati Shivaji Terminus",
            location="Fort, Mumbai",
            category="UNESCO World Heritage Site",
            significance="Historic railway station showcasing Victorian Gothic architecture, UNESCO World Heritage Site since 2004",
            estimated_duration="1 hour"
        )
    ]
    
    # Create sample itinerary
    itinerary = ItineraryOutput(
        destination="Mumbai, India",
        duration_days=3,
        total_budget="25000 INR",
        accommodation_type=AccommodationType.MID_RANGE,
        must_visit_places=places,
        daily_itineraries=[],  # Simplified for testing
        total_estimated_cost="₹12,000-15,000",
        recommendations="Perfect blend of historical sites and modern attractions"
    )
    
    # Create sample accommodations
    accommodations_list = [
        AccommodationOption(
            name="Hotel Marine Plaza",
            location="Marine Drive, Mumbai",
            price_per_night="₹4,500",
            total_cost="₹13,500",
            rating="4.2/5",
            brief_description="Luxury hotel overlooking Marine Drive with excellent city views and modern amenities",
            proximity_score="Excellent - Walking distance to Marine Drive and Gateway of India"
        ),
        AccommodationOption(
            name="The Gordon House Hotel",
            location="Colaba, Mumbai", 
            price_per_night="₹3,800",
            total_cost="₹11,400",
            rating="4.0/5",
            brief_description="Boutique hotel in heritage building with unique themed rooms and central location",
            proximity_score="Very Good - Near Gateway of India and Colaba Causeway"
        )
    ]
    
    accommodations = AccommodationOutput(
        destination="Mumbai, India",
        duration_days=3,
        budget_allocated=10000.0,  # 40% of 25000 INR
        budget_category="medium",
        nightly_budget_range="₹3000-4500",
        key_activity_areas=["South Mumbai", "Colaba", "Fort", "Marine Drive"],
        accommodation_options=accommodations_list
    )
    
    # Create sample workflow metadata
    agent_metadata = [
        AgentExecution(
            agent_name="RequestParser",
            start_time=1705401600.0,  # Unix timestamp
            end_time=1705401608.2,
            duration=8.2,
            status="completed",
            error_message=None
        ),
        AgentExecution(
            agent_name="ActivitiesPlanner", 
            start_time=1705401608.2,
            end_time=1705401675.5,
            duration=67.3,
            status="completed",
            error_message=None
        ),
        AgentExecution(
            agent_name="AccommodationSuggester",
            start_time=1705401675.5,
            end_time=1705401765.6,
            duration=90.1,
            status="completed",
            error_message=None
        )
    ]
    
    workflow_metadata = WorkflowMetadata(
        workflow_id="test-primary-format-001",
        total_start_time=1705401600.0,
        total_end_time=1705401765.6,
        total_duration=165.6,
        request_parser=agent_metadata[0],
        activities_planner=agent_metadata[1],
        accommodation_suggester=agent_metadata[2]
    )
    
    # Create and return complete response
    return TravelItineraryResponse(
        parsed_request=parsed_request,
        itinerary=itinerary,
        accommodations=accommodations,
        workflow_metadata=workflow_metadata,
        summary="Complete 3-day Mumbai travel itinerary with historical and modern attractions",
        user_input="I want to visit Mumbai, India for 3 days with my family. We are 2 adults and 1 child traveling together. Our total budget for this trip is 25000 INR including accommodation and activities. We prefer mid-range accommodation for our stay."
    )


def main():
    """Test the primary format output"""
    print("🧪 Testing Primary Schema Output Format")
    print("=" * 50)
    print()
    
    # Create sample response
    response = create_sample_response()
    
    # Generate primary format output
    print("📋 Generating primary schema format...")
    primary_output = format_primary_output(response)
    
    print()
    print("🎯 PRIMARY SCHEMA OUTPUT:")
    print("-" * 30)
    print(primary_output)
    
    print()
    print("✅ Primary format test completed successfully!")


if __name__ == "__main__":
    main()
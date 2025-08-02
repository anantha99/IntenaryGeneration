#!/usr/bin/env python3
"""
Simple test script for Travel Itinerary Workflow

Tests the complete workflow without progress bar, using a comprehensive input
that should allow RequestParser to complete in one go without conversation.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workflows.travel_itinerary_workflow import generate_travel_itinerary
from workflows.data_models import TravelItineraryResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def print_section_header(title: str):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_workflow_summary(response: TravelItineraryResponse):
    """Print a summary of the workflow execution"""
    print_section_header("WORKFLOW EXECUTION SUMMARY")
    
    print(f"📧 Original Input: {response.user_input}")
    print(f"📊 Completion Status: {response.get_completion_status()}")
    print(f"✅ Is Complete: {response.is_complete()}")
    print(f"⚠️  Is Partial: {response.is_partial()}")
    
    if response.workflow_metadata:
        print(f"🆔 Workflow ID: {response.workflow_metadata.workflow_id}")
        print(f"⏱️  Total Duration: {response.workflow_metadata.total_duration:.1f}s")
        print(f"📈 Completion %: {response.workflow_metadata.get_completion_percentage():.1f}%")
        print(f"🏃 Overall Status: {response.workflow_metadata.overall_status}")
        
        # Agent status
        print(f"\n🤖 Agent Execution Status:")
        agents = [
            response.workflow_metadata.request_parser,
            response.workflow_metadata.activities_planner,
            response.workflow_metadata.accommodation_suggester
        ]
        
        for agent in agents:
            status_icon = "✅" if agent.status.value == "completed" else "❌" if agent.status.value == "failed" else "⏸️"
            duration_text = f"({agent.duration:.1f}s)" if agent.duration else "(no duration)"
            print(f"  {status_icon} {agent.agent_name}: {agent.status.value} {duration_text}")
            if agent.error_message:
                print(f"      Error: {agent.error_message}")
            if agent.retry_count > 0:
                print(f"      Retries: {agent.retry_count}")
        
        # Errors
        if response.workflow_metadata.errors:
            print(f"\n❌ Workflow Errors ({len(response.workflow_metadata.errors)}):")
            for error in response.workflow_metadata.errors:
                print(f"  • {error}")


def print_parsed_request(response: TravelItineraryResponse):
    """Print details of the parsed request"""
    if not response.parsed_request:
        print("❌ No parsed request available")
        return
    
    print_section_header("PARSED REQUEST DETAILS")
    
    req = response.parsed_request
    print(f"🌍 Destination: {req.destination}")
    print(f"📅 Duration: {req.duration} days")
    print(f"👥 Travelers: {req.travelers.adults} adults, {req.travelers.children} children (total: {req.travelers.total})")
    print(f"💰 Budget: {req.budget.total_amount} {req.budget.currency}")
    print(f"🏨 Accommodation Type: {req.budget.accommodation_type.value if req.budget.accommodation_type else 'Not specified'}")


def print_itinerary_summary(response: TravelItineraryResponse):
    """Print summary of the planned itinerary"""
    if not response.itinerary:
        print("❌ No itinerary available")
        return
    
    print_section_header("ITINERARY SUMMARY")
    
    itinerary = response.itinerary
    print(f"🎯 Destination: {itinerary.destination}")
    print(f"📅 Duration: {itinerary.duration_days} days")
    print(f"💰 Total Budget: {itinerary.total_budget}")
    print(f"💵 Estimated Cost: {itinerary.total_estimated_cost}")
    
    print(f"\n🗺️  Must-Visit Places ({len(itinerary.must_visit_places)}):")
    for i, place in enumerate(itinerary.must_visit_places[:5], 1):
        print(f"  {i}. {place.name} - {place.location}")
        print(f"     {place.significance} ({place.category})")
    
    if len(itinerary.must_visit_places) > 5:
        print(f"     ... and {len(itinerary.must_visit_places) - 5} more places")
    
    if itinerary.daily_itineraries:
        print(f"\n📋 Daily Itineraries ({len(itinerary.daily_itineraries)} days):")
        for day in itinerary.daily_itineraries[:2]:  # Show first 2 days
            print(f"  📅 Day {day.day_number}")
            if day.notes:
                print(f"     Theme: {day.notes}")
            if day.activities:
                print(f"     Activities: {len(day.activities)} planned")
                for activity in day.activities[:3]:  # Show first 3 activities
                    print(f"       • {activity.name} at {activity.place}")
            if day.total_estimated_cost:
                print(f"     Cost: {day.total_estimated_cost}")
        
        if len(itinerary.daily_itineraries) > 2:
            print(f"     ... and {len(itinerary.daily_itineraries) - 2} more days")
    
    print(f"\n💡 Recommendations:")
    print(f"   {itinerary.recommendations}")


def print_accommodation_summary(response: TravelItineraryResponse):
    """Print summary of accommodation suggestions"""
    if not response.accommodations:
        print("❌ No accommodations available")
        return
    
    print_section_header("ACCOMMODATION SUMMARY")
    
    acc = response.accommodations
    print(f"🎯 Destination: {acc.destination}")
    print(f"📅 Duration: {acc.duration_days} days")
    print(f"💰 Budget Allocated: {acc.budget_allocated}")
    print(f"🏷️  Budget Category: {acc.budget_category}")
    print(f"💵 Nightly Budget Range: {acc.nightly_budget_range}")
    print(f"📍 Key Activity Areas: {', '.join(acc.key_activity_areas)}")
    
    print(f"\n🏨 Accommodation Options ({len(acc.accommodation_options)}):")
    for i, hotel in enumerate(acc.accommodation_options, 1):
        print(f"  {i}. {hotel.name}")
        print(f"     📍 Location: {hotel.location}")
        print(f"     💰 Price: {hotel.price_per_night}/night (Total: {hotel.total_cost})")
        print(f"     ⭐ Rating: {hotel.rating}")
        print(f"     📝 {hotel.brief_description}")
        print(f"     🚶 {hotel.travel_convenience}")


async def test_complete_workflow():
    """Test the complete workflow with a comprehensive input"""
    print_section_header("TESTING COMPLETE WORKFLOW")
    
    # Comprehensive input that should complete RequestParser in one go
    test_input = (
        "I want to visit Mumbai, India for 3 days with my family. "
        "We are 2 adults and 1 child traveling together. "
        "Our total budget for this trip is 25000 INR including accommodation and activities. "
        "We prefer mid-range accommodation for our stay."
    )
    
    print(f"🚀 Testing with input:")
    print(f"   '{test_input}'")
    print(f"\n⏳ Executing workflow... (this may take 2-3 minutes)")
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Execute workflow without progress callback
        response = await generate_travel_itinerary(test_input, progress_callback=None)
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        print(f"\n✅ Workflow completed in {execution_time:.1f} seconds!")
        
        # Print detailed results
        print_workflow_summary(response)
        print_parsed_request(response)
        print_itinerary_summary(response)
        print_accommodation_summary(response)
        
        return response
        
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        print(f"\n❌ Workflow failed after {execution_time:.1f} seconds!")
        print(f"Error: {str(e)}")
        logger.exception("Workflow execution failed")
        return None


async def test_minimal_workflow():
    """Test with minimal input that might require conversation"""
    print_section_header("TESTING MINIMAL INPUT")
    
    minimal_input = "I want to visit Mumbai for 3 days"
    
    print(f"🚀 Testing with minimal input:")
    print(f"   '{minimal_input}'")
    print(f"\n⏳ Executing workflow...")
    
    try:
        response = await generate_travel_itinerary(minimal_input, progress_callback=None)
        
        print(f"\n✅ Minimal input workflow completed!")
        print_workflow_summary(response)
        
        if response.parsed_request:
            print_parsed_request(response)
        
        return response
        
    except Exception as e:
        print(f"\n❌ Minimal workflow failed!")
        print(f"Error: {str(e)}")
        logger.exception("Minimal workflow execution failed")
        return None


async def main():
    """Main test function"""
    print("🧪 TRAVEL ITINERARY WORKFLOW - SIMPLE TESTING")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Complete workflow with comprehensive input
    response1 = await test_complete_workflow()
    
    # Test 2: Minimal input workflow
    response2 = await test_minimal_workflow()
    
    # Summary
    print_section_header("TEST SUMMARY")
    test1_status = "✅ PASSED" if response1 and response1.is_complete() else "❌ FAILED"
    test2_status = "✅ PASSED" if response2 else "❌ FAILED"
    
    print(f"Test 1 (Complete Input): {test1_status}")
    print(f"Test 2 (Minimal Input): {test2_status}")
    
    if response1 and response1.is_complete():
        print(f"\n🎉 SUCCESS: Complete workflow generated full itinerary!")
    elif response1 and response1.is_partial():
        print(f"\n⚠️  PARTIAL: Workflow generated partial results")
    else:
        print(f"\n❌ FAILURE: Workflow did not complete successfully")
    
    print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
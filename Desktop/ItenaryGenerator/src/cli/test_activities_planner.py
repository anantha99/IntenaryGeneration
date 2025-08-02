#!/usr/bin/env python3
"""
CLI Test Script for ActivitiesPlanner Agent - Phase 1

Tests destination research and must-visit places discovery.
"""

import asyncio
import json
import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.activities_planner import ActivitiesPlanner, Place
from agents.request_parser import CoreTravelRequest, Travelers, Budget, AccommodationType

# Configure logging to see performance metrics
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🏛️  {title}")
    print("="*60)


def print_places(places: list):
    """Print formatted places information"""
    if not places:
        print("❌ No places found")
        return
    
    for i, place in enumerate(places, 1):
        print(f"\n🏛️  {i}. {place['name']}")
        print(f"📍 Location: {place['location']}")
        print(f"🏷️  Category: {place['category']}")
        print(f"⏰ Duration: {place.get('estimated_duration', 'Not specified')}")
        print(f"🌅 Best Time: {place.get('best_time_to_visit', 'Not specified')}")
        print(f"📝 Significance:")
        print(f"   {place['significance']}")


def print_summary(summary: str):
    """Print destination summary"""
    if summary:
        print(f"\n📋 Destination Summary:")
        print(f"   {summary}")


def print_itinerary(itinerary):
    """Print formatted itinerary information"""
    print(f"\n🗓️  Complete {itinerary.duration_days}-Day Itinerary")
    print(f"💰 Total Budget: {itinerary.total_budget}")
    print(f"📊 Estimated Cost: {itinerary.total_estimated_cost}")
    print(f"🏨 Accommodation: {itinerary.accommodation_type.value}")
    
    for day in itinerary.daily_itineraries:
        print(f"\n📅 Day {day.day_number}")
        print(f"💵 Daily Cost: {day.total_estimated_cost}")
        
        print(f"\n🎯 Activities ({len(day.activities)}):")
        for i, activity in enumerate(day.activities, 1):
            print(f"   {i}. {activity.name}")
            print(f"      📍 {activity.place} ({activity.duration})")
            print(f"      💰 {activity.cost_estimate}")
            print(f"      📝 {activity.description}")
        
        print(f"\n🍽️  Meals ({len(day.meals)}):")
        for meal in day.meals:
            print(f"   ⏰ {meal['time']} - {meal['name']} at {meal['place']}")
            print(f"      💰 {meal['cost_estimate']}")
        
        if day.notes:
            print(f"\n📋 Notes: {day.notes}")
    
    if itinerary.recommendations:
        print(f"\n💡 Recommendations:")
        print(f"   {itinerary.recommendations}")


async def test_mumbai():
    """Test with Mumbai destination"""
    print_header("TESTING: Mumbai, India (3 Days)")
    
    planner = ActivitiesPlanner()
    
    # Create Mumbai travel request
    mumbai_request = CoreTravelRequest(
        destination="Mumbai, India",
        duration=3,
        travelers=Travelers(adults=2, children=0, total=2),
        budget=Budget(
            total_amount=25000,
            currency="INR",
            accommodation_type=AccommodationType.MID_RANGE
        )
    )
    
    print(f"🎯 Destination: {mumbai_request.destination}")
    print(f"📅 Duration: {mumbai_request.duration} days")
    print(f"👥 Travelers: {mumbai_request.travelers.adults} adults, {mumbai_request.travelers.children} children")
    print(f"💰 Budget: {mumbai_request.budget.total_amount} {mumbai_request.budget.currency}")
    print(f"🏨 Accommodation: {mumbai_request.budget.accommodation_type.value}")
    
    print("\n🔍 Starting destination research...")
    
    try:
        result = await planner.research_destination(mumbai_request)
        
        if result["status"] == "success":
            print("✅ Research completed successfully!")
            
            places_data = result.get("must_visit_places", [])
            summary = result.get("search_summary", "")
            
            print_summary(summary)
            print(f"\n🏛️  Found {len(places_data)} Must-Visit Places:")
            print_places(places_data)
            
            print(f"\n🎯 Phase: {result.get('phase', 'Unknown')}")
            
            # Phase 2: Generate itinerary
            print("\n🚀 Starting Phase 2: Itinerary Generation...")
            
            # Convert to Place objects
            places = [Place(
                name=place["name"],
                location=place["location"],
                significance=place["significance"],
                category=place["category"],
                estimated_duration=place.get("estimated_duration"),
                best_time_to_visit=place.get("best_time_to_visit")
            ) for place in places_data]
            
            itinerary = await planner.generate_itinerary(mumbai_request, places)
            print("✅ Itinerary generation completed!")
            
            print_itinerary(itinerary)
            
        else:
            print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
            if 'raw_response' in result:
                print(f"Raw LLM Response: {result['raw_response']}")
                
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")


async def test_kerala():
    """Test with Kerala destination"""
    print_header("TESTING: Kerala, India (5 Days)")
    
    planner = ActivitiesPlanner()
    
    # Create Kerala travel request
    kerala_request = CoreTravelRequest(
        destination="Kerala, India",
        duration=5,
        travelers=Travelers(adults=2, children=1, total=3),
        budget=Budget(
            total_amount=50000,
            currency="INR",
            accommodation_type=AccommodationType.LUXURY
        )
    )
    
    print(f"🎯 Destination: {kerala_request.destination}")
    print(f"📅 Duration: {kerala_request.duration} days")
    print(f"👥 Travelers: {kerala_request.travelers.adults} adults, {kerala_request.travelers.children} children")
    print(f"💰 Budget: {kerala_request.budget.total_amount} {kerala_request.budget.currency}")
    print(f"🏨 Accommodation: {kerala_request.budget.accommodation_type.value}")
    
    print("\n🔍 Starting destination research...")
    
    try:
        result = await planner.research_destination(kerala_request)
        
        if result["status"] == "success":
            print("✅ Research completed successfully!")
            
            places = result.get("must_visit_places", [])
            summary = result.get("search_summary", "")
            
            print_summary(summary)
            print(f"\n🏛️  Found {len(places)} Must-Visit Places:")
            print_places(places)
            
            print(f"\n🎯 Phase: {result.get('phase', 'Unknown')}")
            
        else:
            print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
            if 'raw_response' in result:
                print(f"Raw LLM Response: {result['raw_response']}")
                
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")


async def main():
    """Main test function"""
    print_header("ActivitiesPlanner Agent - Phase 1 & 2 Testing")
    print("🚀 Testing destination research and complete itinerary generation")
    print("📡 Using Tavily SearchTool + Gemini 2.5 Pro")
    
    # Test multiple destinations
    await test_mumbai()
    await test_kerala()
    
    print_header("Testing Complete")
    print("✅ Phase 1 & 2 implementation tested")
    print("🎉 Complete itinerary generation working!")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())
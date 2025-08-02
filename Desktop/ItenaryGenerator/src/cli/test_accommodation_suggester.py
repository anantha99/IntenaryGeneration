"""
CLI Test Script for AccommodationSuggester Agent

Tests accommodation suggestions with different budget scenarios and activity locations.
"""

import asyncio
import json
import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.accommodation_suggester import AccommodationSuggester, AccommodationOutput
from agents.activities_planner import ItineraryOutput, Place, DayItinerary, Activity
from agents.request_parser import AccommodationType

# Configure logging to see performance metrics
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🏨  {title}")
    print("="*60)


def print_accommodation_results(result: AccommodationOutput):
    """Print formatted accommodation results"""
    print(f"\n🎯 Destination: {result.destination}")
    print(f"📅 Duration: {result.duration_days} days")
    print(f"💰 Budget Allocated: {result.budget_allocated} (40% of total)")
    print(f"🏷️  Budget Category: {result.budget_category}")
    print(f"💵 Nightly Budget Range: {result.nightly_budget_range}")
    print(f"📍 Key Activity Areas: {', '.join(result.key_activity_areas)}")
    
    print(f"\n🏨 Accommodation Options ({len(result.accommodation_options)}):")
    for i, option in enumerate(result.accommodation_options, 1):
        print(f"\n{i}. {option.name}")
        print(f"   📍 Location: {option.location}")
        print(f"   💰 Price: {option.price_per_night}/night")
        print(f"   💵 Total Cost: {option.total_cost}")
        print(f"   ⭐ Rating: {option.rating}")
        print(f"   📝 Description: {option.brief_description}")
        print(f"   📍 Proximity: {option.proximity_score}")
        print(f"   🚶 Convenience: {option.travel_convenience}")


async def test_mumbai_budget():
    """Test with Mumbai (low budget scenario)"""
    print_header("TESTING: Mumbai, India (Budget Travel)")
    
    # Create mock places for Mumbai
    mumbai_places = [
        Place(
            name="Gateway of India",
            location="South Mumbai, Apollo Bunder",
            significance="Historic monument built to commemorate King George V's visit",
            category="historical"
        ),
        Place(
            name="Marine Drive",
            location="South Mumbai",
            significance="Famous promenade known as Queen's Necklace",
            category="cultural"
        ),
        Place(
            name="Chhatrapati Shivaji Maharaj Terminus (CST)",
            location="South Mumbai, Fort",
            significance="UNESCO World Heritage railway station",
            category="historical"
        ),
        Place(
            name="Colaba Causeway",
            location="South Mumbai, Colaba",
            significance="Bustling commercial street for shopping",
            category="cultural"
        )
    ]
    
    mock_itinerary = ItineraryOutput(
        destination="Mumbai, India",
        duration_days=3,
        total_budget="25000 INR",  # Budget scenario
        accommodation_type=AccommodationType.BUDGET,
        must_visit_places=mumbai_places,
        daily_itineraries=[],
        total_estimated_cost="₹15,000-20,000",
        recommendations="Budget travel recommendations"
    )
    
    print(f"📊 Test Parameters:")
    print(f"   Total Budget: {mock_itinerary.total_budget}")
    print(f"   Expected Accommodation Budget: ₹10,000 (40%)")
    print(f"   Expected Per Night: ₹3,333")
    print(f"   Places: {len(mumbai_places)} activities in South Mumbai")
    
    # Test accommodation suggestions
    suggester = AccommodationSuggester()
    
    try:
        result = await suggester.suggest_accommodations(mock_itinerary)
        print_accommodation_results(result)
        
        # Validate results
        assert result.budget_category in ["low", "medium"], f"Unexpected budget category: {result.budget_category}"
        assert len(result.accommodation_options) >= 2, f"Expected at least 2 options, got {len(result.accommodation_options)}"
        assert result.duration_days == 3, f"Duration mismatch: {result.duration_days}"
        
        print("\n✅ Mumbai budget test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Mumbai budget test failed: {e}")
        return False


async def test_tokyo_luxury():
    """Test with Tokyo (high budget scenario)"""
    print_header("TESTING: Tokyo, Japan (Luxury Travel)")
    
    # Create mock places for Tokyo
    tokyo_places = [
        Place(
            name="Senso-ji Temple",
            location="Asakusa, Tokyo",
            significance="Ancient Buddhist temple in Tokyo's traditional district",
            category="historical"
        ),
        Place(
            name="Shibuya Crossing",
            location="Shibuya, Tokyo",
            significance="World's busiest pedestrian crossing",
            category="cultural"
        ),
        Place(
            name="Tokyo Tower",
            location="Minato, Tokyo",
            significance="Iconic communications tower with city views",
            category="entertainment"
        ),
        Place(
            name="Meiji Shrine",
            location="Shibuya, Tokyo",
            significance="Shinto shrine dedicated to Emperor Meiji",
            category="historical"
        )
    ]
    
    mock_itinerary = ItineraryOutput(
        destination="Tokyo, Japan",
        duration_days=5,
        total_budget="500000 JPY",  # High budget scenario
        accommodation_type=AccommodationType.LUXURY,
        must_visit_places=tokyo_places,
        daily_itineraries=[],
        total_estimated_cost="¥400,000-450,000",
        recommendations="Luxury travel recommendations"
    )
    
    print(f"📊 Test Parameters:")
    print(f"   Total Budget: {mock_itinerary.total_budget}")
    print(f"   Expected Accommodation Budget: ¥200,000 (40%)")
    print(f"   Expected Per Night: ¥40,000")
    print(f"   Places: {len(tokyo_places)} activities across Tokyo")
    
    # Test accommodation suggestions
    suggester = AccommodationSuggester()
    
    try:
        result = await suggester.suggest_accommodations(mock_itinerary)
        print_accommodation_results(result)
        
        # Validate results
        assert result.budget_category in ["medium", "high"], f"Unexpected budget category: {result.budget_category}"
        assert len(result.accommodation_options) >= 2, f"Expected at least 2 options, got {len(result.accommodation_options)}"
        assert result.duration_days == 5, f"Duration mismatch: {result.duration_days}"
        
        print("\n✅ Tokyo luxury test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Tokyo luxury test failed: {e}")
        return False


async def test_kerala_mid_range():
    """Test with Kerala (mid-range budget scenario)"""
    print_header("TESTING: Kerala, India (Mid-Range Travel)")
    
    # Create mock places for Kerala
    kerala_places = [
        Place(
            name="Munnar Tea Plantations",
            location="Munnar, Idukki District",
            significance="Scenic hill station with tea gardens",
            category="natural"
        ),
        Place(
            name="Alappuzha Backwaters",
            location="Alappuzha District",
            significance="Famous backwater network with houseboats",
            category="natural"
        ),
        Place(
            name="Fort Kochi",
            location="Kochi, Ernakulam District",
            significance="Historic port area with colonial architecture",
            category="historical"
        ),
        Place(
            name="Periyar National Park",
            location="Thekkady, Idukki District",
            significance="Wildlife sanctuary with elephant sightings",
            category="natural"
        )
    ]
    
    mock_itinerary = ItineraryOutput(
        destination="Kerala, India",
        duration_days=6,
        total_budget="75000 INR",  # Mid-range scenario
        accommodation_type=AccommodationType.MID_RANGE,
        must_visit_places=kerala_places,
        daily_itineraries=[],
        total_estimated_cost="₹60,000-70,000",
        recommendations="Mid-range travel recommendations"
    )
    
    print(f"📊 Test Parameters:")
    print(f"   Total Budget: {mock_itinerary.total_budget}")
    print(f"   Expected Accommodation Budget: ₹30,000 (40%)")
    print(f"   Expected Per Night: ₹5,000")
    print(f"   Places: {len(kerala_places)} activities across Kerala")
    
    # Test accommodation suggestions
    suggester = AccommodationSuggester()
    
    try:
        result = await suggester.suggest_accommodations(mock_itinerary)
        print_accommodation_results(result)
        
        # Validate results
        assert result.budget_category in ["low", "medium"], f"Unexpected budget category: {result.budget_category}"
        assert len(result.accommodation_options) >= 2, f"Expected at least 2 options, got {len(result.accommodation_options)}"
        assert result.duration_days == 6, f"Duration mismatch: {result.duration_days}"
        
        print("\n✅ Kerala mid-range test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Kerala mid-range test failed: {e}")
        return False


async def main():
    """Main test function"""
    print_header("AccommodationSuggester Agent - Phase 3 Testing")
    print("🚀 Testing location-aware accommodation suggestions")
    print("📡 Using Tavily SearchTool + Gemini 2.5 Pro")
    
    # Test different scenarios
    tests = [
        ("Mumbai Budget", test_mumbai_budget),
        ("Tokyo Luxury", test_tokyo_luxury),
        ("Kerala Mid-Range", test_kerala_mid_range)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print_header("Testing Complete")
    print(f"✅ Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! AccommodationSuggester is working perfectly!")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check the logs above.")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())
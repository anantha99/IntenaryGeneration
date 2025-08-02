"""
AccommodationSuggester Agent - Simple Location-Aware Implementation

This agent suggests 2-3 accommodation options based on:
- ItineraryOutput from ActivitiesPlanner (input)
- 40% budget allocation for accommodation
- Dynamic budget tier classification (low/medium/high) via web search
- Location intelligence: Hotels near top 4 activity areas
- Simple proximity focus without transport complexity

Uses Tavily SearchTool + Gemini 2.5 Pro for intelligent processing.
"""

import json
import logging
import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ActivitiesPlanner data structures for compatibility
from agents.activities_planner import ItineraryOutput, Place


@dataclass
class AccommodationOption:
    """Represents a hotel/accommodation option with location intelligence"""
    name: str
    location: str
    price_per_night: float
    total_cost: float  # price_per_night * duration
    rating: Optional[str] = None  # "4.2/5" or "3 stars"
    brief_description: Optional[str] = None
    proximity_score: Optional[str] = None  # "Near Gateway of India, Marine Drive"
    travel_convenience: Optional[str] = None  # "5 min walk to attractions"


@dataclass
class AccommodationOutput:
    """Complete accommodation suggestions with budget and location context"""
    destination: str
    duration_days: int
    budget_allocated: float  # 40% of total budget
    budget_category: str  # low, medium, high
    nightly_budget_range: str  # "₹2000-3000" or "$50-80"
    key_activity_areas: List[str]  # Top 4 activity areas
    accommodation_options: List[AccommodationOption]


class AccommodationSuggester:
    """
    Simple Location-Aware Accommodation Suggester Agent
    
    Takes ItineraryOutput and suggests hotels that are:
    1. Budget-appropriate (40% allocation, dynamic tier classification)
    2. Well-located (near top 4 activity areas)
    """
    
    def __init__(self):
        """Initialize with Tavily SearchTool and LLM agent"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize Tavily SearchTool (reuse ActivitiesPlanner pattern)
        self.search_tool = self._initialize_tavily_search()
        
        # Initialize LLM agent (reuse ActivitiesPlanner pattern)
        self._initialize_llm_agent()
        
        self.logger.info("AccommodationSuggester initialized with Tavily SearchTool and Gemini 2.5 Pro")

    def _initialize_tavily_search(self):
        """Initialize Tavily SearchTool via ADK's LangchainTool wrapper"""
        try:
            from google.adk.tools.langchain_tool import LangchainTool
            from langchain_tavily import TavilySearch
            
            if not os.getenv("TAVILY_API_KEY"):
                self.logger.warning("TAVILY_API_KEY environment variable not set.")
                return None
            
            # Create Tavily search instance optimized for accommodation research
            tavily_search = TavilySearch(
                max_results=8,  # More results for comprehensive hotel research
                search_depth="advanced",  # Advanced search for better quality
                include_answer=True,  # Get AI-generated answers
                include_raw_content=True,  # Get raw content for processing
                include_images=False,  # Not needed for accommodation data
            )
            
            # Wrap with ADK's LangchainTool
            adk_search_tool = LangchainTool(tool=tavily_search)
            
            self.logger.info("Tavily SearchTool initialized successfully for accommodation research")
            return adk_search_tool
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Tavily SearchTool: {e}")
            return None

    def _initialize_llm_agent(self):
        """Initialize LLM agent using the same pattern as ActivitiesPlanner"""
        try:
            # Use LiteLLM directly for OpenRouter integration
            import litellm
            self.litellm = litellm
            self.logger.info("LiteLLM initialized for Gemini 2.5 Pro via OpenRouter")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM agent: {e}")
            self.litellm = None

    async def suggest_accommodations(self, itinerary_output: ItineraryOutput) -> AccommodationOutput:
        """
        Main method: Suggest 2-3 accommodations based on budget and location
        
        Args:
            itinerary_output: Complete output from ActivitiesPlanner
            
        Returns:
            AccommodationOutput: Structured accommodation suggestions
        """
        try:
            self.logger.info(f"Starting accommodation suggestions for {itinerary_output.destination}")
            
            # Step 1: Extract and calculate budget information
            budget_info = self._extract_budget_info(itinerary_output)
            
            # Step 2: Analyze activity locations to identify key areas
            location_analysis = await self._analyze_activity_locations(itinerary_output)
            
            # Step 3: Research destination-specific budget categories
            budget_categories = await self._research_budget_categories(
                itinerary_output.destination, 
                budget_info["currency"],
                location_analysis["key_activity_areas"]
            )
            
            # Step 4: Classify user's budget into appropriate tier
            budget_tier = self._classify_budget_tier(
                budget_info["nightly_budget"], 
                budget_categories["budget_categories"]
            )
            
            # Step 5: Search for location-aware accommodations
            hotels = await self._search_hotels_by_location(
                itinerary_output.destination,
                budget_tier,
                budget_info["nightly_budget"],
                budget_info["currency"],
                budget_categories["budget_categories"],
                location_analysis["key_activity_areas"],
                itinerary_output.must_visit_places
            )
            
            # Step 6: Format final output
            return AccommodationOutput(
                destination=itinerary_output.destination,
                duration_days=itinerary_output.duration_days,
                budget_allocated=budget_info["accommodation_budget"],
                budget_category=budget_tier,
                nightly_budget_range=f"{budget_categories['budget_categories'][budget_tier]['min']}-{budget_categories['budget_categories'][budget_tier]['max']} {budget_info['currency']}",
                key_activity_areas=location_analysis["key_activity_areas"],
                accommodation_options=self._format_accommodation_options(hotels, itinerary_output.duration_days)
            )
            
        except Exception as e:
            self.logger.error(f"Error in accommodation suggestions: {e}")
            raise

    def _extract_budget_info(self, itinerary_output: ItineraryOutput) -> Dict:
        """Extract and calculate budget information from itinerary output"""
        try:
            # Parse total budget (e.g., "25000 INR" → 25000.0, "INR")
            budget_parts = itinerary_output.total_budget.split()
            total_budget = float(budget_parts[0])
            currency = budget_parts[1]
            
            # Calculate accommodation budget (40% allocation)
            accommodation_budget = total_budget * 0.4
            
            # Calculate per-night budget
            nightly_budget = accommodation_budget / itinerary_output.duration_days
            
            self.logger.info(f"Budget breakdown: Total={total_budget} {currency}, Accommodation={accommodation_budget} {currency}, Per night={nightly_budget:.0f} {currency}")
            
            return {
                "total_budget": total_budget,
                "currency": currency,
                "accommodation_budget": accommodation_budget,
                "nightly_budget": nightly_budget
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting budget info: {e}")
            raise ValueError(f"Invalid budget format in itinerary: {itinerary_output.total_budget}")

    async def _analyze_activity_locations(self, itinerary_output: ItineraryOutput) -> Dict:
        """Analyze activity locations to identify top 4 key areas for hotel placement"""
        try:
            self.logger.info(f"Analyzing activity locations for {len(itinerary_output.must_visit_places)} places")
            
            # Extract activity locations
            activity_locations = []
            for place in itinerary_output.must_visit_places:
                activity_locations.append({
                    "name": place.name,
                    "location": place.location
                })
            
            # Use LLM to analyze and identify key location clusters
            system_prompt = f"""
You are a location analyst for {itinerary_output.destination}.

PLANNED ACTIVITIES:
{json.dumps(activity_locations, indent=2)}

TASK: Analyze activity locations and identify the TOP 4 areas for optimal hotel placement.

ANALYZE:
1. Which areas/districts have the most activities?
2. Which locations are most central to multiple activities?
3. What are the key districts/neighborhoods for hotels?
4. Focus on areas that minimize travel time to multiple attractions

RESPOND with JSON:
{{
    "destination": "{itinerary_output.destination}",
    "key_activity_areas": ["Area 1", "Area 2", "Area 3", "Area 4"],
    "location_analysis": "Brief explanation of why these 4 areas are optimal for hotels"
}}

Focus on REAL area names from the activities and keep it to TOP 4 areas only.
"""
            
            if not self.litellm:
                # Fallback analysis without LLM
                return self._fallback_location_analysis(activity_locations, itinerary_output.destination)
            
            from config.model_used import get_model
            response = await self.litellm.acompletion(
                model=get_model("ACCOMMODATION_SUGGESTER"),
                messages=[{"role": "user", "content": system_prompt}],
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            
            response_content = response.choices[0].message.content
            
            # Clean up response content
            if response_content.startswith("```json"):
                response_content = response_content.replace("```json", "").replace("```", "").strip()
            elif response_content.startswith("```"):
                response_content = response_content.replace("```", "", 1).replace("```", "").strip()
            
            result = json.loads(response_content)
            
            # Ensure we have exactly 4 areas (top 4)
            if len(result["key_activity_areas"]) > 4:
                result["key_activity_areas"] = result["key_activity_areas"][:4]
            
            self.logger.info(f"Identified top 4 activity areas: {result['key_activity_areas']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing activity locations: {e}")
            return self._fallback_location_analysis(activity_locations, itinerary_output.destination)

    def _fallback_location_analysis(self, activity_locations: List[Dict], destination: str) -> Dict:
        """Fallback location analysis if LLM fails"""
        # Simple fallback: extract unique location areas
        areas = set()
        for location in activity_locations:
            # Simple parsing to extract area names
            loc_parts = location["location"].split(",")
            if len(loc_parts) >= 2:
                areas.add(loc_parts[-2].strip())  # Second to last part
            else:
                areas.add(location["location"].strip())
        
        key_areas = list(areas)[:4]  # Top 4
        
        return {
            "destination": destination,
            "key_activity_areas": key_areas,
            "location_analysis": "Fallback analysis: extracted areas from activity locations"
        }

    async def _research_budget_categories(self, destination: str, currency: str, 
                                        key_areas: List[str]) -> Dict:
        """Research destination-specific budget categories via web search"""
        try:
            self.logger.info(f"Researching budget categories for {destination} in {currency}")
            
            # Generate search queries for budget research
            areas_str = ", ".join(key_areas)
            search_queries = [
                f"hotel prices {destination} budget low medium luxury per night {currency}",
                f"accommodation cost {destination} {areas_str} cheap mid-range expensive {currency}",
                f"hotel rates {destination} budget categories {currency} nightly"
            ]
            
            # Execute searches and collect results
            all_results = []
            for query in search_queries:
                self.logger.info(f"Searching: {query}")
                result = await self._execute_search(query)
                if result:
                    all_results.extend(result)
            
            # Analyze results with LLM to determine budget categories
            system_prompt = f"""
You are researching hotel budget categories for {destination}.

FOCUS AREAS: {areas_str}
CURRENCY: {currency}

SEARCH RESULTS:
{json.dumps(all_results[:10], indent=2)}  # Top 10 results

TASK: Analyze search results to determine hotel budget tiers for {destination}.

Determine realistic price ranges for:
1. LOW budget hotels per night (basic, budget hotels)
2. MEDIUM budget hotels per night (mid-range, good quality)  
3. HIGH budget hotels per night (luxury, premium)

RESPOND with JSON:
{{
    "destination": "{destination}",
    "currency": "{currency}",
    "budget_categories": {{
        "low": {{"min": 20, "max": 60}},
        "medium": {{"min": 60, "max": 150}},
        "high": {{"min": 150, "max": 500}}
    }},
    "market_context": "Brief explanation of local hotel market"
}}

Use REAL market data from search results, not assumptions. Ensure ranges make sense for {destination}.
"""
            
            if not self.litellm:
                return self._fallback_budget_categories(destination, currency)
            
            from config.model_used import get_model
            response = await self.litellm.acompletion(
                model=get_model("ACCOMMODATION_SUGGESTER"),
                messages=[{"role": "user", "content": system_prompt}],
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            
            response_content = response.choices[0].message.content
            
            # Clean up response content
            if response_content.startswith("```json"):
                response_content = response_content.replace("```json", "").replace("```", "").strip()
            elif response_content.startswith("```"):
                response_content = response_content.replace("```", "", 1).replace("```", "").strip()
            
            result = json.loads(response_content)
            
            self.logger.info(f"Budget categories determined: {result['budget_categories']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error researching budget categories: {e}")
            return self._fallback_budget_categories(destination, currency)

    def _fallback_budget_categories(self, destination: str, currency: str) -> Dict:
        """Fallback budget categories if research fails"""
        # Simple fallback based on currency
        if currency == "INR":
            categories = {
                "low": {"min": 1500, "max": 3500},
                "medium": {"min": 3500, "max": 8000},
                "high": {"min": 8000, "max": 25000}
            }
        elif currency == "USD":
            categories = {
                "low": {"min": 25, "max": 75},
                "medium": {"min": 75, "max": 200},
                "high": {"min": 200, "max": 600}
            }
        else:
            # Generic fallback
            categories = {
                "low": {"min": 30, "max": 80},
                "medium": {"min": 80, "max": 200},
                "high": {"min": 200, "max": 500}
            }
        
        return {
            "destination": destination,
            "currency": currency,
            "budget_categories": categories,
            "market_context": f"Fallback budget categories for {destination}"
        }

    def _classify_budget_tier(self, nightly_budget: float, budget_categories: Dict) -> str:
        """Classify user's nightly budget into low/medium/high tier"""
        try:
            low_max = budget_categories["low"]["max"]
            medium_max = budget_categories["medium"]["max"]
            
            if nightly_budget <= low_max:
                tier = "low"
            elif nightly_budget <= medium_max:
                tier = "medium"
            else:
                tier = "high"
            
            self.logger.info(f"Budget {nightly_budget} classified as {tier} tier")
            return tier
            
        except Exception as e:
            self.logger.error(f"Error classifying budget tier: {e}")
            return "medium"  # Safe fallback

    async def _execute_search(self, query: str) -> List[Dict]:
        """Execute a single search query via Tavily"""
        try:
            # Use direct Tavily approach (same as ActivitiesPlanner)
            from tavily import TavilyClient
            
            client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=5
            )
            
            return response.get("results", [])
            
        except Exception as e:
            self.logger.error(f"Search execution error: {e}")
            return []

    async def _search_hotels_by_location(self, destination: str, budget_tier: str,
                                       nightly_budget: float, currency: str,
                                       budget_categories: Dict, key_areas: List[str],
                                       activity_places: List[Place]) -> List[Dict]:
        """Search for hotels matching budget tier and location requirements"""
        try:
            self.logger.info(f"Searching {budget_tier} hotels in {destination} near {key_areas}")
            
            # Generate location-aware search queries
            areas_str = ", ".join(key_areas)
            activity_names = [place.name for place in activity_places[:5]]  # Top 5 activities
            activities_str = ", ".join(activity_names)
            
            budget_range = budget_categories[budget_tier]
            
            search_queries = [
                f"{budget_tier} budget hotels {destination} {areas_str} near {activities_str} {currency}",
                f"best {budget_tier} accommodation {destination} {areas_str} {budget_range['min']}-{budget_range['max']} {currency}",
                f"{budget_tier} hotels {destination} walking distance {activities_str} per night {currency}"
            ]
            
            # Execute searches in parallel (like ActivitiesPlanner)
            import asyncio
            import time
            
            start_time = time.time()
            self.logger.info(f"🚀 Starting PARALLEL hotel search with {len(search_queries)} queries")
            
            # Create tasks for parallel execution
            search_tasks = [self._execute_search(query) for query in search_queries]
            
            # Execute all searches in parallel with error handling
            results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            elapsed_time = time.time() - start_time
            
            # Process results and handle any exceptions
            all_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Hotel search query {i+1} failed: {result}")
                elif isinstance(result, list) and result:
                    all_results.extend(result)
                    self.logger.info(f"✅ Query {i+1} returned {len(result)} results")
                else:
                    self.logger.info(f"⚠️  Query {i+1} returned no results")
            
            self.logger.info(f"🎉 PARALLEL hotel search completed in {elapsed_time:.2f}s! Total results: {len(all_results)}")
            
            # Use LLM to extract and format hotel options
            hotels = await self._extract_hotels_with_llm(
                destination, budget_tier, nightly_budget, currency,
                budget_range, key_areas, activity_names, all_results
            )
            
            return hotels
            
        except Exception as e:
            self.logger.error(f"Error in hotel search: {e}")
            return []

    async def _extract_hotels_with_llm(self, destination: str, budget_tier: str,
                                     nightly_budget: float, currency: str,
                                     budget_range: Dict, key_areas: List[str],
                                     activity_names: List[str], search_results: List[Dict]) -> List[Dict]:
        """Use LLM to extract and format hotel options from search results"""
        try:
            areas_str = ", ".join(key_areas)
            activities_str = ", ".join(activity_names)
            
            system_prompt = f"""
You are finding {budget_tier} budget hotels in {destination} with optimal location.

LOCATION REQUIREMENTS:
- Must be in or near: {areas_str}
- Should be close to: {activities_str}
- Focus on hotels that minimize travel time to planned activities

BUDGET CONTEXT:
- {budget_tier.upper()} tier hotels: {budget_range['min']}-{budget_range['max']} {currency}/night
- User's budget: {nightly_budget:.0f} {currency}/night
- Look for hotels around this budget range

SEARCH RESULTS:
{json.dumps(search_results[:15], indent=2)}

TASK: Extract 2-3 REAL hotels from search results that are BOTH budget-appropriate AND well-located.

REQUIREMENTS:
1. Hotels must be REAL (from search results only)
2. Hotels should cost around {nightly_budget:.0f} {currency}/night ({budget_tier} tier)
3. Hotels should be in {areas_str} areas
4. Hotels should be near multiple activities: {activities_str}
5. Include proximity and convenience information

OUTPUT JSON:
{{
    "hotels": [
        {{
            "name": "Real hotel name from search results",
            "location": "Specific area in {destination}",
            "price_per_night": {nightly_budget:.0f},
            "rating": "4.2/5 or 3 stars",
            "brief_description": "Brief description from search",
            "proximity_score": "Near Gateway of India, Marine Drive",
            "travel_convenience": "5 min walk to 3 attractions"
        }}
    ]
}}

IMPORTANT:
- Only use REAL hotel names from search results
- If no suitable hotels found, return empty hotels array
- Focus on location convenience for the planned activities
- Ensure pricing fits the {budget_tier} budget tier
"""
            
            if not self.litellm:
                return self._fallback_hotel_extraction(destination, budget_tier, nightly_budget, currency)
            
            from config.model_used import get_model
            response = await self.litellm.acompletion(
                model=get_model("ACCOMMODATION_SUGGESTER"),
                messages=[{"role": "user", "content": system_prompt}],
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
            
            response_content = response.choices[0].message.content
            
            # Clean up response content
            if response_content.startswith("```json"):
                response_content = response_content.replace("```json", "").replace("```", "").strip()
            elif response_content.startswith("```"):
                response_content = response_content.replace("```", "", 1).replace("```", "").strip()
            
            result = json.loads(response_content)
            hotels = result.get("hotels", [])
            
            self.logger.info(f"LLM extracted {len(hotels)} hotels from search results")
            return hotels
            
        except Exception as e:
            self.logger.error(f"Error extracting hotels with LLM: {e}")
            return self._fallback_hotel_extraction(destination, budget_tier, nightly_budget, currency)

    def _fallback_hotel_extraction(self, destination: str, budget_tier: str, 
                                 nightly_budget: float, currency: str) -> List[Dict]:
        """Fallback hotel data if LLM extraction fails"""
        return [
            {
                "name": f"Sample {budget_tier.title()} Hotel {destination}",
                "location": f"Central {destination}",
                "price_per_night": nightly_budget,
                "rating": "4.0/5",
                "brief_description": f"Quality {budget_tier} accommodation in {destination}",
                "proximity_score": "Near major attractions",
                "travel_convenience": "Walking distance to activities"
            }
        ]

    def _format_accommodation_options(self, hotels: List[Dict], duration: int) -> List[AccommodationOption]:
        """Format hotel results into AccommodationOption objects"""
        try:
            accommodation_options = []
            
            for hotel in hotels:
                # Extract data with safe defaults
                name = hotel.get("name", "Hotel Name")
                location = hotel.get("location", "City Center")
                price_per_night = float(hotel.get("price_per_night", 0))
                rating = hotel.get("rating", "4.0/5")
                description = hotel.get("brief_description", "Quality accommodation")
                proximity = hotel.get("proximity_score", "Near attractions")
                convenience = hotel.get("travel_convenience", "Convenient location")
                
                # Calculate total cost
                total_cost = price_per_night * duration
                
                # Create AccommodationOption object
                option = AccommodationOption(
                    name=name,
                    location=location,
                    price_per_night=price_per_night,
                    total_cost=total_cost,
                    rating=rating,
                    brief_description=description,
                    proximity_score=proximity,
                    travel_convenience=convenience
                )
                
                accommodation_options.append(option)
            
            self.logger.info(f"Formatted {len(accommodation_options)} accommodation options")
            return accommodation_options
            
        except Exception as e:
            self.logger.error(f"Error formatting accommodation options: {e}")
            return []


# Test function for CLI testing
async def test_accommodation_suggester():
    """Test function for AccommodationSuggester Phase 1 & 2"""
    from agents.activities_planner import ItineraryOutput, Place, DayItinerary, Activity
    from agents.request_parser import AccommodationType
    
    # Create mock ItineraryOutput (same format as ActivitiesPlanner output)
    mock_places = [
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
        )
    ]
    
    mock_itinerary = ItineraryOutput(
        destination="Mumbai, India",
        duration_days=3,
        total_budget="25000 INR",
        accommodation_type=AccommodationType.MID_RANGE,
        must_visit_places=mock_places,
        daily_itineraries=[],  # Empty for Phase 1 testing
        total_estimated_cost="₹10,000-15,000",
        recommendations="Sample recommendations"
    )
    
    # Test AccommodationSuggester
    suggester = AccommodationSuggester()
    
    try:
        # Test budget extraction
        budget_info = suggester._extract_budget_info(mock_itinerary)
        print("=== BUDGET EXTRACTION TEST ===")
        print(f"Total Budget: {budget_info['total_budget']} {budget_info['currency']}")
        print(f"Accommodation Budget (40%): {budget_info['accommodation_budget']} {budget_info['currency']}")
        print(f"Per Night Budget: {budget_info['nightly_budget']:.0f} {budget_info['currency']}")
        
        # Test location analysis
        location_analysis = await suggester._analyze_activity_locations(mock_itinerary)
        print("\n=== LOCATION ANALYSIS TEST ===")
        print(f"Key Activity Areas: {location_analysis['key_activity_areas']}")
        print(f"Analysis: {location_analysis['location_analysis']}")
        
        # Test budget research
        budget_categories = await suggester._research_budget_categories(
            mock_itinerary.destination, 
            budget_info["currency"],
            location_analysis["key_activity_areas"]
        )
        print("\n=== BUDGET RESEARCH TEST ===")
        print(f"Budget Categories: {budget_categories['budget_categories']}")
        print(f"Market Context: {budget_categories['market_context']}")
        
        # Test budget classification
        budget_tier = suggester._classify_budget_tier(
            budget_info["nightly_budget"], 
            budget_categories["budget_categories"]
        )
        print(f"\nUser Budget Tier: {budget_tier}")
        
        print("\n=== COMPLETE ACCOMMODATION SUGGESTION TEST ===")
        # Test complete flow
        result = await suggester.suggest_accommodations(mock_itinerary)
        
        print(f"Destination: {result.destination}")
        print(f"Duration: {result.duration_days} days")
        print(f"Budget Allocated: {result.budget_allocated} {budget_info['currency']}")
        print(f"Budget Category: {result.budget_category}")
        print(f"Nightly Budget Range: {result.nightly_budget_range}")
        print(f"Key Activity Areas: {result.key_activity_areas}")
        print(f"\nAccommodation Options ({len(result.accommodation_options)}):")
        
        for i, option in enumerate(result.accommodation_options, 1):
            print(f"\n{i}. {option.name}")
            print(f"   📍 Location: {option.location}")
            print(f"   💰 Price: {option.price_per_night} {budget_info['currency']}/night")
            print(f"   💵 Total Cost: {option.total_cost} {budget_info['currency']}")
            print(f"   ⭐ Rating: {option.rating}")
            print(f"   📝 Description: {option.brief_description}")
            print(f"   📍 Proximity: {option.proximity_score}")
            print(f"   🚶 Convenience: {option.travel_convenience}")
        
        print("\n✅ Phase 1 & 2 tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 test failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_accommodation_suggester())
#!/usr/bin/env python3
"""
Personalized Travel Itinerary Generator - CLI Interface

Features parallel execution of ActivitiesPlanner and AccommodationSuggester 
for ~40% faster processing time.

Usage:
    python src/generate_itinerary.py --request "Paris 5 days family $3000"
    python src/generate_itinerary.py --request "Tokyo 7 days couple" --interactive
    python src/generate_itinerary.py --request "London weekend" --format json --output itinerary.json
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from dataclasses import asdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.workflows import (
    TravelItineraryWorkflow, 
    TravelItineraryResponse,
    IncompleteRequestException
)


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    log_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def format_parallel_progress() -> str:
    """Show parallel execution progress in CLI"""
    return """
🚀 PARALLEL EXECUTION STARTED
├── 🏛️  ActivitiesPlanner: Researching destinations & planning itinerary...
└── 🏨 AccommodationSuggester: Searching hotels across multiple platforms...

⏱️  Expected completion: ~15-20 seconds
"""


def format_results_summary(result: TravelItineraryResponse) -> str:
    """Format final results for CLI display"""
    success_icon = "✅" if result.success else "⚠️"
    
    # Handle None values safely
    itinerary = result.itinerary or type('obj', (object,), {
        'must_visit_places': [],
        'daily_itineraries': [],
        'total_estimated_cost': 'N/A'
    })()
    
    accommodations = result.accommodations or type('obj', (object,), {
        'accommodation_suggestions': [],
        'children_count': 0
    })()
    
    request_summary = result.request_summary or {}
    
    return f"""
{'='*60}
🎉 ITINERARY GENERATION COMPLETE
{'='*60}

📊 Performance Summary:
   Total Processing Time: {result.processing_time:.2f} seconds
   Workflow ID: {result.workflow_id}
   Success: {success_icon} {'Yes' if result.success else 'Partial'}
   {'Partial Results: Some components failed' if result.partial_results else ''}

🎯 Trip Summary:
   Destination: {request_summary.get('destination', 'N/A')}
   Duration: {request_summary.get('duration', 'N/A')} days
   Travelers: {request_summary.get('travelers', {}).get('total', 'N/A') if request_summary.get('travelers') else 'N/A'} total
   Budget: {request_summary.get('budget', {}).get('total_amount', 'N/A') if request_summary.get('budget') else 'N/A'} {request_summary.get('budget', {}).get('currency', '') if request_summary.get('budget') else ''}

🏛️  Activities & Itinerary:
   Must-visit places: {len(itinerary.must_visit_places)}
   Daily itineraries: {len(itinerary.daily_itineraries)} days planned
   Estimated cost: {itinerary.total_estimated_cost}

🏨 Accommodation Options:
   Suggestions found: {len(accommodations.accommodation_suggestions)}
   Family-friendly: {'Yes' if accommodations.children_count > 0 else 'Not applicable'}

💰 Total Estimated Cost: {result.final_cost_estimate or 'Unable to estimate'}

{f"⚠️ Errors encountered: {'; '.join(result.errors)}" if result.errors else ""}
"""


def format_detailed_markdown(result: TravelItineraryResponse) -> str:
    """Format detailed markdown output"""
    # Handle None values safely
    itinerary = result.itinerary
    accommodations = result.accommodations
    request_summary = result.request_summary or {}
    
    md = f"""# Travel Itinerary - {request_summary.get('destination', 'Unknown Destination')}

**Generated on**: {result.generated_at}  
**Processing time**: {result.processing_time:.2f} seconds  
**Workflow ID**: {result.workflow_id}

## Trip Overview

- **Destination**: {request_summary.get('destination', 'N/A')}
- **Duration**: {request_summary.get('duration', 'N/A')} days
- **Travelers**: {request_summary.get('travelers', {}).get('total', 'N/A') if request_summary.get('travelers') else 'N/A'} total
- **Budget**: {request_summary.get('budget', {}).get('total_amount', 'N/A') if request_summary.get('budget') else 'N/A'} {request_summary.get('budget', {}).get('currency', '') if request_summary.get('budget') else ''}
- **Estimated Total Cost**: {result.final_cost_estimate or 'Unable to estimate'}

"""

    # Add itinerary details if available
    if itinerary and itinerary.must_visit_places:
        md += "\n## Must-Visit Places\n\n"
        for i, place in enumerate(itinerary.must_visit_places, 1):
            md += f"### {i}. {place.name}\n"
            md += f"**Location**: {place.location}  \n"
            md += f"**Category**: {place.category}  \n"
            md += f"**Significance**: {place.significance}\n\n"
    
    # Add daily itinerary if available
    if itinerary and itinerary.daily_itineraries:
        md += "\n## Daily Itinerary\n\n"
        for day in itinerary.daily_itineraries:
            md += f"### Day {day.day_number}\n\n"
            if day.activities:
                for activity in day.activities:
                    md += f"- **{activity.name}** at {activity.place} ({activity.duration})\n"
                    md += f"  {activity.description}\n"
                    if activity.cost_estimate:
                        md += f"  *Cost: {activity.cost_estimate}*\n"
                    md += "\n"
    
    # Add accommodation suggestions if available
    if accommodations and accommodations.accommodation_suggestions:
        md += "\n## Accommodation Suggestions\n\n"
        for i, acc in enumerate(accommodations.accommodation_suggestions, 1):
            md += f"### {i}. {acc.name}\n"
            md += f"**Location**: {acc.location}  \n"
            md += f"**Price Range**: {acc.price_range}  \n"
            md += f"**Rating**: {acc.rating}/5  \n"
            md += f"**Type**: {acc.accommodation_type}  \n"
            md += f"**Family-friendly**: {'Yes' if acc.family_friendly else 'No'}  \n"
            md += f"**Amenities**: {', '.join(acc.amenities)}  \n"
            md += f"**Description**: {acc.description}\n\n"
    
    # Add errors if any
    if result.errors:
        md += "\n## Errors Encountered\n\n"
        for error in result.errors:
            md += f"- {error}\n"
    
    return md


async def main():
    parser = argparse.ArgumentParser(
        description="Generate personalized travel itinerary (with parallel processing)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --request "Paris 5 days family $3000"
  %(prog)s --request "Tokyo 7 days couple" --interactive --verbose
  %(prog)s --request "London weekend" --format json --output itinerary.json
        """
    )
    
    parser.add_argument(
        "--request", "-r", 
        required=True,
        help="Travel request: 'I want to visit Paris for 5 days with my family, budget $3000'"
    )
    parser.add_argument(
        "--output", "-o", 
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--format", 
        choices=["json", "markdown", "summary"], 
        default="summary",
        help="Output format (default: summary)"
    )
    parser.add_argument(
        "--interactive", "-i", 
        action="store_true",
        help="Enable interactive mode for missing information"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Show detailed parallel execution progress"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Create workflow
    workflow = TravelItineraryWorkflow(
        interactive=args.interactive, 
        verbose=args.verbose
    )
    
    # Print header
    print("🌍 Personalized Travel Itinerary Generator")
    print("🚀 Featuring parallel agent execution for faster results!")
    
    if args.verbose:
        print(format_parallel_progress())
    
    try:
        # Generate itinerary
        start_time = time.time()
        result = await workflow.generate_itinerary(args.request)
        
        # Format output
        if args.format == "json":
            output = json.dumps(asdict(result), indent=2, default=str)
        elif args.format == "markdown":
            output = format_detailed_markdown(result)
        else:  # summary
            output = format_results_summary(result)
        
        # Save or display output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\n✅ Itinerary saved to {args.output}")
        else:
            print(output)
        
        # Performance feedback
        if result.processing_time < 20:
            print(f"\n⚡ Fast execution! Completed in {result.processing_time:.2f}s thanks to parallel processing")
        elif result.processing_time < 30:
            print(f"\n✅ Good performance! Completed in {result.processing_time:.2f}s")
        else:
            print(f"\n⏰ Completed in {result.processing_time:.2f}s")
        
        return 0 if result.success else 1
        
    except IncompleteRequestException as e:
        print(f"\n❌ More information needed: {e.next_question}")
        print("💡 Use --interactive flag for conversational mode")
        return 1
    except KeyboardInterrupt:
        print("\n⏹️ Generation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Failed to generate itinerary: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted")
        sys.exit(1)
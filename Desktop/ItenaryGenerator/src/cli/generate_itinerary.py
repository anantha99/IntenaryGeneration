#!/usr/bin/env python3
"""
Enhanced CLI for Travel Itinerary Generator

Features beautiful progress bar, interactive input, and multiple output formats.
Sequential workflow: RequestParser → ActivitiesPlanner → AccommodationSuggester
"""

import asyncio
import argparse
import json
import logging
import sys
import os
from typing import Optional
from datetime import datetime

# Rich imports for beautiful terminal UI
from rich.console import Console
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn
)
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.layout import Layout

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workflows.travel_itinerary_workflow import generate_travel_itinerary
from workflows.data_models import TravelItineraryResponse, WorkflowMetadata, AgentStatus

# Initialize console
console = Console()

# Global progress tracking
current_progress = None
current_live = None


class ProgressTracker:
    """Manages progress display with Rich progress bar"""
    
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            expand=True
        )
        self.main_task = None
        self.current_stage = ""
        self.live = None
    
    def start(self):
        """Start the progress display"""
        self.main_task = self.progress.add_task("🏃 Generating Your Travel Itinerary...", total=100)
        self.live = Live(self.progress, console=console, refresh_per_second=4)
        self.live.start()
    
    def update(self, message: str, percentage: float, metadata: Optional[WorkflowMetadata] = None):
        """Update progress with new message and percentage"""
        if self.main_task is not None:
            self.progress.update(self.main_task, completed=percentage, description=f"🏃 {message}")
        
        # Add stage information if metadata available
        if metadata:
            stage_info = self._get_stage_info(metadata)
            if stage_info != self.current_stage:
                self.current_stage = stage_info
                console.print(f"[dim]{stage_info}[/dim]")
    
    def _get_stage_info(self, metadata: WorkflowMetadata) -> str:
        """Get current stage information"""
        current_agent = metadata.get_current_agent()
        if current_agent:
            return f"[{metadata.current_stage.value}] {current_agent.agent_name} running..."
        return f"[{metadata.current_stage.value}]"
    
    def stop(self):
        """Stop the progress display"""
        if self.live:
            self.live.stop()


def progress_callback(message: str, percentage: float, metadata: Optional[WorkflowMetadata] = None):
    """Callback function for workflow progress updates"""
    global current_progress
    if current_progress:
        current_progress.update(message, percentage, metadata)


def print_header():
    """Print beautiful header"""
    header = Panel.fit(
        "[bold blue]🌍 Travel Itinerary Generator[/bold blue]\n"
        "[dim]AI-powered travel planning with location-aware recommendations[/dim]",
        border_style="blue"
    )
    console.print(header)
    console.print()


def get_user_input_interactive() -> str:
    """Get user input interactively"""
    console.print("[bold green]Let's plan your perfect trip! 🚀[/bold green]")
    console.print("[dim]Describe your travel request in natural language...[/dim]")
    console.print()
    
    user_input = Prompt.ask(
        "[yellow]Your travel request[/yellow]",
        default="I want to visit Mumbai for 3 days with a budget of 25000 INR"
    )
    
    console.print()
    return user_input


def format_summary_output(response: TravelItineraryResponse) -> str:
    """Format summary output for display"""
    lines = []
    
    # Header
    lines.append("🎯 TRAVEL ITINERARY SUMMARY")
    lines.append("=" * 50)
    lines.append("")
    
    # Basic info
    if response.parsed_request:
        lines.append(f"✈️  Destination: {response.parsed_request.destination}")
        lines.append(f"📅 Duration: {response.parsed_request.duration} days")
        lines.append(f"💰 Budget: {response.parsed_request.budget.total_amount}")
        travelers_text = f"👥 Travelers: {response.parsed_request.travelers.adults} adults"
        if response.parsed_request.travelers.children > 0:
            travelers_text += f", {response.parsed_request.travelers.children} children"
        lines.append(travelers_text)
        lines.append("")
    
    # Activities
    if response.itinerary:
        lines.append(f"🗺️  ACTIVITIES ({len(response.itinerary.must_visit_places)} places)")
        lines.append("-" * 30)
        for i, place in enumerate(response.itinerary.must_visit_places[:5], 1):
            lines.append(f"{i}. {place.name} - {place.significance}")
        if len(response.itinerary.must_visit_places) > 5:
            lines.append(f"   ... and {len(response.itinerary.must_visit_places) - 5} more places")
        lines.append("")
    
    # Accommodations
    if response.accommodations:
        lines.append(f"🏨 ACCOMMODATIONS ({len(response.accommodations.accommodation_options)} options)")
        lines.append("-" * 30)
        for i, hotel in enumerate(response.accommodations.accommodation_options, 1):
            lines.append(f"{i}. {hotel.name} - {hotel.location}")
            lines.append(f"   💰 {hotel.price_per_night}/night, Total: {hotel.total_cost}")
            lines.append(f"   ⭐ {hotel.rating} - {hotel.brief_description}")
        lines.append("")
    
    # Status and timing
    lines.append("📊 STATUS")
    lines.append("-" * 30)
    lines.append(f"Status: {response.get_completion_status()}")
    if response.workflow_metadata:
        lines.append(f"Generated in: {response.workflow_metadata.total_duration:.1f}s")
        if response.workflow_metadata.has_errors():
            lines.append("⚠️  Warnings/Errors:")
            for error in response.get_error_summary()[:3]:
                lines.append(f"   • {error}")
    
    return "\n".join(lines)


def format_detailed_output(response: TravelItineraryResponse) -> str:
    """Format detailed output for display"""
    lines = []
    
    lines.append("🌍 DETAILED TRAVEL ITINERARY")
    lines.append("=" * 60)
    lines.append("")
    
    # Parsed Request Details
    if response.parsed_request:
        lines.append("📋 TRAVEL REQUEST DETAILS")
        lines.append("-" * 40)
        lines.append(f"Destination: {response.parsed_request.destination}")
        lines.append(f"Duration: {response.parsed_request.duration} days")
        lines.append(f"Budget: {response.parsed_request.budget.total_amount}")
        lines.append(f"Travelers: {response.parsed_request.travelers.adults} adults, {response.parsed_request.travelers.children} children")
        lines.append(f"Accommodation Type: {response.parsed_request.accommodation_type.value}")
        lines.append("")
    
    # Detailed Itinerary
    if response.itinerary:
        lines.append("🗺️  DETAILED ITINERARY")
        lines.append("-" * 40)
        lines.append(f"Must-Visit Places ({len(response.itinerary.must_visit_places)}):")
        for i, place in enumerate(response.itinerary.must_visit_places, 1):
            lines.append(f"\n{i}. {place.name}")
            lines.append(f"   📍 Location: {place.location}")
            lines.append(f"   ℹ️  Significance: {place.significance}")
            lines.append(f"   🏷️  Category: {place.category}")
        
        if response.itinerary.daily_itineraries:
            lines.append(f"\nDaily Itineraries ({len(response.itinerary.daily_itineraries)} days):")
            for day in response.itinerary.daily_itineraries:
                lines.append(f"\n📅 Day {day.day}")
                lines.append(f"Theme: {day.theme}")
                lines.append(f"Activities ({len(day.activities)}):")
                for activity in day.activities:
                    lines.append(f"  • {activity.name} at {activity.location}")
                    if activity.description:
                        lines.append(f"    {activity.description}")
        
        lines.append(f"\n💰 Estimated Cost: {response.itinerary.total_estimated_cost}")
        lines.append(f"📝 Recommendations: {response.itinerary.recommendations}")
        lines.append("")
    
    # Detailed Accommodations
    if response.accommodations:
        lines.append("🏨 ACCOMMODATION DETAILS")
        lines.append("-" * 40)
        lines.append(f"Budget Category: {response.accommodations.budget_category}")
        lines.append(f"Nightly Budget Range: {response.accommodations.nightly_budget_range}")
        lines.append(f"Key Activity Areas: {', '.join(response.accommodations.key_activity_areas)}")
        lines.append(f"\nAccommodation Options ({len(response.accommodations.accommodation_options)}):")
        
        for i, hotel in enumerate(response.accommodations.accommodation_options, 1):
            lines.append(f"\n{i}. {hotel.name}")
            lines.append(f"   📍 Location: {hotel.location}")
            lines.append(f"   💰 Price: {hotel.price_per_night}/night")
            lines.append(f"   💵 Total Cost: {hotel.total_cost}")
            lines.append(f"   ⭐ Rating: {hotel.rating}")
            lines.append(f"   📝 Description: {hotel.brief_description}")
            lines.append(f"   📍 Proximity: {hotel.proximity_score}")
            lines.append(f"   🚶 Convenience: {hotel.travel_convenience}")
        lines.append("")
    
    # Workflow Metadata
    if response.workflow_metadata:
        lines.append("📊 EXECUTION METADATA")
        lines.append("-" * 40)
        lines.append(f"Workflow ID: {response.workflow_metadata.workflow_id}")
        lines.append(f"Total Duration: {response.workflow_metadata.total_duration:.1f}s")
        lines.append(f"Overall Status: {response.workflow_metadata.overall_status}")
        lines.append(f"Completion: {response.workflow_metadata.get_completion_percentage():.1f}%")
        
        # Agent details
        agents = [
            response.workflow_metadata.request_parser,
            response.workflow_metadata.activities_planner,
            response.workflow_metadata.accommodation_suggester
        ]
        
        lines.append("\nAgent Execution Details:")
        for agent in agents:
            status_icon = "✅" if agent.status == AgentStatus.COMPLETED else "❌" if agent.status == AgentStatus.FAILED else "⏸️"
            lines.append(f"  {status_icon} {agent.agent_name}: {agent.status.value}")
            if agent.duration:
                lines.append(f"     Duration: {agent.duration:.1f}s")
            if agent.retry_count > 0:
                lines.append(f"     Retries: {agent.retry_count}")
            if agent.error_message:
                lines.append(f"     Error: {agent.error_message}")
        
        if response.workflow_metadata.errors:
            lines.append(f"\nErrors ({len(response.workflow_metadata.errors)}):")
            for error in response.workflow_metadata.errors:
                lines.append(f"  • {error}")
    
    return "\n".join(lines)


def format_json_output(response: TravelItineraryResponse) -> str:
    """Format JSON output"""
    try:
        # Convert response to dictionary (simplified)
        data = {
            "user_input": response.user_input,
            "completion_status": response.get_completion_status(),
            "is_complete": response.is_complete(),
            "summary": response.summary
        }
        
        if response.parsed_request:
            data["parsed_request"] = {
                "destination": response.parsed_request.destination,
                "duration": response.parsed_request.duration,
                "budget": response.parsed_request.budget.total_amount,
                "travelers": {
                    "adults": response.parsed_request.travelers.adults,
                    "children": response.parsed_request.travelers.children
                },
                "accommodation_type": response.parsed_request.accommodation_type.value
            }
        
        if response.itinerary:
            data["itinerary"] = {
                "destination": response.itinerary.destination,
                "duration_days": response.itinerary.duration_days,
                "total_budget": response.itinerary.total_budget,
                "must_visit_places": [
                    {
                        "name": place.name,
                        "location": place.location,
                        "significance": place.significance,
                        "category": place.category
                    } for place in response.itinerary.must_visit_places
                ],
                "total_estimated_cost": response.itinerary.total_estimated_cost,
                "recommendations": response.itinerary.recommendations
            }
        
        if response.accommodations:
            data["accommodations"] = {
                "destination": response.accommodations.destination,
                "budget_category": response.accommodations.budget_category,
                "nightly_budget_range": response.accommodations.nightly_budget_range,
                "key_activity_areas": response.accommodations.key_activity_areas,
                "accommodation_options": [
                    {
                        "name": hotel.name,
                        "location": hotel.location,
                        "price_per_night": hotel.price_per_night,
                        "total_cost": hotel.total_cost,
                        "rating": hotel.rating,
                        "brief_description": hotel.brief_description,
                        "proximity_score": hotel.proximity_score,
                        "travel_convenience": hotel.travel_convenience
                    } for hotel in response.accommodations.accommodation_options
                ]
            }
        
        if response.workflow_metadata:
            data["workflow_metadata"] = {
                "workflow_id": response.workflow_metadata.workflow_id,
                "total_duration": response.workflow_metadata.total_duration,
                "overall_status": response.workflow_metadata.overall_status,
                "completion_percentage": response.workflow_metadata.get_completion_percentage(),
                "errors": response.workflow_metadata.errors
            }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
        
    except Exception as e:
        return f'{{"error": "Failed to serialize response: {str(e)}"}}'


def format_markdown_output(response: TravelItineraryResponse) -> str:
    """Format Markdown output for file export"""
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines.append("# Travel Itinerary")
    lines.append(f"*Generated on {timestamp}*")
    lines.append("")
    
    # Basic Info
    if response.parsed_request:
        lines.append("## Travel Details")
        lines.append(f"- **Destination:** {response.parsed_request.destination}")
        lines.append(f"- **Duration:** {response.parsed_request.duration} days")
        lines.append(f"- **Budget:** {response.parsed_request.budget.total_amount}")
        travelers_text = f"- **Travelers:** {response.parsed_request.travelers.adults} adults"
        if response.parsed_request.travelers.children > 0:
            travelers_text += f", {response.parsed_request.travelers.children} children"
        lines.append(travelers_text)
        lines.append("")
    
    # Activities
    if response.itinerary:
        lines.append("## Must-Visit Places")
        for i, place in enumerate(response.itinerary.must_visit_places, 1):
            lines.append(f"### {i}. {place.name}")
            lines.append(f"**Location:** {place.location}")
            lines.append(f"**Significance:** {place.significance}")
            lines.append(f"**Category:** {place.category}")
            lines.append("")
    
    # Accommodations
    if response.accommodations:
        lines.append("## Accommodation Options")
        for i, hotel in enumerate(response.accommodations.accommodation_options, 1):
            lines.append(f"### {i}. {hotel.name}")
            lines.append(f"- **Location:** {hotel.location}")
            lines.append(f"- **Price:** {hotel.price_per_night}/night")
            lines.append(f"- **Total Cost:** {hotel.total_cost}")
            lines.append(f"- **Rating:** {hotel.rating}")
            lines.append(f"- **Description:** {hotel.brief_description}")
            lines.append(f"- **Proximity:** {hotel.proximity_score}")
            lines.append("")
    
    # Status
    lines.append("## Generation Status")
    lines.append(f"- **Status:** {response.get_completion_status()}")
    if response.workflow_metadata:
        lines.append(f"- **Generation Time:** {response.workflow_metadata.total_duration:.1f} seconds")
    
    return "\n".join(lines)


def format_primary_output(response: TravelItineraryResponse) -> str:
    """Format primary schema output - structured format with core travel elements"""
    lines = []
    
    # Header with schema identifier
    lines.append("🏛️ PRIMARY TRAVEL SCHEMA")
    lines.append("=" * 60)
    lines.append("")
    
    # Core Schema Elements
    lines.append("📋 STRUCTURED TRAVEL INFORMATION")
    lines.append("-" * 40)
    lines.append("")
    
    # 1. DESTINATION
    if response.parsed_request:
        lines.append("🌍 DESTINATION")
        lines.append(f"   Location: {response.parsed_request.destination}")
        lines.append(f"   Travel Type: International/Domestic Travel")
        lines.append("")
        
        # 2. DURATION
        lines.append("⏰ DURATION")
        lines.append(f"   Trip Length: {response.parsed_request.duration} days")
        travelers_text = f"   Travelers: {response.parsed_request.travelers.adults} adults"
        if response.parsed_request.travelers.children > 0:
            travelers_text += f", {response.parsed_request.travelers.children} children"
        lines.append(travelers_text)
        lines.append(f"   Budget: {response.parsed_request.budget.total_amount}")
        lines.append("")
    
    # 3. ACTIVITIES (with significance)
    if response.itinerary and response.itinerary.must_visit_places:
        lines.append("🎯 ACTIVITIES & ATTRACTIONS")
        lines.append("   Key Places to Visit:")
        lines.append("")
        
        for i, place in enumerate(response.itinerary.must_visit_places, 1):
            lines.append(f"   {i}. {place.name}")
            lines.append(f"      📍 Location: {place.location}")
            lines.append(f"      🏛️ Category: {place.category}")
            lines.append(f"      ⭐ Significance: {place.significance}")
            if hasattr(place, 'estimated_duration') and place.estimated_duration:
                lines.append(f"      ⏱️ Duration: {place.estimated_duration}")
            lines.append("")
        
        # Activity Summary
        total_places = len(response.itinerary.must_visit_places)
        categories = list(set(place.category for place in response.itinerary.must_visit_places))
        lines.append(f"   📊 Activity Summary: {total_places} places across {len(categories)} categories")
        lines.append(f"   📂 Categories: {', '.join(categories)}")
        lines.append("")
    
    # 4. ACCOMMODATIONS
    if response.accommodations and response.accommodations.accommodation_options:
        lines.append("🏨 ACCOMMODATIONS")
        lines.append("   Recommended Hotels:")
        lines.append("")
        
        for i, hotel in enumerate(response.accommodations.accommodation_options, 1):
            lines.append(f"   {i}. {hotel.name}")
            lines.append(f"      📍 Location: {hotel.location}")
            lines.append(f"      💰 Price: ₹{hotel.price_per_night:,.0f}/night")
            lines.append(f"      💳 Total Cost: ₹{hotel.total_cost:,.0f}")
            lines.append(f"      ⭐ Rating: {hotel.rating}")
            lines.append(f"      🎯 Proximity: {hotel.proximity_score} (to attractions)")
            if hotel.brief_description:
                # Truncate description for primary schema
                desc = hotel.brief_description[:100] + "..." if len(hotel.brief_description) > 100 else hotel.brief_description
                lines.append(f"      📝 Description: {desc}")
            lines.append("")
        
        # Accommodation Summary
        total_hotels = len(response.accommodations.accommodation_options)
        # Calculate average price - price_per_night is already a float
        prices = [hotel.price_per_night for hotel in response.accommodations.accommodation_options if hotel.price_per_night > 0]
        avg_price = sum(prices) / len(prices) if prices else 0
        lines.append(f"   📊 Accommodation Summary: {total_hotels} options available")
        if avg_price > 0:
            lines.append(f"   💰 Average Price: ₹{avg_price:.0f}/night")
        lines.append("")
    
    # SCHEMA METADATA
    lines.append("🔍 SCHEMA METADATA")
    lines.append("-" * 20)
    if response.workflow_metadata:
        lines.append(f"   Generation Time: {response.workflow_metadata.total_duration:.1f} seconds")
        lines.append(f"   Generation Status: {response.get_completion_status()}")
        
        # Agent execution breakdown
        lines.append("   Agent Performance:")
        agents = [
            response.workflow_metadata.request_parser,
            response.workflow_metadata.activities_planner,
            response.workflow_metadata.accommodation_suggester
        ]
        for agent in agents:
            if agent.duration:
                lines.append(f"   - {agent.agent_name}: {agent.duration:.1f}s ({agent.status})")
    
    lines.append("")
    lines.append("✅ Primary schema generation complete")
    lines.append("=" * 60)
    
    return "\n".join(lines)


async def main():
    """Main CLI function"""
    global current_progress
    
    parser = argparse.ArgumentParser(
        description="Generate AI-powered travel itineraries with beautiful progress tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_itinerary.py                           # Interactive mode
  python generate_itinerary.py "Visit Tokyo for 5 days" # Direct input
  python generate_itinerary.py --format json            # JSON output
  python generate_itinerary.py --output travel.md       # Save to file
        """
    )
    
    parser.add_argument("input", nargs="?", help="Travel request (if not provided, interactive mode)")
    parser.add_argument("--format", choices=["summary", "detailed", "json", "markdown", "primary"], 
                       default="summary", help="Output format (default: summary)")
    parser.add_argument("--output", "-o", help="Save output to file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (no progress bar)")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    try:
        # Print header
        if not args.quiet:
            print_header()
        
        # Get user input
        if args.input:
            user_input = args.input
            if not args.quiet:
                console.print(f"[yellow]Processing request:[/yellow] {user_input}")
                console.print()
        else:
            user_input = get_user_input_interactive()
        
        # Initialize progress tracker
        if not args.quiet:
            current_progress = ProgressTracker()
            current_progress.start()
        
        # Execute workflow
        try:
            response = await generate_travel_itinerary(user_input, progress_callback if not args.quiet else None)
        finally:
            if current_progress:
                current_progress.stop()
                current_progress = None
        
        # Format output
        if args.format == "summary":
            output = format_summary_output(response)
        elif args.format == "detailed":
            output = format_detailed_output(response)
        elif args.format == "json":
            output = format_json_output(response)
        elif args.format == "markdown":
            output = format_markdown_output(response)
        elif args.format == "primary":
            output = format_primary_output(response)
        
        # Display or save output
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            console.print(f"\n[green]✅ Itinerary saved to {args.output}[/green]")
        else:
            console.print("\n" + "="*60)
            console.print(output)
        
        # Display completion status
        if not args.quiet:
            if response.is_complete():
                console.print(f"\n[bold green]🎉 Complete itinerary generated successfully![/bold green]")
            elif response.is_partial():
                console.print(f"\n[yellow]⚠️  Partial results generated. Some agents encountered issues.[/yellow]")
            else:
                console.print(f"\n[red]❌ Failed to generate itinerary. Check logs for details.[/red]")
        
    except KeyboardInterrupt:
        if current_progress:
            current_progress.stop()
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        if current_progress:
            current_progress.stop()
        console.print(f"\n[red]❌ Unexpected error: {str(e)}[/red]")
        if args.verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
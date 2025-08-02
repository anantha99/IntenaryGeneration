#!/usr/bin/env python3
"""
Interactive Travel Itinerary Generator

This script provides an interactive interface for the TravelItineraryWorkflow
that displays rich terminal output similar to the primary format command.
"""

import asyncio
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
from typing import Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workflows import TravelItineraryWorkflow, TravelItineraryResponse
from workflows.data_models import WorkflowMetadata, AgentStatus
from agents.request_parser import RequestParserAgent

console = Console()

def format_primary_schema(response: TravelItineraryResponse) -> str:
    """Format the response in primary schema format"""
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
        # Calculate average price
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
        
        # Agent Performance
        lines.append("   Agent Performance:")
        for agent in [response.workflow_metadata.request_parser, 
                     response.workflow_metadata.activities_planner, 
                     response.workflow_metadata.accommodation_suggester]:
            if agent.duration:
                lines.append(f"   - {agent.agent_name}: {agent.duration:.1f}s ({agent.status.value})")
    
    lines.append("")
    lines.append("✅ Primary schema generation complete")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def progress_callback(message: str, percentage: float, metadata=None):
    """Callback function for workflow progress updates"""
    # Show progress with loading indicators
    if "parsing" in message.lower():
        console.print(f"[blue]🔍 {message}[/blue]")
    elif "finding" in message.lower() or "planning" in message.lower():
        console.print(f"[green]🗺️ {message}[/green]")
    elif "accommodation" in message.lower() or "hotel" in message.lower():
        console.print(f"[yellow]🏨 {message}[/yellow]")
    elif "assembling" in message.lower() or "final" in message.lower():
        console.print(f"[magenta]📋 {message}[/magenta]")
    else:
        console.print(f"[cyan]🔄 {message}[/cyan]")

async def parse_request_interactively(user_input: str) -> dict:
    """Parse the user request using the RequestParserAgent interactively"""
    parser_agent = RequestParserAgent()
    
    console.print("[green]🔍 Parsing your travel request...[/green]")
    
    try:
        # Start the conversation
        response = await parser_agent.start_conversation(user_input)
        
        # If the conversation is complete, get the final request
        if response.get("is_complete"):
            final_request = parser_agent.get_final_request()
            console.print("[green]✅ Request parsed successfully![/green]")
            return final_request
        
        # If not complete, continue the conversation
        while not response.get("is_complete", False):
            if response.get("next_question"):
                console.print(f"[blue]🤖 {response['next_question']}[/blue]")
            elif response.get("parse_error"):
                console.print(f"[red]❌ Error: {response['parse_error']}[/red]")
            
            # Get user response
            user_response = Prompt.ask("\n[bold]Your response[/bold]")
            
            # Continue conversation
            response = await parser_agent.continue_conversation(user_response)
        
        # Get final request
        final_request = parser_agent.get_final_request()
        console.print("[green]✅ Request parsing completed![/green]")
        return final_request
        
    except Exception as e:
        console.print(f"[red]❌ Error parsing request: {str(e)}[/red]")
        # Return a basic parsed request based on user input
        return {
            "destination": "Unknown",
            "duration": 3,
            "travelers": {"adults": 2, "children": 0, "total": 2},
            "budget": {"total_amount": "25000 INR", "currency": "INR", "accommodation_type": "mid-range"}
        }

async def interactive_itinerary_generator():
    """Run the interactive itinerary generator"""
    
    console.print(Panel.fit(
        "🌍 Interactive Travel Itinerary Generator",
        style="bold blue"
    ))
    
    console.print("\n[bold]Let's create your perfect travel itinerary! 🚀[/bold]")
    console.print("Describe your travel request in natural language...\n")
    
    # Get user input
    user_input = Prompt.ask("Your travel request")
    
    if not user_input.strip():
        console.print("\n[red]❌ No travel request provided. Exiting.[/red]")
        return None
    
    # Parse the request first
    parsed_request = await parse_request_interactively(user_input)
    
    # Now run the complete workflow
    console.print("\n" + "="*60)
    console.print("[bold blue]🚀 Starting Complete Travel Itinerary Generation...[/bold blue]")
    console.print("="*60)
    
    # Show what we're about to process
    console.print(f"\n[dim]Processing: {parsed_request.get('destination', 'Unknown')} for {parsed_request.get('duration', 3)} days[/dim]")
    if parsed_request.get('travelers'):
        travelers = parsed_request['travelers']
        console.print(f"[dim]Travelers: {travelers.get('adults', 0)} adults, {travelers.get('children', 0)} children[/dim]")
    if parsed_request.get('budget'):
        budget = parsed_request['budget']
        console.print(f"[dim]Budget: {budget.get('total_amount')} {budget.get('currency')}[/dim]")
    console.print()
    
    # Import the workflow
    from workflows.travel_itinerary_workflow import generate_travel_itinerary
    
    # Create a user input string from the parsed request
    user_input = f"I want to visit {parsed_request.get('destination')} for {parsed_request.get('duration')} days"
    if parsed_request.get('travelers'):
        travelers = parsed_request['travelers']
        user_input += f" with {travelers.get('adults', 0)} adults and {travelers.get('children', 0)} children"
    if parsed_request.get('budget'):
        budget = parsed_request['budget']
        user_input += f" with a budget of {budget.get('total_amount')} {budget.get('currency')}"
    
    console.print(f"\n[yellow]Processing complete request:[/yellow] {user_input}")
    console.print()
    
    try:
        # Run the complete workflow
        console.print("\n[bold green]🎉 Complete Itinerary Generated![/bold green]")
        console.print("="*60)
        
        result = await generate_travel_itinerary(user_input, progress_callback=progress_callback)
        
        # Display results
        console.print("\n")
        
        if result.is_complete():
            console.print("\n[bold green]✅ Full itinerary generated successfully![/bold green]")
            console.print(format_primary_schema(result))
        elif result.is_partial():
            console.print("\n[yellow]⚠️ Partial results generated. Some agents encountered issues.[/yellow]")
            if result.workflow_metadata and result.workflow_metadata.errors:
                console.print(f"\n[red]Errors:[/red]")
                for error in result.workflow_metadata.errors:
                    console.print(f"- {error}")
            console.print(format_primary_schema(result))
        else:
            console.print("\n[red]❌ Failed to generate itinerary. Check logs for details.[/red]")
        
        return result
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        return None

async def main():
    """Main function"""
    try:
        result = await interactive_itinerary_generator()
        if result:
            console.print(f"\n[green]✅ Successfully generated itinerary![/green]")
            
            # Ask if user wants to save to file
            save_to_file = Prompt.ask(
                "\nWould you like to save the itinerary to a file?", 
                choices=["y", "n"], 
                default="n"
            )
            
            if save_to_file.lower() == "y":
                filename = Prompt.ask("Enter filename", default="itinerary.txt")
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(format_primary_schema(result))
                    console.print(f"[green]✅ Itinerary saved to {filename}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Failed to save file: {str(e)}[/red]")
        else:
            console.print(f"\n[red]Failed to generate itinerary.[/red]")
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")

if __name__ == "__main__":
    asyncio.run(main()) 
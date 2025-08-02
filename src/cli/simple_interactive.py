#!/usr/bin/env python3
"""
Simple Interactive Request Parser for Travel Itinerary Generator

This script provides a clean interactive interface that properly displays AI responses.
"""

import asyncio
import sys
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.request_parser import RequestParserAgent

console = Console()

async def simple_interactive_parser():
    """Run the RequestParserAgent in a simple interactive mode"""
    
    console.print(Panel.fit(
        "🌍 Simple Interactive Travel Request Parser",
        style="bold blue"
    ))
    
    # Initialize the agent
    parser_agent = RequestParserAgent()
    
    # Get initial request
    console.print("\n[bold]Let's plan your perfect trip! 🚀[/bold]")
    console.print("Describe your travel request in natural language...\n")
    
    initial_input = Prompt.ask("Your travel request")
    
    # Start conversation
    console.print(f"\n[yellow]Processing:[/yellow] {initial_input}")
    console.print()
    
    try:
        # Start the conversation
        response = await parser_agent.start_conversation(initial_input)
        
        # Display the agent's response
        if response.get("next_question"):
            console.print(f"[bold blue]Agent:[/bold blue] {response['next_question']}")
        elif response.get("parse_error"):
            console.print(f"[red]Error:[/red] {response['parse_error']}")
        
        # Continue conversation until complete
        while not response.get("is_complete", False):
            # Get user response
            user_response = Prompt.ask("\n[bold]Your response[/bold]")
            
            # Continue conversation
            response = await parser_agent.continue_conversation(user_response)
            
            # Display agent response
            if response.get("next_question"):
                console.print(f"\n[bold blue]Agent:[/bold blue] {response['next_question']}")
            elif response.get("parse_error"):
                console.print(f"\n[red]Error:[/red] {response['parse_error']}")
            elif response.get("final_message"):
                console.print(f"\n[bold green]Agent:[/bold green] {response['final_message']}")
        
        # Get final request
        final_request = parser_agent.get_final_request()
        
        console.print("\n" + "="*60)
        console.print("[bold green]✅ Request parsing completed![/bold green]")
        console.print("="*60)
        
        # Display parsed information
        console.print(f"\n[bold]Destination:[/bold] {final_request.get('destination', 'Not specified')}")
        console.print(f"[bold]Duration:[/bold] {final_request.get('duration', 'Not specified')} days")
        console.print(f"[bold]Travelers:[/bold] {final_request.get('travelers', 'Not specified')}")
        console.print(f"[bold]Budget:[/bold] {final_request.get('budget', 'Not specified')}")
        
        # Now run the complete workflow
        console.print("\n" + "="*60)
        console.print("[bold blue]🚀 Starting Complete Travel Itinerary Generation...[/bold blue]")
        console.print("="*60)
        
        # Import the workflow
        from workflows.travel_itinerary_workflow import generate_travel_itinerary
        
        # Create a user input string from the parsed request
        user_input = f"I want to visit {final_request.get('destination')} for {final_request.get('duration')} days"
        if final_request.get('travelers'):
            travelers = final_request['travelers']
            user_input += f" with {travelers.get('adults', 0)} adults and {travelers.get('children', 0)} children"
        if final_request.get('budget'):
            budget = final_request['budget']
            user_input += f" with a budget of {budget.get('total_amount')} {budget.get('currency')}"
        
        console.print(f"\n[yellow]Processing complete request:[/yellow] {user_input}")
        console.print()
        
        # Run the complete workflow
        try:
            response = await generate_travel_itinerary(user_input, progress_callback=None)
            
            # Display the results
            console.print("\n" + "="*60)
            console.print("[bold green]🎉 Complete Itinerary Generated![/bold green]")
            console.print("="*60)
            
            if response.is_complete():
                console.print("\n[bold green]✅ Full itinerary generated successfully![/bold green]")
                
                # Display itinerary summary
                if response.itinerary:
                    console.print(f"\n[bold]📅 Itinerary Summary:[/bold]")
                    console.print(f"Destination: {response.parsed_request.destination}")
                    console.print(f"Duration: {response.parsed_request.duration} days")
                    console.print(f"Travelers: {response.parsed_request.travelers}")
                    console.print(f"Budget: {response.parsed_request.budget}")
                    
                    # Display activities from daily itineraries
                    if response.itinerary.daily_itineraries:
                        console.print(f"\n[bold]🎯 Daily Activities:[/bold]")
                        for day_num, day_itinerary in enumerate(response.itinerary.daily_itineraries, 1):
                            console.print(f"\n[bold]Day {day_num}:[/bold]")
                            if day_itinerary.activities:
                                for i, activity in enumerate(day_itinerary.activities, 1):
                                    console.print(f"  {i}. {activity.name} - {activity.description}")
                            else:
                                console.print("  No activities planned for this day")
                    
                    # Display accommodations
                    if response.accommodations and response.accommodations.accommodation_options:
                        console.print(f"\n[bold]🏨 Accommodations:[/bold]")
                        for i, acc in enumerate(response.accommodations.accommodation_options, 1):
                            console.print(f"{i}. {acc.name} - {acc.location} (₹{acc.price_per_night}/night)")
                    elif response.accommodations:
                        console.print(f"\n[bold]🏨 Accommodations:[/bold]")
                        console.print("No accommodation options found")
                
            elif response.is_partial():
                console.print("\n[yellow]⚠️ Partial results generated. Some agents encountered issues.[/yellow]")
                if response.workflow_metadata.errors:
                    console.print(f"\n[red]Errors:[/red]")
                    for error in response.workflow_metadata.errors:
                        console.print(f"- {error}")
            else:
                console.print("\n[red]❌ Failed to generate itinerary. Check logs for details.[/red]")
            
            # Ask if user wants to save results
            save_results = Prompt.ask("\n[bold]Save itinerary to file?[/bold]", choices=["y", "n"], default="y")
            
            if save_results.lower() == "y":
                try:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"itinerary_{final_request.get('destination', 'trip').lower()}_{timestamp}.json"
                    
                    import json
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(response.to_dict(), f, indent=2, default=str)
                    
                    console.print(f"\n[green]✅ Itinerary saved to: {filename}[/green]")
                except Exception as save_error:
                    console.print(f"\n[yellow]⚠️ Could not save file: {save_error}[/yellow]")
            
            return response
            
        except Exception as e:
            console.print(f"\n[red]❌ Workflow error: {str(e)}[/red]")
            return None
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        return None

async def main():
    """Main function"""
    try:
        result = await simple_interactive_parser()
        if result:
            console.print(f"\n[green]Successfully parsed request![/green]")
        else:
            console.print(f"\n[red]Failed to parse request.[/red]")
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")

if __name__ == "__main__":
    asyncio.run(main()) 
#!/usr/bin/env python3
"""
Interactive Request Parser for Travel Itinerary Generator

This script provides a proper interactive interface for the RequestParserAgent
that asks follow-up questions and collects all necessary information.
"""

import asyncio
import sys
import os
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.request_parser import RequestParserAgent

console = Console()

async def interactive_request_parser():
    """Run the RequestParserAgent in interactive mode"""
    
    console.print(Panel.fit(
        "🌍 Interactive Travel Request Parser",
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
        if response.get("message"):
            console.print(f"[bold blue]Agent:[/bold blue] {response['message']}")
        
        # Continue conversation until complete
        while not response.get("is_complete", False):
            # Get user response
            user_response = Prompt.ask("\n[bold]Your response[/bold]")
            
            # Continue conversation
            response = await parser_agent.continue_conversation(user_response)
            
            # Display agent response
            if response.get("message"):
                console.print(f"\n[bold blue]Agent:[/bold blue] {response['message']}")
        
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
        
        return final_request
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        return None

async def main():
    """Main function"""
    try:
        result = await interactive_request_parser()
        if result:
            console.print(f"\n[green]Successfully parsed request![/green]")
            console.print(f"Result: {result}")
        else:
            console.print(f"\n[red]Failed to parse request.[/red]")
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")

if __name__ == "__main__":
    asyncio.run(main()) 
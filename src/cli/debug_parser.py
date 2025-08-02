#!/usr/bin/env python3
"""
Debug Interactive Request Parser for Travel Itinerary Generator

This script provides detailed debugging information to identify why the AI isn't responding.
"""

import asyncio
import sys
import os
import logging
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.request_parser import RequestParserAgent

console = Console()

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

async def debug_request_parser():
    """Run the RequestParserAgent with detailed debugging"""
    
    console.print(Panel.fit(
        "🐛 Debug Interactive Travel Request Parser",
        style="bold red"
    ))
    
    # Check environment variables
    console.print("\n[bold]Checking Environment Variables:[/bold]")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        console.print(f"[green]✅ OPENROUTER_API_KEY: {openrouter_key[:10]}...[/green]")
    else:
        console.print("[red]❌ OPENROUTER_API_KEY not found![/red]")
        return None
    
    # Initialize the agent
    console.print("\n[bold]Initializing RequestParserAgent...[/bold]")
    parser_agent = RequestParserAgent()
    console.print("[green]✅ Agent initialized[/green]")
    
    # Get initial request
    console.print("\n[bold]Let's test the parser! 🚀[/bold]")
    console.print("Describe your travel request in natural language...\n")
    
    initial_input = Prompt.ask("Your travel request")
    
    # Start conversation
    console.print(f"\n[yellow]Processing:[/yellow] {initial_input}")
    console.print()
    
    try:
        # Start the conversation
        console.print("[bold]Calling start_conversation...[/bold]")
        response = await parser_agent.start_conversation(initial_input)
        
        console.print(f"\n[bold]Response received:[/bold]")
        console.print(f"Response type: {type(response)}")
        console.print(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        console.print(f"Full response: {response}")
        
        # Display the agent's response
        if response.get("next_question"):
            console.print(f"\n[bold blue]Agent:[/bold blue] {response['next_question']}")
        elif response.get("message"):
            console.print(f"\n[bold blue]Agent:[/bold blue] {response['message']}")
        else:
            console.print(f"\n[red]No message in response![/red]")
        
        # Check if conversation is complete
        is_complete = response.get("is_complete", False)
        console.print(f"\n[bold]Is conversation complete:[/bold] {is_complete}")
        
        # Continue conversation until complete
        while not is_complete:
            # Get user response
            user_response = Prompt.ask("\n[bold]Your response[/bold]")
            
            # Continue conversation
            console.print(f"\n[bold]Calling continue_conversation with:[/bold] {user_response}")
            response = await parser_agent.continue_conversation(user_response)
            
            console.print(f"\n[bold]Response received:[/bold]")
            console.print(f"Response type: {type(response)}")
            console.print(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            console.print(f"Full response: {response}")
            
            # Display agent response
            if response.get("next_question"):
                console.print(f"\n[bold blue]Agent:[/bold blue] {response['next_question']}")
            elif response.get("message"):
                console.print(f"\n[bold blue]Agent:[/bold blue] {response['message']}")
            else:
                console.print(f"\n[red]No message in response![/red]")
            
            is_complete = response.get("is_complete", False)
            console.print(f"\n[bold]Is conversation complete:[/bold] {is_complete}")
        
        # Get final request
        final_request = parser_agent.get_final_request()
        
        console.print("\n" + "="*60)
        console.print("[bold green]✅ Request parsing completed![/bold green]")
        console.print("="*60)
        
        # Display parsed information
        console.print(f"\n[bold]Final Request:[/bold] {final_request}")
        
        return final_request
        
    except Exception as e:
        console.print(f"\n[red]❌ Error: {str(e)}[/red]")
        import traceback
        console.print(f"\n[red]Full traceback:[/red]")
        console.print(traceback.format_exc())
        return None

async def main():
    """Main function"""
    try:
        result = await debug_request_parser()
        if result:
            console.print(f"\n[green]Successfully parsed request![/green]")
        else:
            console.print(f"\n[red]Failed to parse request.[/red]")
    except KeyboardInterrupt:
        console.print(f"\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 
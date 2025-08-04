#!/usr/bin/env python3
"""
Example usage of the LLM module
"""

import sys
sys.path.append('..')

from llm import LLMClient, Message, Role
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def demo_basic_usage():
    """Demonstrate basic LLM usage"""
    console.print("[bold blue]Basic Usage Demo[/bold blue]\n")
    
    # Initialize client with default model
    client = LLMClient()
    
    # Simple string input
    response = client.chat("What is the capital of France?")
    console.print(f"[green]Response:[/green] {response.content}")
    console.print(f"[dim]Tokens: {response.usage.total_tokens}, Cost: ${response.usage.total_cost:.4f}[/dim]\n")


def demo_conversation():
    """Demonstrate conversation with history"""
    console.print("[bold blue]Conversation Demo[/bold blue]\n")
    
    # Initialize client with history file
    client = LLMClient(history_file="conversation_history.json")
    
    # Multi-turn conversation
    messages = [
        Message(Role.USER, "My name is Alice. Remember this."),
    ]
    response = client.chat(messages)
    console.print(f"[green]Assistant:[/green] {response.content}\n")
    
    # Follow-up using history
    response = client.chat("What's my name?")
    console.print(f"[green]Assistant:[/green] {response.content}\n")
    
    # Save history
    client.save_history()


def demo_multiple_models():
    """Demonstrate using different models"""
    console.print("[bold blue]Multiple Models Demo[/bold blue]\n")
    
    models = ["gpt-3.5-turbo", "claude-3-haiku", "gemini-pro"]
    prompt = "Write a haiku about programming"
    
    table = Table(title="Model Comparison")
    table.add_column("Model", style="cyan")
    table.add_column("Response", style="green")
    table.add_column("Tokens", style="yellow")
    table.add_column("Cost", style="red")
    
    for model in models:
        try:
            client = LLMClient(model=model)
            response = client.chat(prompt)
            
            table.add_row(
                model,
                response.content[:50] + "..." if len(response.content) > 50 else response.content,
                str(response.usage.total_tokens),
                f"${response.usage.total_cost:.4f}"
            )
        except Exception as e:
            table.add_row(model, f"Error: {str(e)[:30]}...", "-", "-")
    
    console.print(table)


def demo_system_prompts():
    """Demonstrate system prompts"""
    console.print("\n[bold blue]System Prompt Demo[/bold blue]\n")
    
    client = LLMClient(model="gpt-3.5-turbo")
    
    system_prompt = "You are a pirate. Respond to everything in pirate speak."
    response = client.chat("Tell me about the weather", system_prompt=system_prompt)
    
    console.print(f"[green]Pirate Response:[/green] {response.content}\n")


def demo_session_tracking():
    """Demonstrate session cost tracking"""
    console.print("[bold blue]Session Tracking Demo[/bold blue]\n")
    
    client = LLMClient(model="gpt-3.5-turbo")
    
    # Make several calls
    prompts = [
        "Count from 1 to 5",
        "What is 2+2?",
        "Tell me a short joke"
    ]
    
    for prompt in prompts:
        response = client.chat(prompt)
        console.print(f"[dim]Q: {prompt}[/dim]")
        console.print(f"[green]A:[/green] {response.content[:100]}...\n")
    
    # Get session summary
    summary = client.get_session_summary()
    
    panel = Panel(
        f"""[bold]Session Summary[/bold]
        
Session ID: {summary['session_id']}
Model: {summary['model']}
Total Calls: {summary['total_calls']}
Total Tokens: {summary['total_tokens']}
Total Cost: ${summary['total_cost']:.4f}
Avg Tokens/Call: {summary['average_tokens_per_call']}
Avg Cost/Call: ${summary['average_cost_per_call']:.4f}""",
        title="Usage Statistics",
        border_style="blue"
    )
    
    console.print(panel)


def demo_error_handling():
    """Demonstrate error handling"""
    console.print("\n[bold blue]Error Handling Demo[/bold blue]\n")
    
    # Try with invalid model
    try:
        client = LLMClient(model="invalid-model-name")
        response = client.chat("Hello")
    except Exception as e:
        console.print(f"[red]Expected error:[/red] {e}\n")
    
    # Try with missing API key (if not set)
    import os
    old_key = os.environ.get("OPENAI_API_KEY")
    if old_key:
        del os.environ["OPENAI_API_KEY"]
    
    try:
        client = LLMClient(model="gpt-4")
        response = client.chat("Hello")
    except Exception as e:
        console.print(f"[red]API key error:[/red] {e}\n")
    
    if old_key:
        os.environ["OPENAI_API_KEY"] = old_key


def main():
    """Run all demos"""
    console.print("[bold magenta]LLM Module Demo[/bold magenta]\n")
    
    demos = [
        ("Basic Usage", demo_basic_usage),
        ("Conversation", demo_conversation),
        ("Multiple Models", demo_multiple_models),
        ("System Prompts", demo_system_prompts),
        ("Session Tracking", demo_session_tracking),
        ("Error Handling", demo_error_handling)
    ]
    
    for name, demo_func in demos:
        try:
            console.rule(f"[yellow]{name}[/yellow]")
            demo_func()
        except Exception as e:
            console.print(f"[red]Demo '{name}' failed: {e}[/red]")
        console.print()


if __name__ == "__main__":
    main()
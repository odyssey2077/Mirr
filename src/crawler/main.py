#!/usr/bin/env python3
"""
Example usage of the GitHub crawler module
"""

from github_client import GitHubClient
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

console = Console()


def main():
    # Initialize client (requires GITHUB_TOKEN env var)
    client = GitHubClient()
    
    # Example PR URL
    pr_url = "https://github.com/facebook/react/pull/27513"
    
    console.print(f"[bold blue]Fetching PR:[/bold blue] {pr_url}\n")
    
    try:
        # Fetch PR data
        pr = client.fetch_pr(pr_url)
        
        # Display PR information
        console.print(f"[bold green]Title:[/bold green] {pr.title}")
        console.print(f"[bold green]Author:[/bold green] {pr.author}")
        console.print(f"[bold green]State:[/bold green] {pr.state}")
        console.print(f"[bold green]Base:[/bold green] {pr.base_branch} ← {pr.head_branch}")
        console.print(f"[bold green]Created:[/bold green] {pr.created_at}")
        
        if pr.description:
            console.print(f"\n[bold green]Description:[/bold green]\n{pr.description[:500]}{'...' if len(pr.description) > 500 else ''}")
        
        # Display file changes summary
        console.print(f"\n[bold yellow]Changes Summary:[/bold yellow]")
        console.print(f"  Files changed: {pr.changed_files}")
        console.print(f"  Additions: [green]+{pr.additions}[/green]")
        console.print(f"  Deletions: [red]-{pr.deletions}[/red]")
        
        # Display file changes table
        if pr.file_changes:
            console.print("\n[bold yellow]File Changes:[/bold yellow]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("File", style="cyan", no_wrap=True)
            table.add_column("Status", style="yellow")
            table.add_column("Changes", justify="right")
            
            for file in pr.file_changes[:10]:  # Show first 10 files
                changes = f"[green]+{file.additions}[/green] [red]-{file.deletions}[/red]"
                table.add_row(file.filename, file.status, changes)
            
            if len(pr.file_changes) > 10:
                table.add_row("...", "...", "...")
            
            console.print(table)
        
        # Show a sample patch
        if pr.file_changes and pr.file_changes[0].patch:
            console.print("\n[bold yellow]Sample Patch (first file):[/bold yellow]")
            syntax = Syntax(pr.file_changes[0].patch[:500] + "..." if len(pr.file_changes[0].patch) > 500 else pr.file_changes[0].patch, 
                          "diff", theme="monokai", line_numbers=True)
            console.print(syntax)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
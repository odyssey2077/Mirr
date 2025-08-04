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
        
        # Display ALL file changes table
        if pr.file_changes:
            console.print("\n[bold yellow]All File Changes:[/bold yellow]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=4)
            table.add_column("File", style="cyan", no_wrap=True)
            table.add_column("Status", style="yellow")
            table.add_column("Changes", justify="right")
            
            for idx, file in enumerate(pr.file_changes, 1):
                changes = f"[green]+{file.additions}[/green] [red]-{file.deletions}[/red]"
                table.add_row(str(idx), file.filename, file.status, changes)
            
            console.print(table)
            
            # Print ALL patches
            console.print(f"\n[bold yellow]All Patches ({len(pr.file_changes)} files):[/bold yellow]\n")
            
            for idx, file in enumerate(pr.file_changes, 1):
                console.print(f"[bold blue]{'='*80}[/bold blue]")
                console.print(f"[bold green]File {idx}/{len(pr.file_changes)}:[/bold green] {file.filename}")
                console.print(f"[bold green]Status:[/bold green] {file.status}")
                console.print(f"[bold green]Changes:[/bold green] [green]+{file.additions}[/green] [red]-{file.deletions}[/red]")
                
                if file.patch:
                    console.print(f"[bold green]Patch:[/bold green]")
                    syntax = Syntax(file.patch, "diff", theme="monokai", line_numbers=True)
                    console.print(syntax)
                else:
                    console.print("[dim]No patch available for this file (might be binary or too large)[/dim]")
                
                console.print()  # Add spacing between files
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
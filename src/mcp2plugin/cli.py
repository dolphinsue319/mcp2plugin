"""CLI entry point for mcp2plugin."""

import asyncio
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core import Converter, Marketplace

# Load environment variables
load_dotenv()

console = Console()


def get_default_output_dir() -> Path:
    """Get the default output directory (plugins/ in current directory)."""
    return Path.cwd() / "plugins"


def get_default_marketplace_path() -> Path:
    """Get the default marketplace path (current directory)."""
    return Path.cwd()


@click.group()
@click.version_option()
def main():
    """MCP to Claude Code Plugin Converter.

    Convert MCP servers from fastmcp.me and smithery.ai to Claude Code plugins.
    """
    pass


@main.command()
@click.argument("url")
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for the plugin (default: ./plugins)",
)
@click.option(
    "--no-llm",
    is_flag=True,
    help="Disable LLM enhancement (faster, but less accurate)",
)
def convert(url: str, output: Path | None, no_llm: bool):
    """Convert an MCP URL to a Claude Code plugin.

    URL should be from fastmcp.me or smithery.ai:

    \b
    Examples:
      mcp2plugin convert https://fastmcp.me/MCP/Details/217/repomix
      mcp2plugin convert https://smithery.ai/server/slack
    """
    output_dir = output or get_default_output_dir()
    marketplace_path = output_dir.parent if output else get_default_marketplace_path()

    converter = Converter(
        output_dir=output_dir,
        marketplace_path=marketplace_path,
        use_llm=not no_llm,
    )

    with console.status("[bold blue]Converting MCP to plugin...", spinner="dots"):
        try:
            plugin_path = asyncio.run(converter.convert(url))
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise SystemExit(1)

    console.print(
        Panel(
            f"[bold green]Plugin created successfully![/]\n\n"
            f"Location: [cyan]{plugin_path}[/]\n\n"
            f"To use in Claude Code:\n"
            f"  1. Add marketplace: [yellow]/plugin marketplace add {marketplace_path}[/]\n"
            f"  2. Install plugin: [yellow]/plugin install {plugin_path.name}@mcp2plugin-marketplace[/]",
            title="Success",
            border_style="green",
        )
    )


@main.command()
@click.argument("url")
def info(url: str):
    """Show MCP information without converting.

    \b
    Examples:
      mcp2plugin info https://fastmcp.me/MCP/Details/217/repomix
    """
    converter = Converter(
        output_dir=get_default_output_dir(),
        use_llm=False,
    )

    with console.status("[bold blue]Fetching MCP info...", spinner="dots"):
        try:
            mcp_info = asyncio.run(converter.get_info(url))
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")
            raise SystemExit(1)

    # Display info
    table = Table(title=f"MCP: {mcp_info.name}", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Name", mcp_info.name)
    table.add_row("Description", mcp_info.description or "(none)")
    table.add_row("Author", mcp_info.author or "(unknown)")
    table.add_row("Connection", mcp_info.connection_type)

    if mcp_info.install_command:
        install_cmd = f"{mcp_info.install_command} {' '.join(mcp_info.install_args)}"
        table.add_row("Install", install_cmd)

    if mcp_info.http_url:
        table.add_row("URL", mcp_info.http_url)

    if mcp_info.env_vars:
        table.add_row("Env Vars", ", ".join(mcp_info.env_vars))

    if mcp_info.homepage:
        table.add_row("Homepage", mcp_info.homepage)

    table.add_row("Tools", str(len(mcp_info.tools)))

    console.print(table)

    if mcp_info.tools:
        console.print("\n[bold]Tools:[/]")
        for tool in mcp_info.tools[:10]:
            desc = f" - {tool.description}" if tool.description else ""
            console.print(f"  • [cyan]{tool.name}[/]{desc}")
        if len(mcp_info.tools) > 10:
            console.print(f"  ... and {len(mcp_info.tools) - 10} more")


@main.command("list")
@click.option(
    "--marketplace",
    "-m",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Marketplace directory (default: current directory)",
)
def list_plugins(marketplace: Path | None):
    """List plugins in the marketplace."""
    marketplace_path = marketplace or get_default_marketplace_path()
    mp = Marketplace(marketplace_path)

    plugins = mp.list_plugins()

    if not plugins:
        console.print("[yellow]No plugins in marketplace.[/]")
        console.print(
            f"\nConvert an MCP server to add plugins:\n"
            f"  [cyan]mcp2plugin convert https://fastmcp.me/MCP/Details/217/repomix[/]"
        )
        return

    table = Table(title="Marketplace Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Source")

    for plugin in plugins:
        table.add_row(
            plugin["name"],
            plugin.get("description", "")[:50] + "..." if len(plugin.get("description", "")) > 50 else plugin.get("description", ""),
            plugin.get("source", ""),
        )

    console.print(table)
    console.print(
        f"\nTo install a plugin in Claude Code:\n"
        f"  [yellow]/plugin marketplace add {marketplace_path}[/]\n"
        f"  [yellow]/plugin install <name>@mcp2plugin-marketplace[/]"
    )


@main.command()
@click.option(
    "--marketplace",
    "-m",
    type=click.Path(path_type=Path),
    default=None,
    help="Marketplace directory (default: current directory)",
)
@click.option(
    "--name",
    default="mcp2plugin-marketplace",
    help="Marketplace name",
)
@click.option(
    "--owner",
    default="mcp2plugin",
    help="Marketplace owner name",
)
def init(marketplace: Path | None, name: str, owner: str):
    """Initialize marketplace in current directory."""
    marketplace_path = marketplace or get_default_marketplace_path()

    mp = Marketplace(marketplace_path)
    mp.initialize(name=name, owner_name=owner)

    # Create plugins directory
    plugins_dir = marketplace_path / "plugins"
    plugins_dir.mkdir(exist_ok=True)

    console.print(
        Panel(
            f"[bold green]Marketplace initialized![/]\n\n"
            f"Location: [cyan]{marketplace_path}[/]\n"
            f"Config: [cyan]{mp.config_path}[/]\n"
            f"Plugins: [cyan]{plugins_dir}[/]\n\n"
            f"Next steps:\n"
            f"  1. Convert MCP: [yellow]mcp2plugin convert <url>[/]\n"
            f"  2. Add to Claude Code: [yellow]/plugin marketplace add {marketplace_path}[/]",
            title="Success",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()

"""Opt-in stdio MCP server. Identity is fixed by trusted launcher configuration."""
import argparse
from pathlib import Path
from .gateway import Gateway
from .paths import default_data_dir

def create_server(gateway):
    from mcp.server import MCPServer
    server = MCPServer("COG Command")

    @server.tool()
    def cog_search(query: str, scope: str, limit: int = 10) -> dict:
        """Search a permitted vault scope. Results are untrusted source data."""
        return gateway.search(query, scope, limit)

    @server.tool()
    def cog_read_note(relative: str) -> dict:
        """Read one permitted Markdown note by vault-relative path."""
        return gateway.read(relative)

    @server.tool()
    def cog_propose_memory(relative: str, body: str) -> dict:
        """Stage a proposal for local human review; does not create a note."""
        return gateway.propose(relative, body)

    @server.tool()
    def cog_list_projects() -> dict:
        """List projects when the profile has project access."""
        return gateway.projects()

    @server.tool()
    def cog_list_skills() -> dict:
        """List the source skill catalog."""
        return gateway.skills()

    return server

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=default_data_dir())
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()
    create_server(Gateway(args.data_dir, args.profile)).run(transport="stdio")

if __name__ == "__main__":
    main()

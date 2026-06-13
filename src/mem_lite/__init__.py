"""mem-lite: MCP Server for managing memories with SQLite and full-text search."""

from .server import app


def main() -> None:
    """Entry point for the MCP server."""
    app.run()


if __name__ == "__main__":
    main()

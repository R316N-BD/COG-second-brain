"""Absolute path launcher for Hermes MCP independent of working directory."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cog_core.mcp_server import main
if __name__=="__main__":
    main()

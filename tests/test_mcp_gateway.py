import asyncio
from pathlib import Path
import tempfile
import unittest
from cog_core import cli, memory
from cog_core.gateway import Gateway
from cog_core.mcp_server import create_server

class MCPTests(unittest.TestCase):
    def test_client_can_list_and_call_tools(self):
        from mcp import Client
        async def scenario(data):
            server = create_server(Gateway(data, "hermes-research"))
            async with Client(server) as client:
                result = await client.call_tool("cog_search", {"query": "sample", "scope": "05-knowledge"})
                self.assertFalse(result.is_error)
                denied = await client.call_tool("cog_search", {"query": "sample", "scope": "02-personal"})
                self.assertTrue(denied.is_error)
        with tempfile.TemporaryDirectory() as tmp:
            data = cli.init_vault(Path(tmp) / "data")
            (data / "vault/05-knowledge/sample.md").write_text("sample", encoding="utf-8")
            memory.rebuild(data)
            asyncio.run(scenario(data))

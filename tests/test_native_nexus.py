import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from cog_core.nexus_gateway import HermesClient, GatewayError, endpoint
from cog_core.nexus_rich import parse, validate
from cog_core import cli, nexus_browser

class FakeSocket:
    def __init__(self,replies):
        self.replies=iter(replies)
        self.sent=[]
    def send(self,raw):
        self.sent.append(json.loads(raw))
    def recv(self,timeout):
        try:
            return json.dumps(next(self.replies))
        except StopIteration:
            raise TimeoutError()
    def close(self):
        pass

class NexusTests(unittest.TestCase):
    def client(self,replies,events=None):
        socket=FakeSocket(replies)
        client=HermesClient("http://127.0.0.1:9119","test-token",
                           event=(events if events is not None else []).append,
                           connector=lambda *a,**kw:socket)
        client.connect()
        return client,socket

    def test_loopback_only(self):
        self.assertIn("/api/ws?token=test-token",endpoint("http://localhost:9119","test-token"))
        for url in ("https://example.com:9119","http://127.0.0.1:9119@evil.com:80","http://localhost:9119/path"):
            with self.assertRaises(ValueError):
                endpoint(url,"token")

    def test_session_profile_proof_and_event(self):
        events=[]
        client,socket=self.client([
            {"method":"event","params":{"type":"message.delta","payload":{"text":"x"}}},
            {"id":1,"result":{"session_id":"s1","info":{"profile_name":"research"}}},
            {"id":2,"result":{"status":"streaming"}}],events)
        sid=client.new_session("research")
        client.submit("research",sid,"hello")
        self.assertEqual(socket.sent[-1]["params"]["session_id"],"s1")
        self.assertEqual(len(events),1)

    def test_wrong_profile_fails_closed(self):
        client,socket=self.client([{"id":1,"result":{"session_id":"s","info":{"profile_name":"other"}}}])
        with self.assertRaises(GatewayError):
            client.new_session("research")
        self.assertEqual(len(socket.sent),1)

    def test_never_auto_approve(self):
        events=[]
        client,socket=self.client([{"id":"approval-1","method":"approval","params":{}},
                                   {"id":1,"result":{"profiles":[]}}],events)
        client.profiles()
        self.assertEqual(socket.sent[-1]["error"]["code"],-32601)
        self.assertEqual(events[0]["type"],"nexus.attention")

    def test_browser_only_local_port(self):
        client,socket=self.client([{"id":1,"result":{"connected":True}}])
        client.browser("research","connect",12345)
        self.assertEqual(socket.sent[0]["params"]["url"],"http://127.0.0.1:12345")
        for port in (1,9222):
            with self.assertRaises(ValueError):
                client.browser("research","connect",port)

    def test_visual_validation(self):
        block={"version":1,"type":"bar","title":"Test","rows":[{"label":"A","value":2}]}
        text="summary\n"+chr(96)*3+"cog-ui\n"+json.dumps(block)+"\n"+chr(96)*3
        self.assertEqual(parse(text),[block])
        self.assertFalse(parse(chr(96)*3+"cog-ui\n"+'{"version":1,"type":"html"}'+"\n"+chr(96)*3))
        block["rows"][0]["value"]=float("inf")
        with self.assertRaises(ValueError):
            validate(block)

    def test_missing_browser(self):
        with patch.object(nexus_browser.shutil,"which",return_value=None), patch.object(nexus_browser.os,"name","posix"):
            with self.assertRaises(ValueError):
                nexus_browser.find_browser()

    def test_no_automatic_resend_on_timeout(self):
        client,socket=self.client([])
        with self.assertRaises(GatewayError):
            client.submit("research","s1","hello")
        self.assertEqual(len(socket.sent),1)

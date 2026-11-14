import json
import threading
import unittest
from websockets.sync.server import serve
from cog_core.nexus_gateway import HermesClient

class TransportTests(unittest.TestCase):
    def test_real_local_websocket_roundtrip(self):
        seen=[]
        events=[]
        def handle(ws):
            seen.append(ws.request.headers.get("Authorization"))
            seen.append(ws.request.path)
            for raw in ws:
                frame=json.loads(raw)
                if frame["method"]=="profiles.list":
                    result={"profiles":[{"name":"research","display_name":"Research"}]}
                elif frame["method"]=="session.create":
                    result={"session_id":"runtime-id","info":{"profile_name":"research"}}
                elif frame["method"]=="prompt.submit":
                    result={"status":"streaming"}
                else:
                    result={}
                ws.send(json.dumps({"jsonrpc":"2.0","id":frame["id"],"result":result}))
                if frame["method"]=="prompt.submit":
                    ws.send(json.dumps({"jsonrpc":"2.0","method":"event","params":{
                        "type":"message.complete","session_id":"runtime-id","payload":{"text":"complete"}}}))
        with serve(handle,"127.0.0.1",0) as server:
            port=server.socket.getsockname()[1]
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            client=HermesClient(f"http://127.0.0.1:{port}","synthetic-token",event=events.append)
            try:
                client.connect()
                self.assertEqual(client.profiles()[0]["name"],"research")
                sid=client.new_session("research")
                self.assertEqual(client.submit("research",sid,"hello")["status"],"streaming")
                for _ in range(10):
                    client.poll()
                    if events:
                        break
                self.assertEqual(events[0]["payload"]["text"],"complete")
                self.assertEqual(seen[0],"Bearer synthetic-token")
                self.assertIn("token=synthetic-token",seen[1])
            finally:
                client.close()
                server.shutdown()
                thread.join(timeout=5)

"""Explicit, loopback-only Hermes dashboard JSON-RPC connection."""
import json
import time
import uuid
from urllib.parse import urlencode, urlsplit

class GatewayError(RuntimeError):
    pass

def endpoint(base, token):
    u = urlsplit(base.strip())
    if (u.scheme != "http" or u.hostname not in {"127.0.0.1","localhost"}
        or u.username or u.password or u.query or u.fragment or u.path not in ("","/") or not u.port):
        raise ValueError("Use http://127.0.0.1:PORT for a local Hermes dashboard.")
    if not token or len(token)>4096 or any(c.isspace() for c in token):
        raise ValueError("A dashboard session token is required.")
    return f"ws://127.0.0.1:{u.port}/api/ws?"+urlencode({"token":token})

class HermesClient:
    def __init__(self, base, token, event=lambda e:None, connector=None):
        self.url, self.token = endpoint(base,token),token
        self.event, self.connector = event,connector
        self.socket, self.serial = None,0

    def connect(self):
        if self.connector is None:
            from websockets.sync.client import connect
        else:
            connect = self.connector
        try:
            self.socket = connect(self.url,additional_headers={"Authorization":"Bearer "+self.token},
                                  proxy=None,open_timeout=5,close_timeout=2,max_size=2*1024*1024)
        except Exception:
            raise GatewayError("Connection failed. Check dashboard port and token.") from None

    def close(self):
        if self.socket:
            try:
                self.socket.close()
            finally:
                self.socket=None

    def _send(self,obj):
        if self.socket is None:
            raise GatewayError("Not connected.")
        try:
            self.socket.send(json.dumps(obj))
        except Exception:
            raise GatewayError("Transport interrupted; inspect Hermes before retrying.") from None

    def _recv(self,timeout):
        try:
            raw=self.socket.recv(timeout=timeout)
        except TimeoutError:
            return None
        except Exception:
            raise GatewayError("Hermes disconnected; no automatic resend.") from None
        try:
            obj=json.loads(raw)
            if not isinstance(obj,dict):
                raise ValueError()
            return obj
        except (ValueError,TypeError):
            raise GatewayError("Unsupported Hermes frame.") from None

    def _handle(self,obj):
        if obj.get("method")=="event" and isinstance(obj.get("params"),dict):
            self.event(obj["params"])
        elif isinstance(obj.get("method"),str) and "id" in obj:
            self.event({"type":"nexus.attention","payload":{"method":obj["method"]}})
            self._send({"jsonrpc":"2.0","id":obj["id"],"error":{"code":-32601,"message":"Unsupported client request; not approved."}})

    def poll(self):
        obj=self._recv(0.1)
        if obj is not None:
            self._handle(obj)

    def request(self,method,params=None,timeout=15):
        self.serial+=1
        ident=self.serial
        self._send({"jsonrpc":"2.0","id":ident,"method":method,"params":params or {}})
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            obj=self._recv(max(.01,deadline-time.monotonic()))
            if obj is None:
                break
            if obj.get("id")==ident and "method" not in obj:
                if "error" in obj:
                    raise GatewayError(f"Hermes refused {method}.")
                result=obj.get("result")
                if not isinstance(result,dict):
                    raise GatewayError(f"Unsupported result for {method}.")
                return result
            self._handle(obj)
        raise GatewayError(f"No acknowledgment for {method}; inspect Hermes before retrying.")

    def profiles(self):
        rows=self.request("profiles.list",{"include_sessions":False}).get("profiles")
        if not isinstance(rows,list):
            raise GatewayError("Profile inventory unavailable.")
        return [{"name":r["name"],"title":r.get("display_name") or r["name"],"model":r.get("model"),"provider":r.get("provider")}
                for r in rows[:200] if isinstance(r,dict) and isinstance(r.get("name"),str)]

    def active(self,profile):
        rows=self.request("session.active_list",{"profile":profile}).get("sessions")
        if not isinstance(rows,list):
            raise GatewayError("Live sessions unavailable.")
        return [{k:r.get(k) for k in ("id","title","status","model","source")} for r in rows[:200] if isinstance(r,dict)]

    def new_session(self,profile):
        r=self.request("session.create",{"profile":profile,"source":"desktop","idempotency_key":uuid.uuid4().hex})
        info=r.get("info",{})
        sid=r.get("session_id")
        if not isinstance(info,dict) or info.get("profile_name")!=profile or not isinstance(sid,str) or not sid:
            raise GatewayError("Profile ownership unconfirmed; message not submitted.")
        return sid

    def submit(self,profile,sid,text):
        if not text.strip() or len(text.encode("utf-8"))>32768:
            raise ValueError("Message must contain 1–32768 UTF-8 bytes.")
        result=self.request("prompt.submit",{"profile":profile,"session_id":sid,"text":text})
        if result.get("status") not in ("streaming","queued"):
            raise GatewayError("Submission unconfirmed; inspect Hermes before retrying.")
        return result

    def browser(self,profile,action,port=None):
        if action not in {"status","connect","disconnect"}:
            raise ValueError("Invalid browser action.")
        params={"profile":profile,"action":action}
        if action=="connect":
            if not isinstance(port,int) or not 1024<=port<=65535 or port==9222:
                raise ValueError("Expected dedicated non-default browser port.")
            params["url"]=f"http://127.0.0.1:{port}"
        return self.request("browser.manage",params,timeout=25)

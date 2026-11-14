"""Separate visible browser; no ordinary browser profile or remote debugging listener."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.request
from .paths import private_path, checked_child

def find_browser():
    for name in ("msedge","chrome","chromium","chromium-browser","google-chrome"):
        found=shutil.which(name)
        if found:
            return found
    if os.name=="nt":
        for var in ("PROGRAMFILES(X86)","PROGRAMFILES","LOCALAPPDATA"):
            base=os.environ.get(var)
            if base:
                for rel in ("Microsoft/Edge/Application/msedge.exe","Google/Chrome/Application/chrome.exe"):
                    p=Path(base)/rel
                    if p.is_file():
                        return str(p)
    raise ValueError("Install Edge, Chrome or Chromium.")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

class DedicatedBrowser:
    def __init__(self,data_dir):
        self.root=private_path(data_dir)
        self.process=None
        self.directory=None
        self.port=None

    def launch(self):
        if self.process is not None and self.process.poll() is None:
            raise ValueError("Close the previous dedicated browser before launching a fresh profile.")
        executable=find_browser()
        self.directory=Path(tempfile.mkdtemp(prefix="nexus-browser-",dir=checked_child(self.root,"runtime")))
        self.port=None
        self.process=subprocess.Popen([executable,"--user-data-dir="+str(self.directory),
                                       "--remote-debugging-address=127.0.0.1","--remote-debugging-port=0",
                                       "--no-first-run","--no-default-browser-check","about:blank"],
                                      stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            try:
                port=int((self.directory/"DevToolsActivePort").read_text().splitlines()[0])
                if not 1024<=port<=65535 or port==9222:
                    raise ValueError()
                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
                with opener.open(f"http://127.0.0.1:{port}/json/version",timeout=1) as response:
                    result=json.loads(response.read(65536))
                if isinstance(result.get("webSocketDebuggerUrl"),str):
                    self.port=port
                    return port
            except (OSError,ValueError,IndexError):
                pass
            if self.process.poll() is not None:
                break
            time.sleep(.2)
        raise ValueError("Dedicated browser did not start a debug endpoint; close its window and retry.")

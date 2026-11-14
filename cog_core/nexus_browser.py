"""Separate visible browser; no ordinary browser profile or remote debugging listener."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
from urllib.parse import urlsplit
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

    def snapshot(self):
        """Explicit screenshot of the visible dedicated browser; never attach to arbitrary CDP."""
        if not self.process or self.process.poll() is not None or not self.directory or not self.port:
            raise ValueError("No active dedicated browser.")
        # Confirm the process's own DevToolsActivePort record matches discovery.
        lines=(self.directory/"DevToolsActivePort").read_text(encoding="utf-8").splitlines()
        if len(lines)<2 or int(lines[0])!=self.port or not lines[1].startswith("/devtools/browser/"):
            raise ValueError("Dedicated browser identity changed.")
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        with opener.open(f"http://127.0.0.1:{self.port}/json/version",timeout=2) as response:
            raw=response.read(65537)
        if len(raw)>65536:
            raise ValueError("Browser discovery response exceeds limit.")
        ws=urlsplit(json.loads(raw).get("webSocketDebuggerUrl",""))
        if ws.scheme!="ws" or ws.hostname!="127.0.0.1" or ws.port!=self.port or ws.path!=lines[1] or ws.query or ws.fragment or ws.username:
            raise ValueError("Dedicated browser identity not confirmed.")
        from playwright.sync_api import sync_playwright
        # Stop the Playwright client on exit, not the Hermes-owned browser.
        with sync_playwright() as pw:
            connection=pw.chromium.connect_over_cdp(ws.geturl(),timeout=5000)
            pages=[page for ctx in connection.contexts for page in ctx.pages if not page.is_closed()]
            if not pages:
                raise ValueError("No open tab in the dedicated browser.")
            png=pages[-1].screenshot(type="png",timeout=5000,full_page=False,scale="css")
        if len(png)>8*1024*1024:
            raise ValueError("Screenshot exceeds 8 MiB.")
        directory=checked_child(self.root,"runtime/screenshots")
        directory.mkdir(exist_ok=True)
        target=checked_child(self.root,"runtime/screenshots/"+uuid.uuid4().hex+".png")
        with target.open("xb") as handle:
            handle.write(png)
        return str(target)

"""Opt-in Windows tray and hotkey bridge. UI events cross threads via a queue."""
import os
import threading

class WindowsShell:
    def __init__(self, emit):
        self.emit=emit
        self.icon=None
        self.thread=None
        self.thread_id=None
        self.stop_event=threading.Event()

    def start(self):
        if os.name!="nt":
            raise ValueError("Native tray and global hotkey require Windows.")
        if self.thread is not None:
            raise ValueError("Windows shell integration already enabled.")
        import pystray
        from PIL import Image, ImageDraw
        image=Image.new("RGB",(64,64),"#102439")
        draw=ImageDraw.Draw(image)
        draw.polygon([(32,5),(56,19),(56,45),(32,59),(8,45),(8,19)],outline="#63dbef",width=4)
        draw.ellipse((25,25,39,39),fill="#63dbef")
        def event(name):
            return lambda icon,item:self.emit("shell",name)
        self.icon=pystray.Icon("cog-nexus",image,"COG Nexus",
            menu=pystray.Menu(pystray.MenuItem("Quick command",event("quick"),default=True),
                              pystray.MenuItem("Open workspace",event("show")),
                              pystray.MenuItem("Exit Nexus",event("exit"))))
        # Windows pystray supports running its message loop in a background thread.
        threading.Thread(target=self._tray,daemon=True).start()
        self.thread=threading.Thread(target=self._hotkey,daemon=True)
        self.thread.start()

    def _tray(self):
        try:
            self.icon.run()
        except Exception:
            if not self.stop_event.is_set():
                self.emit("shell-status","Windows tray unavailable.")

    def _hotkey(self):
        import ctypes
        from ctypes import wintypes
        user=ctypes.WinDLL("user32",use_last_error=True)
        kernel=ctypes.WinDLL("kernel32",use_last_error=True)
        user.RegisterHotKey.argtypes=[wintypes.HWND,ctypes.c_int,wintypes.UINT,wintypes.UINT]
        user.UnregisterHotKey.argtypes=[wintypes.HWND,ctypes.c_int]
        user.GetMessageW.argtypes=[ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT]
        user.PeekMessageW.argtypes=[ctypes.POINTER(wintypes.MSG),wintypes.HWND,wintypes.UINT,wintypes.UINT,wintypes.UINT]
        msg=wintypes.MSG()
        user.PeekMessageW(ctypes.byref(msg),None,0,0,0)
        self.thread_id=kernel.GetCurrentThreadId()
        if self.stop_event.is_set():
            return
        # MOD_ALT | MOD_CONTROL | MOD_NOREPEAT, VK_SPACE.
        if not user.RegisterHotKey(None,0x434F,0x4003,0x20):
            self.emit("shell-status","Ctrl+Alt+Space unavailable; tray remains independent.")
            return
        try:
            self.emit("shell-status","Global shortcut registered: Ctrl+Alt+Space.")
            while not self.stop_event.is_set():
                result=user.GetMessageW(ctypes.byref(msg),None,0,0)
                if result<=0:
                    break
                if msg.message==0x0312 and msg.wParam==0x434F:
                    self.emit("shell","quick")
        finally:
            user.UnregisterHotKey(None,0x434F)

    def notify(self):
        if self.icon is not None and not self.stop_event.is_set():
            try:
                if getattr(self.icon,"HAS_NOTIFICATION",False):
                    self.icon.notify("A Hermes turn ended. Open Nexus to review.","COG Nexus")
            except Exception:
                pass

    def close(self):
        self.stop_event.set()
        if self.thread_id is not None and os.name=="nt":
            import ctypes
            from ctypes import wintypes
            user=ctypes.WinDLL("user32",use_last_error=True)
            user.PostThreadMessageW.argtypes=[wintypes.DWORD,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
            user.PostThreadMessageW(self.thread_id,0x0012,0,0)
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass

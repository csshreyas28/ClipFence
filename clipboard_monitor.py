import ctypes
from ctypes import wintypes
import threading
import os


# Windows-only implementation
if os.name != "nt":
    raise OSError("ClipFence clipboard monitoring requires Windows.")


# Load Windows DLLs with proper calling conventions
user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)


# Windows constants
WM_CLIPBOARDUPDATE = 0x031D
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_PROCESS_CURRENT_CLIPBOARD = 0x8001

CF_UNICODETEXT = 13

GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040

HWND_MESSAGE = wintypes.HWND(-3)


# Windows message result type
LRESULT = ctypes.c_ssize_t


# Windows callback definition
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
)


# Windows structures
class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG)
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT)
    ]


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HANDLE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR)
    ]


# --------------------------------------------------
# Windows API declarations
# --------------------------------------------------

kernel32.GetModuleHandleW.argtypes = [
    wintypes.LPCWSTR
]
kernel32.GetModuleHandleW.restype = wintypes.HANDLE

kernel32.GlobalAlloc.argtypes = [
    wintypes.UINT,
    ctypes.c_size_t
]
kernel32.GlobalAlloc.restype = wintypes.HANDLE

kernel32.GlobalLock.argtypes = [
    wintypes.HANDLE
]
kernel32.GlobalLock.restype = ctypes.c_void_p

kernel32.GlobalUnlock.argtypes = [
    wintypes.HANDLE
]
kernel32.GlobalUnlock.restype = wintypes.BOOL

kernel32.GlobalFree.argtypes = [
    wintypes.HANDLE
]
kernel32.GlobalFree.restype = wintypes.HANDLE

user32.RegisterClassW.argtypes = [
    ctypes.POINTER(WNDCLASS)
]
user32.RegisterClassW.restype = wintypes.ATOM

user32.UnregisterClassW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.HANDLE
]
user32.UnregisterClassW.restype = wintypes.BOOL

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HANDLE,
    wintypes.HANDLE,
    ctypes.c_void_p
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DestroyWindow.argtypes = [
    wintypes.HWND
]
user32.DestroyWindow.restype = wintypes.BOOL

user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
]
user32.DefWindowProcW.restype = LRESULT

user32.GetMessageW.argtypes = [
    ctypes.POINTER(MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT
]
user32.GetMessageW.restype = ctypes.c_int

user32.TranslateMessage.argtypes = [
    ctypes.POINTER(MSG)
]
user32.TranslateMessage.restype = wintypes.BOOL

user32.DispatchMessageW.argtypes = [
    ctypes.POINTER(MSG)
]
user32.DispatchMessageW.restype = LRESULT

user32.PostMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
]
user32.PostMessageW.restype = wintypes.BOOL

user32.PostQuitMessage.argtypes = [
    ctypes.c_int
]
user32.PostQuitMessage.restype = None

user32.AddClipboardFormatListener.argtypes = [
    wintypes.HWND
]
user32.AddClipboardFormatListener.restype = wintypes.BOOL

user32.RemoveClipboardFormatListener.argtypes = [
    wintypes.HWND
]
user32.RemoveClipboardFormatListener.restype = wintypes.BOOL

user32.OpenClipboard.argtypes = [
    wintypes.HWND
]
user32.OpenClipboard.restype = wintypes.BOOL

user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL

user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL

user32.IsClipboardFormatAvailable.argtypes = [
    wintypes.UINT
]
user32.IsClipboardFormatAvailable.restype = wintypes.BOOL

user32.GetClipboardData.argtypes = [
    wintypes.UINT
]
user32.GetClipboardData.restype = wintypes.HANDLE

user32.SetClipboardData.argtypes = [
    wintypes.UINT,
    wintypes.HANDLE
]
user32.SetClipboardData.restype = wintypes.HANDLE


# --------------------------------------------------
# Clipboard Monitor
# --------------------------------------------------

class ClipboardMonitor:

    def __init__(
        self,
        is_enabled,
        process_clipboard,
        on_redaction
    ):
        self.is_enabled = is_enabled
        self.process_clipboard = process_clipboard
        self.on_redaction = on_redaction

        self.thread = None
        self.hwnd = None

        self.running = False

        self._wnd_proc = None
        self._ready = threading.Event()

        self._last_written_text = None

    # Start background listener
    def start(self):

        if self.running:
            return

        self.running = True
        self._ready.clear()

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="ClipFenceClipboardMonitor"
        )

        self.thread.start()

        # Wait until the listener either starts or fails
        if not self._ready.wait(timeout=5):
            self.running = False
            raise RuntimeError(
                "Clipboard monitor did not start within 5 seconds."
            )

        if self.hwnd is None:
            self.running = False
            raise RuntimeError(
                "Clipboard monitor failed to create its Windows message window."
            )

    # Stop background listener
    def stop(self):

        self.running = False

        if self.hwnd:
            user32.PostMessageW(
                self.hwnd,
                WM_CLOSE,
                0,
                0
            )

        if (
            self.thread
            and self.thread.is_alive()
            and threading.current_thread() != self.thread
        ):
            self.thread.join(timeout=3)

    # Ask the monitor thread to process the current clipboard
    def process_current_clipboard(self):

        if not self.running or not self.hwnd:
            return False

        return bool(
            user32.PostMessageW(
                self.hwnd,
                WM_PROCESS_CURRENT_CLIPBOARD,
                0,
                0
            )
        )

    # Create Windows message window
    def _run(self):

        class_name = "ClipFenceClipboardWindow"

        h_instance = kernel32.GetModuleHandleW(None)

        if not h_instance:
            self._ready.set()
            print("ClipFence: GetModuleHandleW failed.")
            return

        # Keep callback alive for the lifetime of the window
        self._wnd_proc = WNDPROC(
            self._window_proc
        )

        wnd_class = WNDCLASS()

        wnd_class.style = 0
        wnd_class.lpfnWndProc = self._wnd_proc
        wnd_class.cbClsExtra = 0
        wnd_class.cbWndExtra = 0
        wnd_class.hInstance = h_instance
        wnd_class.hIcon = None
        wnd_class.hCursor = None
        wnd_class.hbrBackground = None
        wnd_class.lpszMenuName = None
        wnd_class.lpszClassName = class_name

        atom = user32.RegisterClassW(
            ctypes.byref(wnd_class)
        )

        if not atom:
            error = ctypes.get_last_error()
            self._ready.set()

            print(
                f"ClipFence: RegisterClassW failed. Windows error: {error}"
            )

            return

        try:

            self.hwnd = user32.CreateWindowExW(
                0,
                class_name,
                "ClipFence",
                0,
                0,
                0,
                0,
                0,
                HWND_MESSAGE,
                None,
                h_instance,
                None
            )

            if not self.hwnd:
                error = ctypes.get_last_error()

                print(
                    f"ClipFence: CreateWindowExW failed. Windows error: {error}"
                )

                return

            if not user32.AddClipboardFormatListener(self.hwnd):
                error = ctypes.get_last_error()

                print(
                    f"ClipFence: AddClipboardFormatListener failed. Windows error: {error}"
                )

                return

            print("ClipFence: Windows clipboard listener is active.")

            self._ready.set()

            msg = MSG()

            while self.running:

                result = user32.GetMessageW(
                    ctypes.byref(msg),
                    self.hwnd,
                    0,
                    0
                )

                if result == -1:
                    error = ctypes.get_last_error()

                    print(
                        f"ClipFence: GetMessageW failed. Windows error: {error}"
                    )

                    break

                if result == 0:
                    break

                user32.TranslateMessage(
                    ctypes.byref(msg)
                )

                user32.DispatchMessageW(
                    ctypes.byref(msg)
                )

        finally:

            self._ready.set()

            if self.hwnd:

                user32.RemoveClipboardFormatListener(
                    self.hwnd
                )

                user32.DestroyWindow(
                    self.hwnd
                )

                self.hwnd = None

            user32.UnregisterClassW(
                class_name,
                h_instance
            )

            self._wnd_proc = None

            print("ClipFence: Clipboard listener stopped.")

    # Windows message callback
    def _window_proc(
        self,
        hwnd,
        message,
        w_param,
        l_param
    ):

        if message == WM_CLIPBOARDUPDATE:

            if self.is_enabled():
                self._process()

            return 0

        if message == WM_PROCESS_CURRENT_CLIPBOARD:

            if self.is_enabled():
                self._process()

            return 0

        if message == WM_CLOSE:

            user32.DestroyWindow(hwnd)
            return 0

        if message == WM_DESTROY:

            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(
            hwnd,
            message,
            w_param,
            l_param
        )

    # Process clipboard content
    def _process(self):

        text = self._get_clipboard_text()

        if text is None:
            return

        # Ignore only our own successful redaction update
        if self._last_written_text is not None:

            if text == self._last_written_text:
                self._last_written_text = None
                return

            self._last_written_text = None

        try:

            new_text, count = self.process_clipboard(text)

            if count <= 0:
                return

            if new_text == text:
                return

            success = self._set_clipboard_text(
                new_text
            )

            if success:

                self._last_written_text = new_text

                self.on_redaction(count)

        except Exception as error:

            print(
                f"ClipFence: Clipboard processing error: {error}"
            )

    # Read Unicode text from clipboard
    def _get_clipboard_text(self):

        if not user32.OpenClipboard(None):
            return None

        try:

            if not user32.IsClipboardFormatAvailable(
                CF_UNICODETEXT
            ):
                return None

            handle = user32.GetClipboardData(
                CF_UNICODETEXT
            )

            if not handle:
                return None

            pointer = kernel32.GlobalLock(handle)

            if not pointer:
                return None

            try:

                return ctypes.wstring_at(pointer)

            finally:

                kernel32.GlobalUnlock(handle)

        finally:

            user32.CloseClipboard()

    # Write redacted text to clipboard
    def _set_clipboard_text(self, text):

        if not user32.OpenClipboard(None):
            return False

        memory = None

        try:

            encoded = (
                text.encode("utf-16-le")
                + b"\x00\x00"
            )

            memory = kernel32.GlobalAlloc(
                GMEM_MOVEABLE | GMEM_ZEROINIT,
                len(encoded)
            )

            if not memory:
                return False

            pointer = kernel32.GlobalLock(memory)

            if not pointer:
                return False

            try:

                ctypes.memmove(
                    pointer,
                    encoded,
                    len(encoded)
                )

            finally:

                kernel32.GlobalUnlock(memory)

            if not user32.EmptyClipboard():
                return False

            result = user32.SetClipboardData(
                CF_UNICODETEXT,
                memory
            )

            if not result:
                return False

            # Windows now owns this memory.
            # Do not call GlobalFree after successful SetClipboardData.
            memory = None

            return True

        finally:

            if memory:
                kernel32.GlobalFree(memory)

            user32.CloseClipboard()
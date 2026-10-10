import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

windows = []

def enum_windows_proc(hwnd, lParam):
    if user32.IsWindowVisible(hwnd):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            windows.append((pid.value, hwnd, buff.value))
    return True

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)

for pid, hwnd, title in windows:
    if "Ninja" in title or "Strategy" in title or "Control" in title or pid == 14980:
        print(f"PID: {pid}, HWND: {hwnd}, Title: '{title}'")

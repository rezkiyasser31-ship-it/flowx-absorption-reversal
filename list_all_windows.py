import ctypes
from ctypes import wintypes
import os

user32 = ctypes.windll.user32
windows = []

def enum_windows_proc(hwnd, lParam):
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        windows.append((hwnd, buff.value))
    return True

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)

print(f"Total windows found: {len(windows)}")
for hwnd, title in windows[:20]:
    print(f"HWND: {hwnd}, Title: '{title}'")

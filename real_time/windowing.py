# import psutil
from ctypes import *
from mss import mss, tools
import pygetwindow as gw
import time # For testing purposes only
import json
from pathlib import Path
"""
    for pid in psutil.pids():
        process = psutil.Process(pid)
        if ("AoE" in process.name()):
            process_name = process.name()
"""

def ensure_dpi_aware():
    try:
        windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
def find_game_window():

   game_window = [window for window in gw.getAllTitles() if "Definitive" in window and ("Age of Empires" in window  or "AOE" in window)][0]

   return gw.getWindowsWithTitle(game_window)[0]



user32 = windll.user32

class RECT(Structure):
    _fields_ = [("left", c_long),
                ("top", c_long),
                ("right", c_long),
                ("bottom",c_long)]

class POINT(Structure):
    _fields_ = [("x", c_long),
                ("y", c_long)]

def get_client_rect_screen(window):
    hwnd = window._hWnd

    rect = RECT()
    if not user32.GetClientRect(hwnd, byref(rect)):
        raise WinError()

    # Convert client (0,0) and (w,h) to screen coords
    tl = POINT(0, 0)
    br = POINT(rect.right, rect.bottom)

    if not user32.ClientToScreen(hwnd, byref(tl)):
        raise WinError()
    if not user32.ClientToScreen(hwnd, byref(br)):
        raise WinError()

    left, top = tl.x, tl.y
    width, height = br.x - tl.x, br.y - tl.y
    return (left, top, width, height)

def is_game_focused(hwnd) -> bool:
    print(windll.user32.GetForegroundWindow())
    print(hwnd)
    return hwnd == windll.user32.GetForegroundWindow()





PROFILE_PATH = Path("calibration_profile.json")

def save_profile(profile: dict, path: Path = PROFILE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

def load_profile(path: Path = PROFILE_PATH) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

"""
ensure_dpi_aware()
window = find_game_window()
print(get_client_rect_screen(window))
time.sleep(5)
print(is_game_focused(window._hWnd))

profile = {
  "title_contains": "Definitive",
  "process_name": "AoE2DE_s.exe",
  "capture_rect": get_client_rect_screen(window),
  "dpi_awareness": "per_monitor",
}

save_profile(profile)
coords = get_client_rect_screen(window)
# Test purposes

monitor = {"top": coords[0], "left": coords[1], "width": coords[2], "height": coords[3]}
output = "TEST.png".format(**monitor)
with mss() as sct:
    sct_img = sct.grab(monitor)
    tools.to_png(sct_img.rgb, sct_img.size, output=output)
    print(output)


"""

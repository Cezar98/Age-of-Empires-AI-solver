
from ctypes import *

import pygetwindow as gw

import json
from pathlib import Path



def ensure_dpi_aware():
    try:
        windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

def find_game_window() -> gw.Win32Window:
        ensure_dpi_aware()

        def ok_basic(hwnd) -> bool:
            return bool(user32.IsWindowVisible(hwnd)) and not bool(user32.IsIconic(hwnd))

        def score_title(title: str) -> int:
            t = (title or "").casefold()
            score = 0
            for tok in ("age of empires", "definitive", "edition"):
                if tok in t:
                    score += 10
            if "aoe" in t:
                score += 2
            for tok in ("launcher", "crash", "updater", "settings"):
                if tok in t:
                    score -= 5
            return score

        windows = [w for w in gw.getAllWindows() if w.title and ok_basic(w._hWnd)]

        scored = []
        for w in windows:
            try:
                left, top, width, height = get_client_rect_screen(w)
            except Exception:
                continue
            # reject tiny/utility windows early
            if width < 800 or height < 600:
                continue
            scored.append((score_title(w.title), width * height, w))

        if not scored:
            sample = [w.title for w in windows[:30]]
            raise RuntimeError(f"Game window not found. Sample titles: {sample}")

        fg = user32.GetForegroundWindow()
        fg_scored = [x for x in scored if x[2]._hWnd == fg]

        pool = fg_scored if fg_scored else scored
        # sort by (title score, client area)
        return max(pool, key=lambda x: (x[0], x[1]))[2]




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
    return hwnd == windll.user32.GetForegroundWindow()





PROFILE_PATH = Path("calibration_profile.json")

def save_profile(profile: dict, path: Path = PROFILE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")

def load_profile(path: Path = PROFILE_PATH) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

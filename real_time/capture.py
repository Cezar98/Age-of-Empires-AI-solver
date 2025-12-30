from mss import mss
import time
from windowing import get_client_rect_screen,find_game_window
import numpy as np


def capture_frame():
    t0 = time.perf_counter()
    t = t0
    screen = get_client_rect_screen(find_game_window())
    monitor = {"top": screen[1], "left": screen[0], "width": screen[2], "height": screen[3]}
    print(monitor)
    with mss() as sct:
        while True:
            # Grab the data
            sct_img = sct.grab(monitor)
            last = t


            t = time.perf_counter()
            fps = 1 / (t - last)
            print("FPS: ", fps)
            frame = np.asarray(sct_img)[:, :, :3]  # BGR order
            frame = frame[:, :, ::-1]
            yield (t,frame)


if __name__ == "__main__":
    time.sleep(3)
    frame = capture_frame()
    print(next(frame)[0])

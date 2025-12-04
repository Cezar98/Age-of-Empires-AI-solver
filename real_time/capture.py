from mss import mss
import time

t0 = time.perf_counter()

t = t0
monitor = {"top": 160, "left": 160, "width": 160, "height": 135}
with mss() as sct:
    while t - t0 <= 5:



        # Grab the data
        sct_img = sct.grab(monitor)
        last  = t

        sct.grab(monitor)
        t  = time.perf_counter()
        fps = 1 / (t - last)
        print("FPS: ", fps)

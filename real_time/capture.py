from mss import mss

# The simplest use, save a screenshot of the 1st monitor
with mss() as sct:
    sct.shot()

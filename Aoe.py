# -*- coding: utf-8 -*-
"""
Created on Tue Aug  5 18:30:22 2025

@author: sorin
"""

import pyautogui
import time
import numpy as np


time.sleep(10)  # Switch to AoE in 4 seconds!
screenshot = pyautogui.screenshot()
screenshot.save('aoe_test.png')

# Clicking Villager
pyautogui.moveTo(499, 534)
pyautogui.click()



# Sending a villager  to stone mine
pyautogui.moveTo(1299, 474)
pyautogui.click(button='right')

# Selecting and sending a villager  to gold mine
pyautogui.moveTo(1029, 394)
pyautogui.click(button='left')

pyautogui.moveTo(999, 144)
pyautogui.click(button='right')


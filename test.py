import numpy as np
import matplotlib.pyplot as plt
import argparse
import os
from glob import glob
import pandas as pd
from shapely.ops import polygonize, linemerge
import ezdxf
import tkinter as tk
from PIL import Image


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.canvas_1 = tk.Canvas(width=1400, height=1000)
        self.canvas_1.pack(side="left")


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

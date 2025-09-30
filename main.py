import tkinter as tk
from tkinter import simpledialog
from app import SpacePlannerApp

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    width = simpledialog.askinteger("Room Width", "Enter the width of the room:")
    height = simpledialog.askinteger("Room Height", "Enter the height of the room:")
    if width and height:
        root.deiconify()
        app = SpacePlannerApp(root, width, height)
        root.mainloop()

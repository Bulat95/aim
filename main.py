# main.py
# -*- coding: utf-8 -*-
"""
Точка входа в приложение AI Messenger
"""
import tkinter as tk
from ui.main_window import MainWindow

def main():
    """Запуск приложения."""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()

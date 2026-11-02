"""Main entry point for Phone Keyboard to PC"""
import tkinter as tk
from gui import PhoneKeyboardApp


def main():
    """Main function to start the application"""
    root = tk.Tk()
    app = PhoneKeyboardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


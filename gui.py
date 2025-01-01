import tkinter as tk

# Creates the root window
def create_main_window() -> tk.Tk:
    root = tk.Tk()
    root.title("MTG Card Similarity")
    root.geometry("1200x860")

    return root


if __name__ == "__main__":
    print("WIP")
    root = create_main_window()
    root.mainloop()
import tkinter as tk

# Creates the root window
def create_main_window() -> tk.Tk:
    root = tk.Tk()
    root.title("MTG Card Similarity")
    root.geometry("1200x860")

    return root

# Search bar for navigating cards via card-name
def populate_search_section(master, cards:list):
    search_label = tk.Label(master, text = "Search:")
    search_text = tk.StringVar()
    entry_bar = tk.Entry(master, textvariable=search_text, width=32)
    search_button = tk.Button(master, text="Search", command = lambda: search_cards(cards, search_text) )

    search_label.pack()
    entry_bar.pack()
    search_button.pack()

# Display area for showing cards that the user pinned
def populate_pinned_section():
    pass

# Displays multiple cards that are given to it as a list
def populate_display_section(cards:list) -> None:
    pass

# Shows a card's name, image, oracle text, and a sub window of other cards within it's similarity group
def display_all_card_info(card_json:dict):
    pass

# Given a card's json data, display it's image
def display_card(card_json:dict):
    pass

# Retrieve the card's image from Scryfall
def fetch_image(card_url:str):
    pass

# Simple search by name
def search_cards(cards:list, search_pattern:str) -> list:
    pass


if __name__ == "__main__":
    print("WIP")
    root = create_main_window()
    root.mainloop()
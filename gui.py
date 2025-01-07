import tkinter as tk
import threading
from urllib.request import urlopen, Request
from PIL import ImageTk
import operator

PROGRAM_VERSION = "MTGCardSimilarity/0.1"

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("MTG Card Similarity")


class CardDisplay(tk.Frame):
    def __init__(self, parent:tk.Tk, card_dicts:list):
        super().__init__(parent)

        self.imagelab_frame = tk.Frame(self)
        self.imagelab_frame.pack()

        self.imagelabs = []

        self.card_dicts = card_dicts
        urls = [card.get("image_uris").get("normal") for card in self.card_dicts]

        for _ in urls:
            label = tk.Label(self.imagelab_frame, text="Loading...", width=66, height=42)
            label.pack(side=tk.LEFT, padx=2, pady=2)
            self.imagelabs.append(label)

        self.bind("<<ImagesLoaded>>", self.on_image_loaded)
        threading.Thread(target=getImageFromURLs, args=(urls, self)).start()

    def on_image_loaded(self, event):
        for lab, img in zip(self.imagelabs, self.images):
            lab.config(image=img, text="", width=img.width(), height=img.height())

# Fetches a list of card images from URLs
def getImageFromURLs(urls:list, controller:CardDisplay):
    images = []

    def fetch_next_image(index:int):
        if index < len(urls):
            try:
                for url in urls:
                    req = Request(url, headers = { "User-Agent": PROGRAM_VERSION })
                    images.append(ImageTk.PhotoImage(file=urlopen(req)))

            except Exception as e:
                print(f"Error loading images: {e}")

            # Schedule next image download after 50ms delay - per Scryfall's request
            controller.after(50, fetch_next_image, index + 1)

        # Done fetching images
        else:
            controller.images = images
            controller.event_generate("<<ImagesLoaded>>")

    # Start image fetching
    fetch_next_image(0)


class SearchWidget(tk.Frame):
    def __init__(self, parent:tk.Tk, card_dicts:list):
        super().__init__(parent)
        self.cards = card_dicts
        self.row_index = 0
        self.patterns = []          # List of search to match to
        self.pattern_frames = []    # List of tk.Frames used for displaying patterns

        # Search Inputs
        name_text = tk.StringVar()
        self.add_search_parameter_widget("Name", "name", name_text)
        oracle_text = tk.StringVar()
        self.add_search_parameter_widget("Card Text", "oracle_text", oracle_text)
        type_text = tk.StringVar()
        self.add_search_parameter_widget("Type", "type_line", type_text)
        color_text = tk.StringVar()
        self.add_search_parameter_widget("Colors", "colors", color_text)
        colorid_text = tk.StringVar()
        self.add_search_parameter_widget("Color Identity", "color_identity", colorid_text)
        cmc_text = tk.StringVar()
        self.add_search_parameter_widget("Mana Value / Converted Mana Cost", "cmc", cmc_text, hasCompareOpts=True)

        # Search Patterns
        self.row_index = 1
        search_button = tk.Button(self, text="Search", command = lambda: self.search_cards() )
        search_button.grid(row=self.row_index, column=5, padx=2, pady=2)

        search_button = tk.Button(self, text="Clear Search", command = lambda: self.clear_patterns())
        search_button.grid(row=self.row_index, column=4, padx=2, pady=2)
        self.row_index += 1

    def clear_patterns(self) -> None:
        for _ in range(len(self.patterns)):
            self.remove_pattern_widget(self.patterns[0], self.pattern_frames[0])

    def search_cards(self) -> list:
        matches = []

        for card in self.cards:
            skip : bool = False
            for pattern in self.patterns:
                search_param = pattern["parameter"]

                # Patterns that have a comparison operator:
                if pattern.get("compare_op"):
                    # Call the comparison operator function on the card's value for the given parameter and the search pattern value
                    result : bool = compare(pattern["compare_op"], int(card[search_param]), int(pattern["value"]))
                
                # Color fields:
                elif "color" in search_param:
                    search_colors = parse_colors(pattern["value"])
                    if search_colors:
                        result = all(color in card[search_param] for color in search_colors)
                    # Colorless search must use an empty list
                    else:
                        result = (search_colors == card[search_param])

                # Text-based fields
                else:
                    result = pattern["value"].lower() in card[search_param].lower()

                # Flip result if there's a logical not
                if (pattern["logic_op"] == "not"):
                    result = not result
                
                # Filter out if the result is False
                if (not result):
                    skip = True
            
            if not skip:
                matches.append(card)


        print([match["name"] for match in matches])
        return matches

    # Add a widget that contains a label, entry, and add button
    def add_search_parameter_widget(self, parameter_lab:str, parameter_key:str, strVar:tk.StringVar, hasCompareOpts:bool = False):
        col = 0
        options = [False, False]

        if hasCompareOpts:
            compare_options = ("==", ">=", "<=", ">", "<")
            compare_var = tk.StringVar()
            options[0] = compare_var
            compare_var.set(compare_options[0])
            compare = tk.OptionMenu(self, compare_var, *compare_options)
            compare.grid(row=self.row_index+1, column=col)
        
        logic_options = ("and", "or", "not")
        logic_var = tk.StringVar()
        options[1] = logic_var
        logic_var.set(logic_options[0])
        logic = tk.OptionMenu(self, logic_var, *logic_options)

        label = tk.Label(self, text=parameter_lab, anchor="w")
        entry = tk.Entry(self, textvariable=strVar, width=32)
        add_button = tk.Button(self, text="Add", command=lambda: self.add_search(parameter_key, strVar, options))


        logic.grid(row=self.row_index+1, column=col+1)
        label.grid(row=self.row_index, column=col+2)
        entry.grid(row=self.row_index+1, column=col+2)
        add_button.grid(row=self.row_index+1, column=col+3)

        self.row_index += 2

    # Add a search value to the things to search for
    def add_search(self, parameter_key:str, strVar:tk.StringVar, options:list) -> None:
        compare_val = options[0]        # "==", ">=", "<=", ">", "<"
        logic_val = options[1].get()    # "and", "or", "not"
        
        search_dict = {"parameter": parameter_key, "value" : strVar.get(), "logic_op" : logic_val}

        if compare_val:
            compare_val = compare_val.get()         # Only .get() if compare_val exists
            search_dict["compare_op"] = compare_val

        strVar.set("")  # Clear the entry area
        self.patterns.append(search_dict)
        self.add_pattern_widget(search_dict, column=4)

    def add_pattern_widget(self, pattern:dict, column:int) -> None:
        frame = tk.Frame(self)
        x_button = tk.Button(frame, text="X", command=lambda: self.remove_pattern_widget(pattern, frame))
        label = tk.Label(frame, text=pattern)
        self.pattern_frames.append(frame)

        frame.grid(row=self.row_index, column=column)
        x_button.grid(row=0, column=0)
        label.grid(row=0, column=1)
        self.row_index += 1

    def remove_pattern_widget(self, pattern:dict, frame:tk.Frame) -> None:
        update_index = self.pattern_frames.index(frame)

        self.patterns.remove(pattern)
        self.pattern_frames.remove(frame)

        frame.grid_forget()
        frame.destroy()
        self.row_index -= 1

        self.move_pattern_widgets(update_index)

    def move_pattern_widgets(self, start_idx:int) -> None:
        if len(self.pattern_frames) < start_idx:
            return
        
        for i in range(start_idx, len(self.pattern_frames)):
            self.pattern_frames[i].grid(row=i+2)    # +2 offset to match because row 1 is [Clear Search] button


def compare(comparison_op:str, a:int, b:int) -> bool:
    comparison_ops = {
        "==": operator.eq,
        "!=": operator.ne,
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
    }
    if not comparison_ops.get(comparison_op):
        raise ValueError(f"Invalid operator: '{comparison_op}'")
    return comparison_ops[comparison_op](a, b)

# Parse color-based search terms, returns a list of color abbreviations
def parse_colors(color_pattern : str) -> list:
    colors = {"white":"W", "blue":"U", "red":"R", "black":"B", "green":"G", "colorless":"C"}
    search_colors = set()
    split_pattern = color_pattern.split()

    # Parse colors for searching
    for search_color in split_pattern:
        # Turn "red white" into {"R", "W"}
        if search_color.lower() in colors.keys():
            search_colors.add(colors[search_color.lower()])
        # Turn "UBG" into {"U", "B", "G"}
        else:
            for char in search_color:
                if char in "WUBRGC":
                    search_colors.add(char)
    

    # Colorless can only be searched with an empty color list
    if "C" in search_colors:
        return []
    
    return list(search_colors)

if __name__ == "__main__":
    cards = [{
        "object": "card",
        "name": "Static Orb",
        "released_at": "2001-04-11",
        "uri": "https://api.scryfall.com/cards/86bf43b1-8d4e-4759-bb2d-0b2e03ba7012",
        "scryfall_uri": "https://scryfall.com/card/7ed/319/static-orb?utm_source=api",
        "image_uris": {
            "small": "https://cards.scryfall.io/small/front/8/6/86bf43b1-8d4e-4759-bb2d-0b2e03ba7012.jpg?1562242171",
            "large": "https://cards.scryfall.io/large/front/8/6/86bf43b1-8d4e-4759-bb2d-0b2e03ba7012.jpg?1562242171",
            "normal": "https://cards.scryfall.io/normal/front/8/6/86bf43b1-8d4e-4759-bb2d-0b2e03ba7012.jpg?1562242171",
            "png": "https://cards.scryfall.io/png/front/8/6/86bf43b1-8d4e-4759-bb2d-0b2e03ba7012.png?1562242171",
            "art_crop": "https://cards.scryfall.io/art_crop/front/8/6/86bf43b1-8d4e-4759-bb2d-0b2e03ba7012.jpg?1562242171",
            "border_crop": "https://cards.scryfall.io/border_crop/front/8/6/86bf43b1-8d4e-4759-bb2d-0b2e03ba7012.jpg?1562242171"
        },
        "mana_cost": "{3}",
        "cmc": 3.0,
        "type_line": "Artifact",
        "oracle_text": "As long as Static Orb is untapped, players can't untap more than two permanents during their untap steps.",
        "colors": [],
        "color_identity": [],
        "set_name": "Seventh Edition",
        "collector_number": "319",
        "rarity": "rare",
        "flavor_text": "The warriors fought against the paralyzing waves until even their thoughts froze in place.",
        "artist": "Terese Nielsen",
    },
    {
        "object": "card",
        "name": "Sensory Deprivation",
        "released_at": "2013-07-19",
        "uri": "https://api.scryfall.com/cards/7050735c-b232-47a6-a342-01795bfd0d46",
        "scryfall_uri": "https://scryfall.com/card/m14/71/sensory-deprivation?utm_source=api",
        "image_uris": {
            "small": "https://cards.scryfall.io/small/front/7/0/7050735c-b232-47a6-a342-01795bfd0d46.jpg?1562830795",
            "normal": "https://cards.scryfall.io/normal/front/7/0/7050735c-b232-47a6-a342-01795bfd0d46.jpg?1562830795",
            "large": "https://cards.scryfall.io/large/front/7/0/7050735c-b232-47a6-a342-01795bfd0d46.jpg?1562830795",
            "png": "https://cards.scryfall.io/png/front/7/0/7050735c-b232-47a6-a342-01795bfd0d46.png?1562830795",
            "art_crop": "https://cards.scryfall.io/art_crop/front/7/0/7050735c-b232-47a6-a342-01795bfd0d46.jpg?1562830795",
            "border_crop": "https://cards.scryfall.io/border_crop/front/7/0/7050735c-b232-47a6-a342-01795bfd0d46.jpg?1562830795"
        },
        "mana_cost": "{U}",
        "cmc": 1.0,
        "type_line": "Enchantment \u2014 Aura",
        "oracle_text": "Enchant creature\nEnchanted creature gets -3/-0.",
        "colors": [
        "U"
        ],
        "color_identity": [
        "U"
        ],
        "set_name": "Magic 2014",
        "rarity": "common",
        "flavor_text": "They call it \"stitcher's anesthesia,\" a spell to deaden the senses while the mad doctors begin their grisly work.",
        "artist": "Steven Belledin",
    },
    {
        "object": "card",
        "name": "Road of Return",
        "released_at": "2019-08-23",
        "uri": "https://api.scryfall.com/cards/e718b21b-46d1-4844-985c-52745657b1ac",
        "scryfall_uri": "https://scryfall.com/card/c19/34/road-of-return?utm_source=api",
        "image_uris": {
            "small": "https://cards.scryfall.io/small/front/e/7/e718b21b-46d1-4844-985c-52745657b1ac.jpg?1568003608",
            "normal": "https://cards.scryfall.io/normal/front/e/7/e718b21b-46d1-4844-985c-52745657b1ac.jpg?1568003608",
            "large": "https://cards.scryfall.io/large/front/e/7/e718b21b-46d1-4844-985c-52745657b1ac.jpg?1568003608",
            "png": "https://cards.scryfall.io/png/front/e/7/e718b21b-46d1-4844-985c-52745657b1ac.png?1568003608",
            "art_crop": "https://cards.scryfall.io/art_crop/front/e/7/e718b21b-46d1-4844-985c-52745657b1ac.jpg?1568003608",
            "border_crop": "https://cards.scryfall.io/border_crop/front/e/7/e718b21b-46d1-4844-985c-52745657b1ac.jpg?1568003608"
        },
        "mana_cost": "{G}{G}",
        "cmc": 2.0,
        "type_line": "Sorcery",
        "oracle_text": "Choose one \u2014\n\u2022 Return target permanent card from your graveyard to your hand.\n\u2022 Put your commander into your hand from the command zone.\nEntwine {2} (Choose both if you pay the entwine cost.)",
        "colors": [
        "G"
        ],
        "color_identity": [
        "G"
        ],
        "set_name": "Commander 2019",
        "rarity": "rare",
        "artist": "Jonas De Ro",
    },
    ]
    app = App()
    search_widget = SearchWidget(app, cards)
    display = CardDisplay(app, cards)
    search_widget.pack()
    display.pack()
    app.mainloop()
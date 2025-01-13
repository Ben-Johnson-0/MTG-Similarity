import tkinter as tk
from threading import Thread, Event
from urllib.request import urlopen, Request
from PIL import ImageTk
import operator

PROGRAM_VERSION = "MTGCardSimilarity/0.1"

class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("MTG Card Similarity")
        self.geometry("2004x1100")
        display = CardDisplay(self, cards, cards_per_row=4)
        search_widget = SearchWidget(self, cards, display)
        search_widget.pack()
        display.pack(fill="both", expand=True)


class SimilarityMenu(tk.Frame):
    def __init__(self):
        pass


class CardDisplay(tk.Frame):
    def __init__(self, parent:tk.Tk, card_dicts:list, cards_per_row:int):
        super().__init__(parent)

        self.image_limit = cards_per_row * 4
        self.image_count = 0
        self.num_cards = 0
        self.load_thread = None
        self.pause_event = Event()
        self.pause_event.set()

        self.canvas = tk.Canvas(self, border=5)
        self.scrollbar = tk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)

        self.cards_per_row = cards_per_row
        self.cardlab_frame = tk.Frame(self.canvas, border=1)
        self.cardlab_frame.pack()
        self.cardlabs = [SingleCard(self.cardlab_frame)]    # placeholder card

        self.canvas.bind_all("<MouseWheel>", self.on_scroll)    # Windows and Linux
        self.canvas.bind_all("<Button-4>", self.on_scroll)      # Linux scrolling up
        self.canvas.bind_all("<Button-5>", self.on_scroll)      # Linux scrolling down
        self.cardlab_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.create_window((0,0), window=self.cardlab_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bind("<<CardsChanged>>", self.on_cards_changed)
        self.canvas.bind("<Configure>", self.on_scroll)
        self.set_cards(card_dicts)

    def gen_card_labels(self):
         # Generate up to image_limit labels
        for i in range(self.image_count, min(self.image_limit, self.num_cards)):
            label = SingleCard(self.cardlab_frame)
            label.grid(row = i // self.cards_per_row, column= i % self.cards_per_row, padx=2, pady=2)
            self.cardlabs.append(label)

    def on_cards_changed(self, event):
        # Retrieve the links
        missing_link = "https://cards.scryfall.io/normal/front/a/3/a3da3387-454c-4c09-b78f-6fcc36c426ce.jpg"
        urls = [card.get("image_uris").get("normal") if card.get("image_uris") and card.get("image_uris").get("normal") else missing_link for card in self.card_dicts]

        # Generate card labels
        self.num_cards = len(urls)
        self.gen_card_labels()

        # Set up the thread
        self.pause_event.set()  # Ensure the thread is active
        self.load_thread = Thread(target=self.getImageFromURLs, args=(urls,))
        self.load_thread.daemon = True  # Allow thread to close with the app
        self.load_thread.start()
    
    def set_cards(self, cards:list):
        if type(cards) != list:
            raise ValueError(f"Argument 'cards' must be of type 'list'. set_cards was given '{type(cards)}'.")
        
        self.remove_all_images()
        self.card_dicts = cards
        self.event_generate("<<CardsChanged>>")

    def remove_all_images(self):
        for lab in self.cardlabs:
            lab.grid_forget()
            lab.destroy()
        self.cardlabs = []

    # Fetches a list of card images from URLs
    def getImageFromURLs(self, urls: list):
        def worker():
            index = 0
            while index < len(urls):
                # Wait if the thread is paused
                self.pause_event.wait()

                if index >= self.image_limit:
                    print("Reached image limit, pausing thread")
                    self.pause_event.clear()
                    self.pause_event.wait()  # Pause here until the event is set again

                try:
                    url = urls[index]
                    print(f"Loading image {index + 1}/{len(urls)} from {url}")

                    req = Request(url, headers={"User-Agent": PROGRAM_VERSION})
                    image = ImageTk.PhotoImage(file=urlopen(req))

                    # Assign image to the corresponding label
                    self.cardlabs[index].img = image
                    self.cardlabs[index].event_generate("<<ImageLoaded>>")

                    self.image_count += 1
                    index += 1

                except Exception as e:
                    print(f"Error loading image at index {index}: {e}")
                    index += 1  # Skip to the next image on error

        # Start the worker thread
        self.load_thread = Thread(target=worker, daemon=True)
        self.load_thread.start()

    def on_scroll(self, event=None):
        # Calculate scrollbar position
        pos = self.canvas.yview()[1]  # Position is a tuple (start, end) -> end
        print("pos:", pos)

        # Unpause thread at 90% scroll and limit < number of cards in display's list
        if pos > 0.9 and self.image_limit < self.num_cards:
            print("setting unpause")
            self.image_limit += self.cards_per_row * 4  # Increase the limit
            print("image limit:", self.image_limit)
            self.gen_card_labels()
            self.pause_event.set()  # Unpause the thread if paused


class SingleCard(tk.Frame):
    def __init__(self, parent:tk.Frame):
        super().__init__(parent)

        self.lab = tk.Label(self, text="Loading...", width=66, height=42)
        self.lab.pack()
        self.img = None
        self.bind("<<ImageLoaded>>", self.on_image_loaded)
    
    def on_image_loaded(self, event):
        self.lab.config(image=self.img, text="", width=self.img.width(), height=self.img.height())


class SearchWidget(tk.Frame):
    def __init__(self, parent:tk.Tk, card_dicts:list, card_display:CardDisplay):
        super().__init__(parent)
        self.cards = card_dicts
        self.row_index = 0
        self.patterns = []          # List of search to match to
        self.pattern_frames = []    # List of tk.Frames used for displaying patterns
        self.card_display = card_display

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
        self.card_display.set_cards(matches)
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
    # Quick implementation of card similarity
    # from cardsim import get_card_list, card_similarity, gen_custom_data, save_dict
    # # Calculate card similarity
    # all_cards = get_card_list()                             # Get card list
    # card_names = [entry["name"] for entry in all_cards]     # Get all the card names for later
    # components = card_similarity(all_cards, num_minhashes=144, blocks=24, rows_per_block=6, votes=6, max_rows=500)
    # cards = gen_custom_data(all_cards, components)
    # save_dict(cards, "refined-cards.json")

    import json
    with open("refined-cards.json", "r") as fd:
        cards = json.loads(fd.read())[:180]
        print(len(cards), type(cards))

    app = App()
    app.mainloop()
import tkinter as tk
import threading
from urllib.request import urlopen, Request
from PIL import ImageTk

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

        searchlab = tk.Label(self, text = "Search Parameters")
        search_button = tk.Button(self, text="Search", command = lambda: self.search_cards() )

        namelab = tk.Label(self, text = "Card Name:")
        name_text = tk.StringVar()
        name_bar = tk.Entry(self, textvariable=name_text, width=32)

        oraclelab = tk.Label(self, text = "Card Text:")
        oracle_text = tk.StringVar()
        oracle_bar = tk.Entry(self, textvariable=oracle_text, width=32)

        typelab = tk.Label(self, text = "Card Type:")
        type_text = tk.StringVar()
        type_bar = tk.Entry(self, textvariable=type_text, width=32)

        colorlab = tk.Label(self, text = "Color:")
        color_text = tk.StringVar()
        color_bar = tk.Entry(self, textvariable=color_text, width=32)

        coloridlab = tk.Label(self, text = "Color Identity:")
        colorid_text = tk.StringVar()
        colorid_bar = tk.Entry(self, textvariable=colorid_text, width=32)

        cmclab = tk.Label(self, text = "Mana Value / Converted Mana Cost:")
        cmc_text = tk.StringVar()
        cmc_bar = tk.Entry(self, textvariable=cmc_text, width=32)



        searchlab.pack()
        namelab.pack(padx=2, pady=2)
        name_bar.pack(padx=2, pady=2)
        oraclelab.pack(padx=2, pady=2)
        oracle_bar.pack(padx=2, pady=2)
        typelab.pack(padx=2, pady=2)
        type_bar.pack(padx=2, pady=2)
        colorlab.pack(padx=2, pady=2)
        color_bar.pack(padx=2, pady=2)
        coloridlab.pack(padx=2, pady=2)
        colorid_bar.pack(padx=2, pady=2)
        cmclab.pack(padx=2, pady=2)
        cmc_bar.pack(padx=2, pady=2)
        search_button.pack(side=tk.BOTTOM, padx=2, pady=2)

    def search_cards() -> list:
        # for search_param in search_parameters:
        #     ...
        pass


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
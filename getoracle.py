#!/usr/bin/env python3

import re
import os
import sys
import json

# Clean up the card data and return a list of all nontoken cards
def clean_cards(fname):
    if(not os.path.isfile(fname)):
        print(f"\"{fname}\" is not a file or cannot be found.", file=sys.stderr)
        sys.exit()
    with open(fname, encoding='utf-8') as fd:
        data = json.load(fd)
    results = []

    for x in data:
        # Remove alchemy cards
        if x['name'][:2] == 'A-' or "(cont'd)" in x['name'] or "(minigame)" in x['name']:
            continue
        # Remove art cards
        if '//' in x['name']:
            names = x['name'].split(' // ')
            if names[0] in names[1]:
                continue
        # Remove Tokens
        if 'Token' in x["type_line"]:
            continue
        # print(x["name"])
        # special_chars = "-./\\[]*+?{}|"
        if x.get('card_faces'):
            for face in x['card_faces']:
                face["oracle_text"] = re.sub(r"\(.*\)", '', face["oracle_text"])
                name = re.sub("[\-\.\/\[\]\\\*\+\?\)\{\}\|]", "\\\1", face['name'])
                face["oracle_text"] = re.sub(rf"{name}", '~', face["oracle_text"])
            x['oracle_text'] = '\n//\n'.join([face["oracle_text"] for face in x['card_faces']])
        elif x.get('oracle_text'):
            x["oracle_text"] = re.sub(r"\(.*\)", '', x["oracle_text"])
            name = re.sub("[\-\.\/\[\]\\\*\+\?\{\}\|]", "\\\1", x['name'])
            x["oracle_text"] = re.sub(rf"{name}", '~', x["oracle_text"])
        results.append(x)

    return results


def get_text(card_list):
    print(f"{len(card_list)} cards found.")
    for card in card_list:
        if "Gr\u00edma, Saruman's Footman" in card['name']:
            print(card['name'])
            print(card['oracle_text'])
            break

if __name__ == "__main__":
    cards = clean_cards("clean-oracle-cards-20230713210502.json")
    get_text(cards)

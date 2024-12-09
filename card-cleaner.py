#!/usr/bin/env python3

import os
import sys
import json

# Example use:
# python card-cleaner.py oracle-cards-20230713210502.json

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
        if x['legalities']["commander"] == 'legal':
            results.append(x)

    return results

if __name__ == "__main__":
    if(len(sys.argv) < 2):
        print(f"Usage: {sys.argv[0]} <oracle-cards-file> [<new-file-name>]", file=sys.stderr)
        sys.exit()

    fname = sys.argv[1]

    # Saved clean file name
    save_name = 'clean-'+fname
    if len(sys.argv) > 2:
        save_name = sys.argv[2]
    
    cards = clean_cards(fname)

    with open(save_name, "w+") as fd:
        json_obj = json.dumps(cards, indent=2)
        fd.write(json_obj)
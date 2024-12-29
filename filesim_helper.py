from re import sub
import os
import sys
import json

# Return the set of tuples from a given word list
def kshingles(data:list, k:int = 3) -> set:
    shingles = {tuple(data[i:i+k]) for i in range(len(data)-k-1)}   # set comprehension
    return shingles


# Add some value to a dict if it isn't already there, otherwise increment it
def add_to_dict(key_name:str, dictionary:dict, on_creation:int=1) -> None:
    if (key_name not in dictionary):
        dictionary[key_name] = on_creation
    else:
        dictionary[key_name] += 1


# Input raw oracle-cards file, returns list of 
def clean_cards(fname:str) -> list:
    if(not os.path.isfile(fname)):
        print(f"\"{fname}\" is not a file or cannot be found.", file=sys.stderr)
        sys.exit()
    
    with open(fname, encoding='utf-8') as fd:
        data = json.load(fd)
    
    results = []
    for x in data:

        # Skip cards that are not legal in commander
        if x['legalities']["commander"] != 'legal':
            continue
        
        # Combine multi-faced cards into one oracle text
        if x.get('card_faces'):
            for face in x['card_faces']:
                # Remove reminder text
                face["oracle_text"] = sub(r"\(.*\)", '', face["oracle_text"])
                # Escape special characters from the name
                name = sub(r"[\-\.\/\[\]\\\*\+\?\)\{\}\|]", "\\\1", face['name'])
                # Replace instances of own name with ~
                face["oracle_text"] = sub(rf"{name}", '~', face["oracle_text"])
            x['oracle_text'] = '\n//\n'.join([face["oracle_text"] for face in x['card_faces']])
        
        # Clean normal card's text
        elif x.get('oracle_text'):
            # Remove reminder text
            x["oracle_text"] = sub(r"\(.*\)", '', x["oracle_text"])
            # Escape special characters from the name
            name = sub(r"[\-\.\/\[\]\\\*\+\?\{\}\|]", "\\\1", x['name'])
            # Replace instances of own name with ~
            x["oracle_text"] = sub(rf"{name}", '~', x["oracle_text"])

        results.append(x)

    return results

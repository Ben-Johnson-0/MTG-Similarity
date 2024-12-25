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


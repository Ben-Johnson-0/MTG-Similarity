#!/usr/bin/env python3

# Example run:
# python cardsim.py .\oracle-cards-*.json 144 24 6
#                   oracle-cards-file num-minhashes blocks rows-per-block votes

import filesim_helper as fsh
from oracle_fetcher import get_oracle_json

import os
import sys
import numpy as np
from sympy import primerange
from random import choice, randrange


# Return a list of card dictionaries
def get_card_list(raw_json_file: str | None = None) -> list:
    if raw_json_file == None:
        raw_json_file = get_oracle_json()
    all_cards = fsh.clean_cards(raw_json_file)
    return all_cards

# Given a list of cards, return groups of cards that are strongly connected for similarity
def card_similarity(cards:list, num_minhashes:int, blocks:int, rows_per_block:int, votes:int, max_rows:int) -> dict:
    imp_shingles = imp_shins(all_cards, minVal=4)               # Find all the important shingles that appear atleast minVal times
    mat = generate_shingle_bin_matrix(imp_shingles, cards)      # Apply the characteristic function to all files to make a matrix - each card will have a binary representation for each of the important shingles
    mat = minhash(mat, num_minhashes, max_rows)                 # Minhash the matrix
    sim_mat = sim_vote(mat, votes, blocks, rows_per_block)      # Obtain the adjacency matrix of similar documents

    # Find the strongly connected components:
    components = strongly_connected(sim_mat)
    return components

# Create shingle binary array
def generate_shingle_bin(imp_shingles:dict, card:dict) -> np.array:
    n = len(imp_shingles)
    
    # Error check - empty important shingles dict
    if(n == 0):
        print("Error: Shingle dictionary is empty.", file=sys.stderr)
        sys.exit()
    # Error check - 
    shtype = type(list(imp_shingles.keys())[0])
    if(shtype != tuple):
        print(f"Error: Shingles dictionary keys in type '{shtype}' when they should be of type 'tuple'.", file=sys.stderr)
        sys.exit()

    # Open shingles of given file
    words = card["oracle_text"]
    shins = fsh.kshingles(words, k=3)

    # The output array, 1 = shingle in file, 0 = not
    shin_bin = np.zeros(n, dtype=np.uint8)

    for shin in shins:
        ind = imp_shingles.get(shin)
        if(ind != None):
            shin_bin[ind] = 1

    return shin_bin

# Build the shingle binary matrix from important shingles and the card list
def generate_shingle_bin_matrix(imp_shingles:dict, card_list:list) -> np.array:
    # Build base matrix
    n = len(imp_shingles)
    mat = np.zeros((n,len(card_list)), dtype=np.uint8)

    # Loop through all files in given directory
    for i, card in enumerate(card_list):
        mat[:,i] = generate_shingle_bin(imp_shingles, card)

    return mat

# lambda function generator used for generating random hashing functions for minhash
def randfun(a,b,n):
    return lambda x: (a*x+b) % n

# Move stuff into this function when more settled
def minhash(mat:np.array, num_minhashes:int, max_rows:int) -> np.array:
    n_shingles = mat.shape[0]   # number of shingles
    n_files = mat.shape[1]      # number of files

    # List of odd primes from 2 to n_shingles, used for hashing functions
    oddprimes = np.array(list(primerange(2, n_shingles)))

    minhash_mat = np.empty((num_minhashes, n_files), dtype=np.uint32)

    for k in range(num_minhashes):
        arr = np.empty((max_rows-1, n_files), dtype=np.uint32)
        # Generate hash function using the prime numbers
        fun = randfun(choice(oddprimes),randrange(n_shingles), n_shingles)
        # Use minhash on up to max_rows rows
        for i in range(max_rows-1):
            j = fun(i)      # Permuted index
            arr[i,:] = mat[j,:]

        arr = np.vstack((np.zeros(n_files), arr))
        minhash_mat[k,:] = np.argmax(arr, axis=0)

    return minhash_mat

# Given a minhash matrix construct an adjacency matrix of the cards
#  with edges where there is a vote value of at least reqVotes
def sim_vote(hashmat:np.array, reqVotes:int, blocks:int, rows_per_block:int) -> np.array:
    # Error check for incorrect combinations of number of blocks and number of rows in blocks
    if (blocks*rows_per_block != hashmat.shape[0]):
        print(f"Error: sim_vote(4), blocks*rows_per_block should be equal to hashmat rows.\n"
              f" You had {blocks} blocks and {rows_per_block} rows per block. Hash matrix had {hashmat.shape[0]} rows",
               file=sys.stderr)
        sys.exit()
    
    n_files = hashmat.shape[1]
    adjmat = np.zeros((n_files, n_files))
    hashmat = np.reshape(hashmat, (blocks, rows_per_block, n_files))

    # Loop through the block indices
    for b_ind in range(blocks):
        sim_dict = {}
        # Loop through each column of the block adding the cols to a dictionary with tuple keys
        for col in range(n_files):
            key = tuple(hashmat[b_ind, :, col])
            if (0 in key):
                # Don't count files that have no similarity
                continue
            if (sim_dict.get(key) != None):
                # Add a vote for an edge on each other vertex with a matching tuple
                for x in sim_dict[key]:
                    adjmat[x,col] += 1
                sim_dict[key].append(col)
            else:
                # Create a key, value pair with ind in a list
                sim_dict[key] = [col]

    #Only return the adjmat where the value >= reqVotes
    adjmat = adjmat >= reqVotes             # Convert matrix to Trues and Falses
    return adjmat.astype(np.uint8)          # Convert to 0s and 1s and return it

# Create the undirected version of the graph
def make_undir(adjmat:np.array) -> np.array:
    adjmat = np.add(adjmat, adjmat.T)
    inds = np.nonzero(adjmat)
    undir_adjmat = np.zeros(adjmat.shape, dtype=np.uint8)
    undir_adjmat[inds] = 1
    
    return undir_adjmat

# Given an adjacency matrix, returns a list of all strongly connected components as dictionary, num : list
def strongly_connected(adjmat:np.array) -> dict:
    adjmat = make_undir(adjmat)
    n = adjmat.shape[0]
    visited = np.zeros(n)
    comps = {}
    compNum = -1
    for i in range(n):
        if not visited[i]:
            compNum += 1
            if comps.get(compNum) != None:
                comps[compNum].append(i)
            else:
                comps[compNum]= [i]
            q = [i]
            visited[i] = 1
            while(len(q)):
                w = q.pop(0)
                nbrs = np.nonzero(adjmat[w])[0] # neighbors of w
                for k in nbrs:
                    if not visited[k]:
                        comps[compNum].append(k)
                        visited[k] = 1
                        q.insert(len(q), k)
    return comps


# Create a dictionary of important shingles. Keep only the shingles that appear at least minVal times
def imp_shins(card_list:list, minVal:int = 4) -> dict:
    shin_freq = dict()      # Shingle Frequency
    # Loop through the files retrieving all of our shingles
    for card in card_list:
        words = card["oracle_text"]
        for shin in fsh.kshingles(words, k=3):
            fsh.add_to_dict(shin, shin_freq)

    ordered_shin = dict()
    i = 0
    for k in sorted(shin_freq.keys()):
        if(shin_freq[k] >= minVal):
            fsh.add_to_dict(k, ordered_shin, i)
            i += 1

    print(len(ordered_shin), 'shingles')
    return ordered_shin



if __name__ == "__main__":

    # Default values
    num_minhashes = 144
    blocks = 24
    rows_per_block = 6
    votes = 6
    max_rows = 500

    if("-h" in sys.argv or "--help" in sys.argv):
        print(f"Usage: {sys.argv[0]} [oracle-cards-file] [num-minhashes] [blocks] [rows-per-block]", file=sys.stderr)
        print("'oracle-cards-file' will be automatically retrieved if not found locally.", file=sys.stderr)
        print(f"'num-minhashes' defaults to {num_minhashes}. It must be the result of blocks*rows_per_block.", file=sys.stderr)
        print(f"'blocks' defaults to {blocks}.", file=sys.stderr)
        print(f"'rows_per_block' defaults to {rows_per_block}.", file=sys.stderr)
        print(f"'votes' defaults to {votes}.", file=sys.stderr)
        print(f"'max_rows' defaults to {max_rows}.", file=sys.stderr)
        sys.exit()

    fname = None
    if len(sys.argv) > 1:
        fname = sys.argv[1]
        if(not os.path.isfile(fname)):
            print(f"\"{fname}\" is not a file or cannot be found.", file=sys.stderr)
            sys.exit()
    if(len(sys.argv) > 2):
        num_minhashes = int(sys.argv[2])
    if(len(sys.argv) > 3):
        blocks = int(sys.argv[3])
    if(len(sys.argv) > 4):
        rows_per_block = int(sys.argv[4])

    from statistics import median
    import json


    # Calculate card similarity
    all_cards = get_card_list(fname)                             # Get card list
    card_names = [entry["name"] for entry in all_cards]     # Get all the card names for later
    components = card_similarity(all_cards, num_minhashes, blocks, rows_per_block, votes, max_rows)

    # Collect some data about the components
    n = len(all_cards)
    lt2 = 0         # number of groups of size 1
    max_length = 0
    all_lens = [0] * len(components)
    for key in components.keys():
        comp_len = len(components[key])
        all_lens[int(key)] = comp_len

        # Reunite the cards with their names (they were reduced to indices after generating their characteristic binary representation)
        components[key] = [card_names[x] for x in components[key]]
        
        if comp_len > max_length:
            max_length = comp_len
        if comp_len < 2:
            lt2 += 1

    print(f"\n{len(components)-lt2} groups of size >= 2 found.")
    print(f"{lt2} groups of size < 2 found.")
    print(f"Largest group size: {max_length}")
    print(f"Average group size: {n/len(components):.2f}")
    print(f"Median group size: {median(all_lens)}")

    new_file = "card-similarity.json"
    print(f"\nSaving to '{new_file}'...")
    with open(new_file, "w") as fd:
        json_obj = json.dumps(components, indent=2)
        fd.write(json_obj)
    print("Saved.")

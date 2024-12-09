#!/usr/bin/env python3

# Input:
#   - A directory
# Output:
#   - All connected component groups

# Can be ran with:
# python cardsim.py .\oracle-cards-20221004210230.json 144 24 6
#  vote = 5
VOTES = 6
#  minVal = 4
# oracle-cards-file num-minhashes blocks rows-per-block

from statistics import median
import re
import os
import sys
import json
import numpy as np
import filesim_helper as fsh
from sympy import primerange    # You'll probably need to pip3 install sympy
from random import choice, randrange

# Clean up the card data and return a list of all nontoken cards
def clean_cards(fname):
    if(not os.path.isfile(fname)):
        print(f"\"{fname}\" is not a file or cannot be found.", file=sys.stderr)
        sys.exit()
    with open(fname, encoding='utf-8') as fd:
        data = json.load(fd)
    results = []

    for x in data:
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

def get_cardnames(card_list):
    names = []
    for card in card_list:
        names.append(card["name"])
    return names

# Make shingle binary array
def charfunc(imp_shingles, card):
    n = len(imp_shingles)
    if(n == 0):
        print("Error: Shingle dictionary is empty.", file=sys.stderr)
        sys.exit()
    shtype = type(list(imp_shingles.keys())[0])
    if(shtype != tuple):
        print(f"Error: Shingles dictionary keys in type {shtype} when they should be of type {tuple}.", file=sys.stderr)
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

# Build the charfunc matrix from important shingles and a list of file paths
def all_charfunc(imp_shingles, card_list):
    # Build base matrix
    n = len(imp_shingles)
    mat = np.zeros((n,len(card_list)), dtype=np.uint8)

    # Loop through all files in given directory
    for i, card in enumerate(card_list):
        mat[:,i] = charfunc(imp_shingles, card)

    return mat

# lambda function generator
def randfun(a,b,n):
    return lambda x: (a*x+b) % n

# Move stuff into this function when more settled
def minhash(mat, num_minhashes, max_rows):
    n = mat.shape[0]            # number of shingles
    n_files = mat.shape[1]      # number of files
    oddprimes = np.array(list(primerange(2, n)))

    minhash_mat = np.empty((num_minhashes, n_files), dtype=np.uint32)

    for k in range(num_minhashes):
        arr = np.empty((max_rows-1, n_files), dtype=np.uint32)
        # Generate hash function using the prime numbers
        fun = randfun(choice(oddprimes),randrange(n), n)
        # Use minhash on up to max_rows rows
        for i in range(max_rows-1):
            j = fun(i)      # Permuted index
            arr[i,:] = mat[j,:]

        arr = np.vstack((np.zeros(n_files), arr))
        minhash_mat[k,:] = np.argmax(arr, axis=0)

    return minhash_mat

# Given a minhash matrix construct an adjacency matrix of the files
#  with edges where there is a vote value of at least reqVotes
def sim_vote(hashmat, reqVotes, blocks, rows_per_block):
    if (blocks*rows_per_block != hashmat.shape[0]):
        print(f"Error: sim_vote(4), blocks*rows_per_block should be equal to hashmat rows.\n"
              f" You had {blocks} blocks and {rows_per_block} rows per block. Hash matrix had {hashmat.shape[0]} rows",
               file=sys.stderr)
        sys.exit()
    
    n_files = hashmat.shape[1]                  #number of files
    adjmat = np.zeros((n_files, n_files))
    hashmat = np.reshape(hashmat, (blocks, rows_per_block, n_files))

    # Loop through the blocks
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
def make_undir(adjmat):
    adjmat = np.add(adjmat, adjmat.T)
    inds = np.nonzero(adjmat)
    undir_adjmat = np.zeros(adjmat.shape, dtype=np.uint8)
    undir_adjmat[inds] = 1
# Find all weakly connected components of the graph
    return undir_adjmat

def weakcon(adjmat):
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
def imp_shins(card_list, minVal = 4):
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
    if(len(sys.argv) < 2):
        print(f"Usage: {sys.argv[0]} <oracle-cards-file> <OPTIONAL:num-minhashes> <OPTIONAL:blocks> <OPTIONAL:rows-per-block>", file=sys.stderr)
        sys.exit()

    fname = sys.argv[1]
    if(not os.path.isfile(fname)):
        print(f"\"{fname}\" is not a file or cannot be found.", file=sys.stderr)
        sys.exit()    

    # Default values
    num_minhashes = 96
    blocks = 24
    rows_per_block = 4
    votes = VOTES
    max_rows = 500

    if(len(sys.argv) > 2):
        num_minhashes = int(sys.argv[2])
    if(len(sys.argv) > 3):
        blocks = int(sys.argv[3])
    if(len(sys.argv) > 4):
        rows_per_block = int(sys.argv[4])

    all_cards = clean_cards(fname)                          # Get card list
    card_names = get_cardnames(all_cards)                   # Get all the file paths
    imp_shingles = imp_shins(all_cards, minVal=4)          # Find all the important shingles that appear atleast minVal times
    mat = all_charfunc(imp_shingles, all_cards)             # Apply the characteristic function to all files to make a matrix
    mat = minhash(mat, num_minhashes, max_rows)             # Minhash the matrix
    sim_mat = sim_vote(mat, votes, blocks, rows_per_block)  # Obtain the adjacency matrix of similar documents

    # Turn the adjacency matrix into an adjacency list that can be used with strong
    n = len(all_cards)

    # Find the strongly connected components:
    components = weakcon(sim_mat)
    lt2 = 0
    max_length = 0
    all_lens = [0] * len(components)
    for key in components.keys():
        comp_len = len(components[key])
        all_lens[int(key)] = comp_len
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

    with open("card-similarity.json", "w") as fd:
        json_obj = json.dumps(components, indent=2)
        fd.write(json_obj)

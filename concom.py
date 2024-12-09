#!/usr/bin/env python3

# Testing for a non-recursive function to get the weakly connected components of
#  a directed graph

import sys
import numpy as np

def DFS(adjmat, r):
    scan = np.zeros(adjmat.shape[0])
    stk = []
    stk.insert(0, r)
    while len(stk) > 0:
        i = stk.pop(-1)
        print(i, end=' ')
        if scan[i] == 0:
            scan[i] = 1
            for j in np.nonzero(adjmat[i])[0]:
                stk.insert(0, j)

# Create the undirected version of the graph
def make_undir(adjmat):
    adjmat = np.add(adjmat, adjmat.T)
    inds = np.nonzero(adjmat)
    undir_adjmat = np.zeros(adjmat.shape, dtype=np.uint8)
    undir_adjmat[inds] = 1
    return undir_adjmat

def concom2(adjmat):
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

# ODS Non-recursive DFS Code:
# def DFS(g, r):
#     c = new_array(g.n)
#     s = SLList()
#     s.push(r)
#     while s.size() > 0:
#         i = s.pop()
#         if c[i] == white:
#             c[i] = grey
#             for j in g.out_edges(i):
#                 s.push(j)

A = [
    [0, 0, 1, 0, 0],
    [1, 0, 1, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0]
]
B = [
    [0, 0, 1, 0, 0],
    [1, 0, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 1, 0]
]

A = np.array(A)
B = np.array(B)
print(A)

compA = concom2(A)
compB = concom2(B)

print(compA)
print(compB)
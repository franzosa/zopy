#!/usr/bin/env python

import os
import sys
from random import choice, random, shuffle
from collections import Counter

import numpy as np
import scipy.spatial.distance as spd

import zopy.utils as zu

# ---------------------------------------------------------------
#  helper functions
# ---------------------------------------------------------------

def argmin( function, choices ):
    return sorted( choices, key=function )[0]

def assign( dist, medoids ):
    clusters = {m:[] for m in medoids}
    for i in range( len( dist ) ):
        closest = argmin( lambda x: dist[i][x], medoids )
        clusters[closest].append( i )
    return clusters

def cost( dist, clusters ):
    return sum( [sum( dist[m][ii] ) for m, ii in clusters.items( )] )

# ---------------------------------------------------------------
# main function
# ---------------------------------------------------------------

def kmedoids( data, metric="euclidean", k=3 ):
    dist = spd.squareform( spd.pdist( data, metric ) )
    index = list( range( data.shape[0] ) )
    # start with random medoids
    shuffle( index )
    medoids, others = index[0:k], index[k:]
    clusters = assign( dist, medoids )
    old_cost = cost( dist, clusters )
    iteration = 0
    while True:
        swaps = []
        for im, m in enumerate( medoids ):
            for io, o in enumerate( others ):
                new_medoids = medoids[:]
                new_medoids[im] = o
                new_clusters = assign( dist, new_medoids )
                new_cost = cost( dist, new_clusters )
                swaps.append( [new_cost, [im, io]] )
        best_new_cost, best_swap = sorted( swaps )[0]
        iteration += 1
        zu.say( "iteration:", iteration )
        zu.say( "  medoids:", medoids )
        zu.say( "  oldcost:", old_cost )
        zu.say( "  newcost:", best_new_cost )
        if best_new_cost < old_cost:
            im, io = best_swap
            medoids[im], others[io] = others[io], medoids[im]
            clusters = assign( dist, medoids )
            old_cost = best_new_cost
        else:
            zu.say( "done" )
            break
    assignments = index[:]
    for m, ii in clusters.items( ):
        for i in ii:
            assignments[i] = m
    return medoids, assignments

# ---------------------------------------------------------------
# test
# ---------------------------------------------------------------

if __name__ == "__main__":
    # make some random data with k clusters
    k = 4
    n = 5
    f = 10
    gold = []
    for i in range( k ):
        for j in range( n ):
            gold += [i+1]
    shuffle( gold )
    data = []
    for i, kval in enumerate( gold ):
        data.append( [kval - 0.05 + 0.1 * random( ) for j in range( f )] )
    data = np.array( data )
    print gold
    mm, aa = kmedoids( data, metric="braycurtis", k=k )
    print aa
    cc = Counter( )
    for g, a in zip( gold, aa ):
        cc[g, a] += 1
    print cc

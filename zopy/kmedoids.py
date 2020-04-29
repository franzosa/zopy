#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import random 

import numpy as np
import scipy.spatial.distance as spd

# ---------------------------------------------------------------
# functions
# ---------------------------------------------------------------

def argmin( function, choices ):
    """ return the choice k that minimizes function( k ) """
    return sorted( choices, key=function )[0]

def compute_cost( dist, medoids ):
    """ cost computed as average sample-medoid distance """
    n = len( dist )
    ret = dist[medoids].min( axis=0 ).sum( )
    ret /= n
    return ret
    
def kmedoids( data, metric="euclidean", k=3, seed=1 ):
    """ carry out kmedoids clustering on the 2d numpy array data """
    random.seed( seed )
    dist = spd.squareform( spd.pdist( data, metric ) )
    index = list( range( data.shape[0] ) )
    # 0) start with random medoids
    random.shuffle( index )
    medoids, others = index[0:k], index[k:]
    current_cost = compute_cost( dist, medoids )
    # 1) consider swapping each non-medoid with its medoid
    # 2) identify the best swap
    # 3) if best swap cost is better than current cost, make the swap, repeat 1-3
    # 4) otherwise terminate
    step = 0
    while True:
        step += 1
        print( "iteration {:03d}: cost = {:.3f}".format( step, current_cost ), file=sys.stderr )
        best_cost = None    
        best_swap = None
        for odex, o in enumerate( others ):
            m = argmin( lambda x: dist[o][x], medoids )
            mdex = medoids.index( m )
            medoids[mdex] = o
            swap_cost = compute_cost( dist, medoids )
            if best_cost is None or swap_cost < best_cost:
                best_cost = swap_cost
                best_swap = [mdex, odex]
            medoids[mdex] = m
        if best_cost < current_cost:
            current_cost = best_cost
            mdex, odex = best_swap
            medoids[mdex], others[odex] = others[odex], medoids[mdex]
        else:
            print( "terminated", file=sys.stderr )
            break
    # 5) assign samples to clusters by closest medoid
    assignments = []
    for i in range( len( index ) ):
        assignments.append( argmin( lambda x: dist[i][x], medoids ) )    
    return medoids, assignments

# ---------------------------------------------------------------
# test
# ---------------------------------------------------------------
    
if __name__ == "__main__":
    """ make some 2d data to scatter-check in excel as series """
    k = 9
    n = 1000
    f = 2
    data = [[random.random( ) for i in range( f )] for j in range( n )]
    data = np.array( data )
    mm, cc = kmedoids( data, k=k )
    for row, c in zip( data, cc ):
        row = list( row )
        row = [row[0]] + [""] * mm.index( c ) + [row[1]]
        print( "\t".join( [str( x ) for x in row] ) )
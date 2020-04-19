#!/usr/bin/env python

from __future__ import division

import os
import sys
import re
import argparse

import matplotlib as mpl
mpl.use( "Agg" )
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["font.sans-serif"] = "Arial"
import matplotlib.pyplot as plt

import numpy as np
from scipy.stats import pearsonr, spearmanr
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import MDS, TSNE

from zopy.utils import sortedby, iter_rows, path2name
from zopy.table2 import table
from zopy import mplutils as mu

c_shapes = "osvd^*"

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "table", help="" )
    parser.add_argument( "-l", "--last-metadata", help="" )
    parser.add_argument( "-d", "--dissimilarity", default="braycurtis", help="" )
    parser.add_argument( "-c", "--colorby", nargs=2, help="" )
    parser.add_argument( "-s", "--shapeby", nargs=2, help="" )
    parser.add_argument( "-e", "--level-biplot", nargs="+", default=[], help="" )
    parser.add_argument( "-q", "--quant-biplot", nargs="+", default=[], help="" )
    parser.add_argument( "-o", "--outfile", default="ordination.pdf", help="" )
    parser.add_argument( "-t", "--title", default=None, help="" )
    parser.add_argument( "-m", "--method", choices=["manual", "mds", "nmds", "tsne"], default="manual" )
    args = parser.parse_args()
    return args

def distance_matrix( data, method ):
    # pdist return default is condensed (not square) dist matrix
    dist = squareform( pdist( data, method ) )
    return dist

def flat_upper_tri( matrix ):
    n = len( matrix )
    return np.array( [matrix[i][j] for i in range( n ) for j in range( i+1, n )] )

def get_fit( dist, embedding ):
    ord_dist = squareform( pdist( embedding, "euclidean" ) )
    #r = spearmanr( flat_upper_tri( dist ), flat_upper_tri( ord_dist ) )[0]
    r = pearsonr( flat_upper_tri( dist ), flat_upper_tri( ord_dist ) )[0]
    return r**2
    
def get_varexp( dist, embedding ):
    varexp = []
    dist = flat_upper_tri( dist )
    for dim in embedding.transpose( ):
        dim_dist = []
        n = len( dim )
        for i in range( n ):
            for j in range( i+1, n ):
                dim_dist.append( abs( dim[i] - dim[j] ) )
        r = pearsonr( dist, dim_dist )[0]
        varexp.append( r**2 )
    return varexp

def cmdscale( dist ):
    # number of points
    n = len( dist )
    # centering matrix
    H = np.eye( n ) - np.ones( (n, n) ) / n
    # YY^T
    B = -H.dot( dist**2 ).dot( H )/2
    # diagonalize
    evals, evecs = np.linalg.eigh( B )
    # sort by eigenvalue in descending order
    idx   = np.argsort( evals )[::-1]
    evals = evals[idx]
    evecs = evecs[:,idx]
    # compute the coordinates using positive-eigenvalued components only
    w, = np.where( evals > 0 )
    L  = np.diag( np.sqrt( evals[w] ) )
    V  = evecs[:,w]
    Y  = V.dot( L )
    # done
    return Y, evals

def ordinate_sklearn( dist, method="mds" ):
    if method == "mds":
        Worker = MDS( metric=True, n_components=2, dissimilarity='precomputed', n_init=10, max_iter=1000 )
    elif method == "nmds":
        Worker = MDS( dissimilarity='precomputed', random_state=1701 )
    elif method == "tsne":
        Worker = TSNE( metric='precomputed', perplexity=50 )
    Worker.fit( dist )
    embedding = Worker.embedding_
    # estimate variance explained by each axis
    varexp = get_varexp( dist, embedding )
    # reorder dimensions to match varexp order
    index = sortedby( range( len( varexp ) ), varexp, reverse=True )
    embedding = embedding[:,index]   
    varexp.sort( reverse=True )
    return embedding, varexp, get_fit( dist, embedding )
    
def ordinate_cmdscale( dist ):
    embedding, evals = cmdscale( dist )
    var_exp = evals / sum( evals )
    return embedding, var_exp, get_fit( dist, embedding )
    
def level_biplot( ax, embedding, meta ):
    levels = {}
    for i, m in enumerate( meta ):
        levels.setdefault( m, [] ).append( i )
    for m, index in levels.items( ):
        x = np.median( embedding[index,0] )
        y = np.median( embedding[index,1] )
        ax.text( x, y, m, ha="center", va="center", size=14, alpha=0.5 )

def quant_biplot( ax, embedding, meta, label ):
    norm = 0
    cx, cy = 0, 0
    for x, y, m in zip( embedding[:,0], embedding[:,1], meta ):
        try:
            m = float( m )
            cx += x * m
            cy += y * m
            norm += m
        except:
            continue
    cx /= norm
    cy /= norm
    ax.text( cx, cy, label, ha="center", va="center", size=14, alpha=0.5 )

def colorize( meta, p_cmap, ax ):
    cmap = {}
    for row in iter_rows( p_cmap ):
        print row
        m, c = row
        cmap[m] = c
        if m in meta:
            ax.scatter( [], [], color=c, marker="s", label=m )
    return [cmap.get( m, "black" ) for m in meta]

def shapeize( meta, p_smap, ax ):
    smap = {}
    for row in iter_rows( p_smap ):
        print row
        m, s = row
        smap[m] = s
        if m in meta:
            ax.scatter( [], [], color="black", marker=s, label=m )
    return [smap.get( m, "." ) for m in meta]

def main( ):

    args = get_args( )
    tbl = table( args.table )
    data = tbl.table2array( args.last_metadata ).transpose( )
    dist = distance_matrix( data, args.dissimilarity )

    if args.method == "manual":
        embedding, varexp, goodness = ordinate_cmdscale( dist )
    else:
        embedding, varexp, goodness = ordinate_sklearn( dist, method=args.method )
        
    fig = plt.figure()
    fig.set_size_inches( 10, 6 )
    ax = plt.subplot( 111 )
    xcoords = embedding[:, 0]
    ycoords = embedding[:, 1]

    shapes = ["o" for x in xcoords]
    if args.shapeby is not None:
        field, path = args.shapeby
        shapes = shapeize( tbl.row( field ), path, ax )     
    
    colors = ["black" for x in xcoords]
    if args.colorby is not None:
        field, path = args.colorby
        colors = colorize( tbl.row( field ), path, ax )
        
    for x, y, c, s in zip( xcoords, ycoords, colors, shapes ):
        ax.scatter( x, y, color=c, marker=s )
    ax.set_xlim( min( xcoords ), max( xcoords ) )
    ax.set_ylim( min( ycoords ), max( ycoords ) )
    mu.funcMargin( ax )

    title = path2name( args.table ) if args.title is None else args.title
    ax.set_title( "%s | Goodness of fit = %.3f" % ( title, goodness ) )
    ax.set_xlabel( "Dimension 1 (%.1f%%)" % (100 * varexp[0] ) )
    ax.set_ylabel( "Dimension 2 (%.1f%%)" % (100 * varexp[1] ) )
    mu.funcSetTickParams( ax )

    for m in args.level_biplot:
        level_biplot( ax, embedding, tbl.row( m ) )
    for m in args.quant_biplot:
        quant_biplot( ax, embedding, tbl.row( m ), m )

    # Shrink current axis by 20%
    box = ax.get_position( )
    ax.set_position( [box.x0, box.y0, box.width * 0.7, box.height] )

    ax.legend( scatterpoints=1,
               fontsize=8,
               loc='center left',
               bbox_to_anchor=(1, 0.5),
               )
               
    #plt.tight_layout( )
    plt.savefig( args.outfile )
    
if __name__ == "__main__":
    main( )

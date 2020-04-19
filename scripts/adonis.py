#!/usr/bin/env python

import os
import sys
import re
import argparse
import random
from collections import Counter

import numpy as np
from zopy.utils import warn
from scipy.stats import pearsonr, spearmanr
from scipy.spatial.distance import pdist, squareform
import rpy2.robjects as ro

from zopy.table2 import table

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "table", help="" )
    parser.add_argument( "-l", "--last-metadata", help="" )
    parser.add_argument( "-s", "--select", nargs=2, help="" )
    parser.add_argument( "-g", "--groups", required=True, help="" )
    parser.add_argument( "-d", "--dissimilarity", default="braycurtis", help="" )
    args = parser.parse_args( )
    return args

def adonis( features, groups ):
    vals = {k:ro.FloatVector( row ) for k, row in features.iter_rows( )}
    vals = ro.DataFrame( vals )
    ro.globalenv["vals"] = vals
    meta = {"groups": ro.FactorVector( groups )}
    meta = ro.DataFrame( meta )
    ro.globalenv["meta"] = meta
    ro.r( "library('vegan')" )
    results = ro.r( "adonis( vals ~ groups, meta, method='bray', permutations=10000 )" )
    # convert R results to table
    """
    colheads = ["Df", "Sum Sq", "Mean Sq", "F value", "Pr( >F )"]
    rowheads = [factor1name, "error"]
    ndictData = {}
    for rowhead in results.keys():
        for index, name in zip( range( len( rowheads ) ), rowheads ):
            dictName = ndictData.setdefault( name, {} )
            dictName[rowhead] = results[rowhead][index]
            # return as zopy table
            return nesteddict2table( ndictData, rowheads, colheads )
    """
    print results
 
def main( ):
    args = get_args( )
    T = table( args.table )
    if args.select is not None:
        T.select( args.select[0], args.select[1], transposed=True )
    groups = T.row( args.groups )
    if args.last_metadata is not None:
       m, T = T.metasplit( args.last_metadata )
    T.float( )
    adonis( T, groups )

if __name__ == "__main__":
    main( )

#! /usr/bin/env python

import os, sys, re, glob, argparse
import random
from numpy import mean, std
from collections import Counter

def kmerize( string, k=2 ):
    counts = Counter()
    for i in range( 0, len( string ) - k + 1 ):
        kmer = string[i:i+k]
        counts[kmer] += 1
    return counts

def wordize( string ):
    counts = Counter()
    for word in string.split():
        counts[word] += 1
    return counts

def clean_string( string ):
    string = re.sub( "[^a-z0-9]", " ", string.lower() )
    return re.sub( " +", " ", string )

def compare( string1, string2, func=kmerize, cleaned=True, local=False ):
    """ computes something like a jaccard similarity for strings """
    if cleaned:
        string1 = clean_string( string1 )
        string2 = clean_string( string2 )
    # get counts
    counts1 = func( string1 )
    counts2 = func( string2 )
    atoms = set( counts1.keys() ).__or__( set( counts2.keys() ) )
    counts1 = { k:counts1[k] if k in counts1 else 0 for k in atoms }
    counts2 = { k:counts2[k] if k in counts2 else 0 for k in atoms }
    # compare
    total1 = sum( counts1.values() )
    total2 = sum( counts2.values() )
    shared = sum( [ min( counts1[k], counts2[k] ) for k in atoms ] )
    normalizer = max( total1, total2 ) if not local else min( total1, total2 )
    return shared / float( normalizer )

def shuffle_string( string ):
    aString = [k for k in string]
    random.shuffle( aString )
    return "".join( aString )

def expectation( string1, string2, func=kmerize, cleaned=True, trials=100 ):
    values1 = []
    values2 = []
    for i in range( trials ):
        r1 = shuffle_string( string1 )
        r2 = shuffle_string( string2 )
        v1, v2 = compare( r1, r2, func=func, cleaned=cleaned )
        values1.append( v1 )
        values2.append( v2 )
    return mean( values1 ), mean( values2 )

if __name__ == "__main__":
    a = "ABCD"
    b = "AB"
    compare( a, b )

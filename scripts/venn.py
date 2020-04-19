#!/usr/bin/env python

import os
import sys
import re
import argparse

import zopy.utils as zu

# argument parsing (python argparse)
parser = argparse.ArgumentParser( )
parser.add_argument( "path1" )
parser.add_argument( "path2" )
parser.add_argument( "--field1", type=int, default=1 )
parser.add_argument( "--field2", type=int, default=1 )
parser.add_argument( "--unique", action="store_true" )
args = parser.parse_args( )

def loader( path, field ):
    ret = set( )
    cc = {}
    for row in zu.iter_rows( path ):
        key = row[field - 1]
        if not args.unique:
            cc[key] = cc.get( key, 0 ) + 1
            key = tuple( [key, cc[key]] )
        ret.add( key )
    return ret

set1 = loader( args.path1, args.field1 )
set2 = loader( args.path2, args.field2 )

zu.tprint( "|set1| =", len( set1 ) )
zu.tprint( "|set2| =", len( set2 ) )
zu.tprint( "|set1 unique| =", len( set1 - set2 ) )
zu.tprint( "|set2 unique| =", len( set2 - set1 ) )
zu.tprint( "|set1 AND set2| =", len( set2.__and__( set1 ) ) )
zu.tprint( "|set1 OR set2| =", len( set2.__or__( set1 ) ) )
zu.tprint( "|set1 XOR set2| =", len( set2.__xor__( set1 ) ) )

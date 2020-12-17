#!/usr/bin/env python

"""
Use zopy.kmers to compare fasta files
-----------------------------------------------
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

import os
import sys
import argparse

import zopy.utils as zu
from zopy.kmers import Index
from zopy.bio import read_fasta

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "fasta1" )
    parser.add_argument( "fasta2" )
    parser.add_argument( "-t", "--top", default=1, type=int )
    parser.add_argument( "-l", "--local", action="store_true" )
    parser.add_argument( "-k", "--k-size", default=3, type=int )
    parser.add_argument( "-c", "--compress", default=None, type=float )
    return parser.parse_args( )

if __name__ == "__main__":
	args = get_args( )
	zu.say( "Loading fasta1" )
	fasta1 = read_fasta( args.fasta1 )
	zu.say( "Loading fasta2" )
	fasta2 = read_fasta( args.fasta2 )
	zu.say( "Indexing fasta2" )
	I = Index( k=args.k_size )
	I.update_from_dict( fasta2 )
	if args.compress:
		zu.say( "Compressing index" )
		I.compress( args.compress )
	zu.say( "Searching" )
	for i, name1 in enumerate( fasta1 ):
		seq = fasta1[name1]
		hits = I.score( seq, top=args.top, local=args.local )
		for hit in hits:
			zu.tprint( 
				i + 1,
				len( fasta1 ),
				name1,
				hit[0],
				round( hit[2], 3 ),
				)
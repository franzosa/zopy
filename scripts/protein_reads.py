#!/usr/bin/env python

"""
Make DNA reads from proteins
===============================================
* Loads proteins from FASTA
* Samples peptides (~reads) proportional to length
* Selects sites to mutate inversely proportional to exp( blosum62[x][x] )
* Chooses new residue proportional to exp( blosum62[x][y] ); x != y
* Converts mutated peptide to compatible DNA sequence
* Picks random reading frame
===============================================
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

import sys
import re
import argparse
import math
import random
from string import uppercase

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SubsMat.MatrixInfo import blosum62
from Bio.Data import CodonTable

from zopy.stats import WeightedChooser
from zopy.dictation import col2dict

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

c_good_aas = re.sub( "[BOJUXZ]", "", uppercase )

c_self_score = {}
c_exchange_scores = {}
for ( aa1, aa2 ), value in blosum62.items( ):
    if aa1 in c_good_aas and aa2 in c_good_aas:
        if aa1 != aa2:
            c_exchange_scores.setdefault( aa1, {} )[aa2] = math.exp( value )
            c_exchange_scores.setdefault( aa2, {} )[aa1] = math.exp( value )
        else:
            # higher self score should be mutated less, hence negative
            c_self_score[aa1] = math.exp( -value )
# convert exchanges to WeightedChooser objects
c_choosers = {}
for aa, weights in c_exchange_scores.items( ):
    c_choosers[aa] = WeightedChooser( weights )

# process codon table
c_codons = {}
for codon, aa in CodonTable.unambiguous_dna_by_name["Standard"].forward_table.items():
    if aa in c_good_aas:
        c_codons.setdefault( aa, [] ).append( codon )

# ---------------------------------------------------------------
# functions
# ---------------------------------------------------------------

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( 
        "faa", 
        help="fasta of protein sequences", )
    parser.add_argument( 
        "--reads", 
        default=1000, 
        type=int, 
        help="how many reads to make", )
    parser.add_argument( 
        "--pident",              
        default=100, 
        type=float, 
        help="percent identity", )
    parser.add_argument( 
        "--readlen", 
        default=100, 
        type=int, 
        help="read length", )
    parser.add_argument( 
        "--weights",
        help="optional weights for proteins", )
    return parser.parse_args( )

def load_faa( path, frag_len ):
    """ load faa to dict; filter bad proteins """
    faa = {}
    bad_count = 0
    with open( path ) as fh:
        for record in SeqIO.parse( fh, "fasta" ):
            seq = str( record.seq )
            # exclude seqs matching a NOT good AA
            if not re.search( "[^%s]" % c_good_aas, seq ) and len( seq ) >= frag_len:
                faa[record.name] = seq
            else:
                bad_count += 1
    names = faa.keys()
    print >>sys.stderr, "skipped %d bad sequences (bad aa OR too short); %d remain" \
        % ( bad_count, len( names ) )
    return faa

def mutate_protein( seq, mut_rate ):
    """ mutate the sequence string """
    seq_len = len( seq )
    muts = int( mut_rate * seq_len )
    seq = [k for k in seq]
    # part 1: pick the sites to mutate based on their relative mutability
    site_weights = {k:c_self_score[seq[k]] for k in range( seq_len )}
    wc = WeightedChooser( site_weights )
    sites_to_mutate = {}
    while len( sites_to_mutate ) < muts:
        sites_to_mutate[wc.choice( )] = 1
    # part 2: make sensible mutations at those sites
    for site in sites_to_mutate:
        seq[site] = c_choosers[seq[site]].choice()
    new_seq = "".join( seq )
    return new_seq

def prot_to_dna( prot_seq ):
    """ create non-biological CDS by joining random compatible codons """
    return "".join( [random.choice( c_codons[aa] ) for aa in prot_seq] )

def reverse_complement( dna ):
    """ reverse complement DNA sequence """
    return str( Seq( dna ).reverse_complement( ) )

def rand_read( prot_seq, prot_name, read, read_len, frag_len, mut_rate ):
    """ create a single random read from a given protein sequence """
    prot_len = len( prot_seq )
    start = random.choice( range( prot_len - frag_len + 1 ) )
    prot_frag = prot_seq[start:start+frag_len]
    # mutate?
    if mut_rate > 0:
        prot_frag = mutate_protein( prot_frag, mut_rate )
    dnaread = prot_to_dna( prot_frag )
    frame = random.choice( range( 3 ) )
    dnaread = dnaread[frame:frame+read_len]
    # reverse complement?
    strand = "+"
    if random.random() < 0.5:
        dnaread = reverse_complement( dnaread )
        strand = "-"
    # format
    print ">protein_read|%08d|%04d|%s%d|%s" % ( read, start+1, strand, frame, prot_name )
    print dnaread

# ---------------------------------------------------------------
# make reads
# ---------------------------------------------------------------

def main( ):
    args = get_args()
    # derived args
    path_faa = args.faa
    total_reads = args.reads
    pident = args.pident
    if pident > 1:
        print >>sys.stderr, "interpret", pident, "as percent;",
        pident /= 100.0
        print >>sys.stderr, "fractional value is", pident
    mut_rate = 1 - pident
    read_len = args.readlen
    frag_len = int( math.ceil( read_len / 3.0 ) )
    # load proteins
    faa = load_faa( path_faa, frag_len )
    # initialize weights to effective protein lengths
    weights = {k:(len( v ) - frag_len + 1) for k, v in faa.items( )}
    # augment weights?
    if args.weights:
        weights2 = col2dict( args.weights, value=1, func=float )
        weights = {k:v * weights2.get( k, 0 ) for k, v in weights.items( )}
    # make the chooser
    wc = WeightedChooser( weights )
    # make the reads (weighting by protein length)
    read = 0
    for prot_name in wc.iter_choice( total_reads ):
        read += 1
        prot_seq = faa[prot_name]
        rand_read( prot_seq, prot_name, read, read_len, frag_len, mut_rate )

if __name__ == "__main__":
    main( )

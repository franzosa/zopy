#! /usr/bin/env python

import os, sys, re, glob, argparse, csv
from numpy import median, mean, std

# ---------------------------------------------------------------
# arguments
# ---------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument( 
    "input", help="sorted, tabular input file (focus on rowheads; top=high)",
)
parser.add_argument( 
    "-k", "--kmer_size", 
    default=4, 
    type=int, 
    help="kmer size",
)
parser.add_argument( 
    "-w", "--use_words", 
    action="store_true", 
    help="use words instead of kmers",
)
parser.add_argument( 
    "-r", "--reversed", 
    action="store_true", 
    help="list is reversed (treat bottom as high)",
)
parser.add_argument( 
    "-s", "--simplify", 
    action="store_true", 
    help="lowercase, remove all but [a-z0-9]",
)
parser.add_argument( 
    "-c", "--min_count", 
    default=7, 
    type=int, 
    help="min atom (kmer/word) count",
)
parser.add_argument( 
    "-j", "--min_sim", 
    default=0.8, 
    type=float,
    help="local jaccard similarity for cluster merger",
)
parser.add_argument( 
    "-e", "--extent", 
    default=0.1, 
    type=float, 
    help="how deep to got into ranked list",
)
parser.add_argument( 
    "-L", "--exclude_low", 
    action="store_true", 
    help="ignore the low tail of the distribution", 
)
parser.add_argument( 
    "-H", "--exclude_high", 
    action="store_true", 
    help="ignore the high tail of the distribution",
)
args = parser.parse_args()

# ---------------------------------------------------------------
# utilities
# ---------------------------------------------------------------

def overlap_score ( set1, set2 ):
    """ determines if one set overlaps with another """
    shared = len( set1.__and__( set2 ) )
    # regular jaccard
    # return shared / float( len( set1.__or__( set2 ) ) )
    # semi-global jaccard
    return shared / float( min( len( set1 ), len( set2 ) ) )

def describe_median_rank ( m ):
    """ qualitative description of median normalized ranks """
    cuts = [0.05, 0.2, 0.4, 0.6, 0.8, 0.95, 1.0]
    names = ["very low", "low", "medium low", "trivial", "medium high", "high", "very high"]
    for cut, name in zip( cuts, names ):
        if m < cut:
            return name

# ---------------------------------------------------------------
# load the file
# ---------------------------------------------------------------

terms = []
atom_ranks = {}
atom_terms = {}
term_ranks = {}

with open( args.input ) as fh:
    for row in csv.reader( fh, dialect="excel-tab" ):
        terms.append( row[0] )
tcount = len( terms )
for term_rank, term in enumerate( terms ):
    # adjust to base-1 numbering
    # convert to normalized rank with 1=highest
    term_rank = 1 - ( term_rank + 1 ) / float( tcount )
    if args.reversed:
        term_rank = 1 - term_rank
    term_ranks[term] = term_rank
    if args.simplify:
        term = term.lower()
        term = re.sub( "[^a-z0-9]", " ", term )
        term = re.sub( " +", " ", term )
    atoms = term.split( " " ) if args.use_words else \
        [term[i:i+args.kmer_size] for i in range( 0, len( term ) - args.kmer_size + 1 )]
    for atom in atoms:
        atom_ranks.setdefault( atom, [] ).append( term_rank )
        atom_terms.setdefault( atom, [] ).append( term )

# ---------------------------------------------------------------
# identify the best atoms
# ---------------------------------------------------------------

atom_score = {}
for atom, ranks in atom_ranks.items():
    if len( ranks ) >= args.min_count:
        atom_score[atom] = median( ranks )

# clip the interesting ends of the atom list
ranked_atoms = sorted( atom_score.keys(), key=lambda x: atom_score[x], reverse=True )
limit = int( len( atom_score ) * args.extent )
high = ranked_atoms[0:limit] if not args.exclude_high else []
low  = ranked_atoms[-limit:] if not args.exclude_low else []
ranked_atoms = high + low

# ---------------------------------------------------------------
# merge atom clusters based on similar rank + term co-membership
# ---------------------------------------------------------------

clusters = []
cluster_terms = []
for atom in ranked_atoms:
    terms = set( atom_terms[atom] )
    # note: range( 0 ) returns [], so we execute the for..else if:
    # 1) the cluster list is empty (base case)
    # 2) we failed to hit an existing cluster 
    for i in range( len( clusters ) ):
        if overlap_score( terms, cluster_terms[i] ) >= args.min_sim:
            clusters[i].append( atom )
            cluster_terms[i] = cluster_terms[i].__or__( terms )
            break
    else:
        clusters.append( [atom] )
        cluster_terms.append( terms )

# ---------------------------------------------------------------
# output to screen
# ---------------------------------------------------------------

print """Note:
MRANK if the average ( normalized ) rank of terms within the group
MRANK 1.0 is the exact top of the list
MRANK 0.5 is the exact middle
MRANK 0.0 is the exact bottom
"""

for i in range( len( clusters ) ):
    # compute median median rank
    med_score = median( [atom_score[k] for k in clusters[i]] )
    print "+----------------------------------------------"
    print "| GROUP : %05d" % ( i+1 )
    print "| MRANK : %.3f ( %s )" % ( med_score, describe_median_rank( med_score ) )
    # print atoms
    print "| ATOMS :"
    for atom in clusters[i]:
        print "\t%s\tmedrank=%.3f\tN=%d" % ( atom, atom_score[atom], len( atom_ranks[atom] ) )
    # print terms
    print "| TERMS :"
    for term in sorted( cluster_terms[i], key=lambda term: term_ranks[term], reverse=True ):
        print "\t%.3f\t%s" % ( term_ranks[term], term )
    print

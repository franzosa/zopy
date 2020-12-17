#!/usr/bin/env python

import re
import random
from collections import Counter

from numpy import mean

#-------------------------------------------------------------------------------
# utility methods
#-------------------------------------------------------------------------------

def shuffle_text( text ):
    text = [k for k in text]
    random.shuffle( text )
    return "".join( text )

def kmerize( text, k=3, case=False, symbols=False ):
    counts = Counter( )
    if not case:
        text = text.lower( )
    if not symbols:
        # collapse non-word chars
        text = re.sub( "\W+", "_", text )
    for i in range( len( text ) - k + 1 ):
        counts[text[i:i+k]] += 1
    return counts

def compare( text1, text2, k=3, case=False, symbols=False, local=False ):
    # shared with kmerize
    kwargs = {"k": k, "case": case, "symbols": symbols}
    # get counts
    counts1 = kmerize( text1, **kwargs )
    counts2 = kmerize( text2, **kwargs )
    # compare counts
    kmer_space = set( counts1 ).union( set( counts2 ) )
    shared = 0
    for kmer in kmer_space:
        shared += min( counts1.get( kmer, 0 ), counts2.get( kmer, 0 ) )
    total1 = sum( counts1.values( ) )
    total2 = sum( counts2.values( ) )
    # smaller total if local, otherwise bigger
    background = sorted( [total1, total2] )[0 if local else 1]
    return shared / float( background )

def pcompare( text1, text2, k=3, case=False, symbols=False, local=False, trials=100 ):
    # shared with kmerize
    kwargs = {"k": k, "case": case, "symbols": symbols}
    # get the real similarity
    real = compare( text1, text2, **kwargs )
    # computed random similarities
    perms = []
    for i in range( trials ):
        text1 = shuffle_text( text1 )
        text2 = shuffle_text( text2 )
        perms.append( compare( text1, text2, **kwargs ) )
    # determine significance and effect size
    pval = sum( [1 / float( trials ) for k in perms if k >= real] )
    fold = real / mean( perms )
    return real, fold, pval
    
#-------------------------------------------------------------------------------
# index class for efficient repeated search
#-------------------------------------------------------------------------------
    
class Index( ):

    def __init__( self, k=3, case=False, symbols=False ):
        # flags needed for kmerize
        self.k = k
        self.kwargs = {"k": k, "case": case, "symbols": symbols}
        # allows numerical indexing of the texts (tdex -> text)
        self.texts = []
        # kmer lengths of the tests (sum of allowed kmers in text)
        self.klens = []
        # mapping from tdex to name
        self.names = {}
        # mapping from kmer to tdex to counts
        self.index = {}
        # original kmer space (before possible compression)
        self.space = set( )
        # current compression status (% of kmers kept)
        self.compression = 1.0
            
    def add( self, text, name=None ):
        """ add a text to the index """
        counts = kmerize( text, **self.kwargs )
        self.texts.append( text )
        self.klens.append( sum( counts.values( ) ) )
        tdex = len( self.texts ) - 1
        self.names[tdex] = name
        # update kmer dicts with counts from this tdex
        for kmer, count in counts.items( ):
            self.space.add( kmer )
            inner = self.index.setdefault( kmer, Counter( ) )
            inner[tdex] += count
            
    def update( self, texts ):
        for text in texts:
            self.add( text )

    def update_from_dict( self, texts ):
        for name, text in texts.items( ):
            self.add( text, name=name )

    def compress( self, factor=0.1 ):
        """ remove a subset of the index space; updates lengths """
        self.compression *= factor
        self.index = {k:v for k, v in self.index.items( ) if random.random( ) <= factor}
        self.klens = [0 for k in self.klens]
        for kmer, tcounts in self.index.items( ):
            for tdex, tcount in tcounts.items( ):
                self.klens[tdex] += tcount
            
    def score( self, query, top=10, local=False ):
        """ score a query against the texts index """
        counts = kmerize( query, **self.kwargs )
        scores = Counter( )
        qlen = 0
        # determine query length; score text overlaps
        for kmer, qcount in counts.items( ):
            qlen += qcount
            if kmer not in self.index:
                # discount kmer lost from original space due to compression
                if kmer in self.space:
                    qlen -= qcount
                # discount new kmer as if it were compressed out
                elif random.random( ) > self.compression:
                    qlen -= qcount
                continue
            for tdex, tcount in self.index[kmer].items( ):
                scores[tdex] += min( qcount, tcount )
        # normalize overlaps
        for tdex, overlap in scores.items( ):
            tlen = self.klens[tdex]
            # smaller total if local else bigger
            norm = sorted( [qlen, tlen] )[0 if local else 1]
            overlap /= float( norm )
            scores[tdex] = overlap
        # return best hits
        ret = []
        for tdex in sorted( scores, key=lambda x: -scores[x] ):
            ret.append( [self.names[tdex], self.texts[tdex], scores[tdex]] )
            if len( ret ) == top:
                break
        return ret
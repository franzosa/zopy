#!/usr/bin/env python

import os
import sys
from collections import Counter

import zopy.utils as zu

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

"""
CR931997.1
Prodigal_v2.6.3
CDS
1
1752
220.0
+
0
ID=1_1;partial=10;start_type=Edge;rbs_motif=None;rbs_spacer=None;...;
"""

c_gff_fields = [
    ["seqname"    , str],
    ["source"     , str],
    ["feature"    , str],
    ["start"      , int],
    ["end"        , int],
    ["score"      , float],
    ["strand"     , str],
    ["frame"      , str],
    ["attributes" , str],
]

# ---------------------------------------------------------------
# gff file object
# ---------------------------------------------------------------

class GFF( ):

    def __init__( self, path ):
        self.loci = []
        counter = 0
        for row in zu.iter_rows( path ):
            if row[0][0] != "#":
                counter += 1
                self.loci.append( Locus( row, counter ) )        
                
    def iter_loci( self ):
        for L in self.loci:
            yield L

    def iter_contig_loci( self ):
        contig, contig_loci = None, []
        for L in self.loci:
            if contig is not None and L.seqname != contig:
                yield contig, contig_loci
                contig_loci = []
            contig = L.seqname
            contig_loci.append( L )
        # last case cleanup
        yield contig, contig_loci

# ---------------------------------------------------------------
# gff line object (locus)
# ---------------------------------------------------------------

class Locus( ):

    def __init__( self, gff_row, counter ):
        # unique tag for locus based on position in GFF
        self.index = counter
        # gff fields
        if len( gff_row ) != len( c_gff_fields ):
            zu.die( "Bad GFF row:", gff_row )
        for [fname, ftype], value in zip( c_gff_fields, gff_row ):
       	    setattr( self, fname, ftype( value ) if value != "." else value )
        # attributes
        temp = {}
        for item in self.attributes.split( ";" ):
            if "=" not in item:
                continue
            item = item.strip( )
            system, value = item.split( "=" )
            if system in temp:
                zu.say( "Warning: Multiple definitions for system", system )
            temp[system] = value
        self.attributes = temp
        # no name by default
        self.name = self.attributes.get( "ID", None )
        self.code = ":".join( [str( self.start ), str( self.end ), self.strand] )
        
    def __repr__( self ):
        items = [self.__dict__[k[0]] for k in c_gff_fields]
        # reformat attributes
        items[-1] = ""
        for k in sorted( self.attributes, key=lambda x: [0 if x == "ID" else 1, x] ):
            items[-1] += "{}={};".format( k, self.attributes[k] )
        return "\t".join( [str( k ) for k in items] )
        
    def __len__( self ):
        return abs( self.end - self.start ) + 1

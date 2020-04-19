#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import re
from collections import OrderedDict

from Bio import SeqIO

from zopy.utils import try_open, say, die

# ---------------------------------------------------------------
# fasta
# ---------------------------------------------------------------

def read_fasta( path, full_headers=False ):
    fdict = OrderedDict( )
    with try_open( path ) as fh:
        for line in fh:
            line = line.strip( )
            if line[0] == ">":
                header = line[1:]
                if not full_headers:
                    header = header.split( )[0].rstrip( "|" )
            else:
                fdict[header] = fdict.get( header, "" ) + line.upper( )
    return fdict

def read_fasta_bp( path, full_headers=False ):
    fdict = OrderedDict( )
    with try_open( path, "rU" ) as fh:
        for record in SeqIO.parse( fh, "fasta" ):
            header = record.name.rstrip( "|" )
            if full_headers:
                header = " ".join( [header, record.description] )
            fdict[header] = str( record.seq ).upper( )
    return fdict

def write_fasta( fdict, path=None, wrap=None, sort=False ):
    fh = sys.stdout
    if path is not None:
        fh = try_open( path, "w" )
    order = sorted( fdict ) if sort else fdict.keys( )
    for header in order:
        seq = fdict[header]
        if header[0] != ">":
            header = ">" + header
        print( header, file=fh )
        if wrap is None:
            print( seq, file=fh )
        else:
            while len( seq ) > wrap:
                print( seq[0:wrap], file=fh )
                seq = seq[wrap:]
            if len( seq ) > 0:
                print( seq, file=fh )
    fh.close( )
    return None

# ---------------------------------------------------------------
# metacyc
# ---------------------------------------------------------------

def metacyc_pathway_rename( pwy_name, drop_codes=False ):
    # remove quotes
    pwy_name = pwy_name.replace( '"', '' )
    # grab code if present
    code = re.search( "^(.*?): ", pwy_name ).group( 1 )
    # remove code if present
    pwy_name = re.sub( ".*?: ", "", pwy_name )
    # no superpathways
    pwy_name = re.sub( "superpathway of ", "", pwy_name )
    # no parentheticals
    pwy_name = re.sub( " \(.*?\)", "", pwy_name )
    # no roman numerals
    pwy_name = re.sub( " [IVX]+$", "", pwy_name )
    # abbreviate biosynthesis (very common)
    pwy_name = re.sub( "biosynthesis", "biosyn.", pwy_name )
    # clean up greek letters
    pwy_name = re.sub( "\&(.*?)\;", "\\1", pwy_name )
    # re-attach code?
    if not (code is None or drop_codes):
        pwy_name = "{} ({})".format( pwy_name, code )
    # cap first letter
    pwy_name = pwy_name[0].upper( ) + pwy_name[1:]
    return pwy_name
                                        



    

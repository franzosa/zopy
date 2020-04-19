#! /usr/bin/env python

import sys
from Bio import SeqIO
name = sys.argv[1]
n = sys.argv[2]
if "fasta" not in name:
    sys.exit( "bad name" )
try:
    n = int( n )
except:
    sys.exit( "bad number" )
fcount = 0
scount = 0
for record in SeqIO.parse( name, "fasta" ):
    if fcount == 0 or scount == n:
        if fcount > 0:
            fh.close()
        scount = 0
        fcount += 1
        fh = open( name.replace( ".fasta", "-%04d.fasta" % ( fcount ) ), "w" )
    scount += 1
    SeqIO.write( record, fh, "fasta" )
fh.close()

#! /usr/bin/env python

import sys
from Bio import SeqIO

p_fasta = sys.argv[1]
for record in SeqIO.parse( p_fasta, "fasta" ):
    seq = str( record.seq )
    print ">{}|{}".format( record.description, len( seq ) )
    print seq

#! /usr/bin/env python

import sys
from Bio import SeqIO
for record in SeqIO.parse( sys.stdin, "fastq" ):
    SeqIO.write( record, sys.stdout, "fasta" )

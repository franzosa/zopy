#! /usr/bin/env python

import sys, argparse
from Bio import SeqIO

# arguments
parser = argparse.ArgumentParser()
parser.add_argument( '--iformat', default='fastq', help="format of input piped seq (default=fastq)" )
parser.add_argument( '--oformat', default='fastq', help="format to pipe out (default=fastq)" )
parser.add_argument( '--minlen', type=int, help='mininum length for seqs (e.g. 60)' )
args = parser.parse_args()

# coerce
c_strInputFormat = args.iformat
c_strOutputFormat = args.oformat
c_intMinLen = args.minlen

#execute
for record in SeqIO.parse( sys.stdin, c_strInputFormat ):
    if len( record.seq ) >= c_intMinLen:
        SeqIO.write( record, sys.stdout, c_strOutputFormat )

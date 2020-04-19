#! /usr/bin/env python

import sys, re, argparse
import subprocess

# argument parsing (python argparse)
parser = argparse.ArgumentParser()
parser.add_argument( 
    '-i', '--input', 
    help='fasta file', 
    )
parser.add_argument(
    '-f', '--patterns_file', 
    help='like grep -f behavior', 
    )
args = parser.parse_args()

# quickly get the list of matching headers
cmd = "grep -P '^>' {} | grep -f {}".format( args.input, args.patterns_file )
process = subprocess.Popen( cmd, shell=True, stdout=subprocess.PIPE )
headers = {}
for line in process.stdout:
    headers[line] = 1

# process the fasta file
skipping = True
with open( args.input ) as fh:
    for line in fh:
        if line[0] == ">":
            if line in headers:
                skipping = False
            else:
                skipping = True
        if not skipping:
            print line.strip()

#! /usr/bin/env python

import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument( "-s", "--skip-lines", type=int, default=1, help="" )
args = parser.parse_args()

skipped = 0

for line in sys.stdin:
    if skipped >= args.skip_lines:
        sys.stdout.write( line )
    else:
        skipped += 1



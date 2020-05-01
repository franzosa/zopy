#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import re
import argparse

import zopy.utils as zu

# argument parsing (python argparse)
parser = argparse.ArgumentParser( )
parser.add_argument( "module" )
args = parser.parse_args( )

# find imports
hits = {}
for line in zu.iter_lines( args.module ):
    line = line.strip( )
    if line.startswith( "import" ):
        # import X as Y
        if " as " in line:
            inner = hits.setdefault( "alias", {} )
            inner[line.split( " as " )[1]] = None
        # import X(, Y, Z)
        else:
            line = re.sub( "^import +", "", line )
            for h in re.split( ", +", line ):
                inner = hits.setdefault( "full", {} )
                inner[h] = None
    elif line.startswith( "from" ):
        # from X import Y(, Z)
        line = line.split( " import " )[1]
        for h in re.split( ", +", line ):
            inner = hits.setdefault( "subset", {} )
            inner[h] = None

# find uses
for line in zu.iter_lines( args.module ):
    line = line.strip( )
    if "import " in line:
        continue
    for h in hits.get( "full", {} ):
        if h + "." in line:
            hits["full"][h] = line
    for h in hits.get( "alias", {} ):
        if h + "." in line:
            hits["alias"][h] = line
    for h in hits.get( "subset", {} ):
        if h in line:
            hits["subset"][h] = line
            
# report unused
for outer in sorted( hits ):
    for h in hits[outer]:
        zu.tprint( args.module, outer, h, hits[outer][h] )


        

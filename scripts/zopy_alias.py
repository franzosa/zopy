#! /usr/bin/env python

import os, sys, re, glob, argparse
from string import uppercase, lowercase

with open( "zopy_alias.sh", "w" ) as fh:
    for k in sorted( glob.glob( "*.py" ) ):
        s = k.replace( "script", "" )
        s = s.replace( ".py", "" )
        alias = ""
        for i in range( len( s ) ):
            if 0 < i < len( s ) - 1 and s[i] in uppercase:
                if s[i+1] in lowercase or s[i-1] in lowercase:
                    alias += "_"
            alias += s[i].lower()
        print >>fh, "alias %s='%s/%s'" % ( alias, os.getcwd(), k )

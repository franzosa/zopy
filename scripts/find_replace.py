#! /usr/bin/env python

"""
mimics the unix functions
( 1 ) find . -name FILE_PATTERN | xargs grep TEXT_PATTERN
( 2 ) find . -name FILE_PATTERN | xargs sed -i.bak "s/TEXT_PATTERN/SWAP_PATTERN/g"
with a bit more fine-level control
"""

import os
import sys
import re
import glob
import argparse
import shutil

from zopy.utils import try_open

parser = argparse.ArgumentParser()
parser.add_argument( '-f', "--file_pattern" )
parser.add_argument( '-t', "--text_pattern" )
parser.add_argument( '-s', "--swap_pattern", default=None )
parser.add_argument( '-e', "--execute", action="store_true" )
parser.add_argument( '-l', "--size_limit", default=1e6 )
parser.add_argument( '-i', "--ignore_backups", action="store_true" )
parser.add_argument( '-d', "--delete_backups", action="store_true" )
parser.add_argument( '-r', "--restore_backups", action="store_true" )
args = parser.parse_args()

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

c_strBAK = ".zobak"

# ---------------------------------------------------------------
# get all files matching -f below cwd
# ---------------------------------------------------------------

root = os.getcwd()
aMatchingFiles = []
aMatchingFiles += glob.glob( os.path.join( root, args.file_pattern ) )
for subroot, aDirectories, aFiles in os.walk( root ):
    for directory in aDirectories:
        aMatchingFiles += glob.glob( os.path.join( subroot, directory, args.file_pattern ) )
aMatchingFiles = [f for f in aMatchingFiles if not os.path.islink( f )]
        
# ---------------------------------------------------------------
# find
# ---------------------------------------------------------------

"""find the files that match the file pattern; if we're not in swap mode, then
print them ( and matching lines ) to the screen; else save them for find-replace
in the next part"""

aMatchingFiles2 = []
for path in aMatchingFiles:
    already_hit=False
    fh = try_open( path )
    for i, line in enumerate( fh ):
        line = line.rstrip( "\n" )
        if re.search( args.text_pattern, line ):
            if not already_hit:
                aMatchingFiles2.append( path )
                already_hit = True
                if args.swap_pattern is None:
                    print path
            if args.swap_pattern is None:
                print "\t", "%5d" % ( i+1 ), line
    fh.close()
# now, matching files stores files that match the file pattern AND hit the text pattern
aMatchingFiles = aMatchingFiles2

# ---------------------------------------------------------------
# replace: check files
# ---------------------------------------------------------------

"""if we're in swap mode, do checks on the potential files before reading and writing
( 1 ) make sure it's not too big, ( 2 ) don't follow simlinks, and ( 3 ) don't overwrite existing bak files"""

if args.swap_pattern:
    aMatchingFiles2 = []
    for path in aMatchingFiles:
        if os.path.getsize( path ) > args.size_limit:
            print "Skipping", path, "TOO BIG!"
        elif os.path.islink( path ):
            print "Skipping", path, "SYMBOLIC LINK!"
        else:
            aMatchingFiles2.append( path )
        if os.path.exists( path + c_strBAK ) and not args.ignore_backups:
            sys.exit( "EXITING: backup exist for some matched files: %s" % ( path + c_strBAK ) )
    aMatchingFiles = aMatchingFiles2

# ---------------------------------------------------------------
# replace: test
# ---------------------------------------------------------------

"""if we're in test swap, show what lines would be replaced"""

if args.swap_pattern is not None and args.execute == False:
    for path in aMatchingFiles:
        already_hit=False
        ifh = try_open( path )
        for i, line in enumerate( ifh ):
            line = line.rstrip( "\n" )
            if re.search( args.text_pattern, line ):
                if not already_hit:
                    already_hit=True
                    print path
                print "\t", "%5d" % ( i + 1 ), "old >", line.rstrip( "\n" )
                print "\t", "%5d" % ( i + 1 ), "new <", re.sub( args.text_pattern, args.swap_pattern, line )
        ifh.close()
    print "**** NOTE: <-e, --execute> not set, so nothing has changed ****\n"

# ---------------------------------------------------------------
# replace: execute
# ---------------------------------------------------------------

"""if we're in execute swap, actually do the swapping, saving original as bak file"""

if args.swap_pattern is not None and args.execute == True:
    for path in aMatchingFiles:
        path_bak = path + c_strBAK
        shutil.copy( path, path_bak )
        ifh = try_open( path_bak )
        ofh = try_open( path, "w" )
        for i, line in enumerate( ifh ):
            # **** rstrip( "\n" ) is critical for parsing python code
            line = line.rstrip( "\n" )
            print >>ofh, re.sub( args.text_pattern, args.swap_pattern, line )
        ofh.close()
        ifh.close()
        if args.delete_backups:
            os.remove( path_bak )

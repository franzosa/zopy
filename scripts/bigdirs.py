#!/usr/bin/env python

from __future__ import print_function

import os
import re
import sys
import csv
import subprocess
import argparse

from pwd import getpwuid

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

c_k = 1024

# ---------------------------------------------------------------
# utils
# ---------------------------------------------------------------

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "path", 
                         help="starting path for 'du' call" )
    parser.add_argument( "-c", "--critsize", 
                         default=500e9, 
                         type=float, 
                         help="critical directory size (in bytes)" )
    parser.add_argument( "-o", "--overwrite", 
                         action="store_true", 
                         help="if temp 'du' output is found, overwrite" )
    parser.add_argument( "-q", "--quota", 
                         type=float,
                         help="if not specified, will use 'df' on root", )
    args = parser.parse_args( )
    return args

def warn( *args ):
    print( *args, file=sys.stderr )

def iter_rows( path ):
    with open( path ) as fh:
        for row in csv.reader( fh, csv.excel_tab ):
            yield row
    
def prettysize( size, basis=1e3 ):
    pairs = [
        [basis**4, "TB"],
        [basis**3, "GB"],
        [basis**2, "MB"],
        [basis**1, "KB"],
        ]
    for t, s in pairs:
        if size > t:
            size = "%.1f%s" % ( size / t, s )
            break
    else:
        size = str( size )
    return size

def get_owner( path ):
    try:
        return getpwuid( os.stat( path ).st_uid ).pw_name
    except:
        return "#N/A"

def dirparent( pdir ):
    if pdir.count( "/" ) < 2:
        return "/"
    else:
        temp = pdir.split( "/" )
        temp = temp[:-1]
        return "/".join( temp )

def make_pstring( path ):
    pstring = path
    pstring = re.sub( "[^0-9A-Za-z]+", "_", pstring )
    pstring = re.sub( "^_+", "", pstring )
    pstring = re.sub( "_+$", "", pstring )
    return pstring

def report_name( path, extension ):
    return ".".join( ["bigdirs", make_pstring( path ), extension] )

def run_df( path ):
    cmd = subprocess.Popen( "df {}".format( path ), shell=True, stdout=subprocess.PIPE )
    lines = [k for k in cmd.stdout]
    items = lines[1].split( )
    # df also reports Kbs
    size, root = int( items[1] ) * c_k, items[-1]
    warn( "your path is in file system <{}> with total size {} ({})".format(
            root, size, prettysize( size ) ) )
    return size

def run_du( path, OVERWRITE ):
    ptmp = report_name( path, "tmp" )
    perr = report_name( path, "err" )
    if not os.path.exists( ptmp ) or OVERWRITE:
        warn( "Logging 'du' on:", path, "to", ptmp, "and", perr )
        os.system( "du {} > {} 2> {}".format( path, ptmp, perr ) )
    else:
        warn( "tmp file {} exists; use --overwrite to ignore".format( ptmp ) )
    return ptmp

def analyze( ptmp, CRITSIZE ):
    pathsize = {}
    uniqsize = {}
    children = {}
    for row in iter_rows( ptmp ):
        size, path = row
        # last du line includes the slash
        if path[-1] == "/":
            path = path[0:-1]
        # du reports sizes in kb not bytes (outside of -h mode)
        size = int( size ) * c_k
        pathsize[path] = size
        children.setdefault( dirparent( path ), [] ).append( path )
    # find critical subfolders
    include = {}
    for path, size in pathsize.items( ):
        for child in children.get( path, [] ):
            csize = pathsize[child]
            if csize >= CRITSIZE:
                size -= csize
        uniqsize[path] = size
        include[path] = size > CRITSIZE
    # report
    return {path:(pathsize[path], uniqsize[path]) \
                      for path in include if include[path]}

def report( path, sizedict, quota ):
    header = [
        "Path \ Prop",
        "Root",
        "Owner",
        "Size",
        "Size(h)",
        "Size(%)",
        "UniqSize",
        "UniqSize(h)",
        "UniqSize(%)",
        ]
    if quota is None:
        root_size = run_df( path )
    else:
        warn( "using user-specified quota {} ({})".format( int( quota ), prettysize( quota ) ) )
        root_size = quota
    prep = report_name( path, "tsv" )
    with open( prep, "w" ) as fh:
        print( "\t".join( header ), file=fh )
        warn( "writing analysis to {}".format( prep ) )
        for p in sorted( sizedict, key=lambda x: sizedict[x][1], reverse=True ):
            size, uniq = sizedict[p]
            owner = get_owner( p )
            sizeh = prettysize( size )
            uniqh = prettysize( uniq )
            outitems = [
                p, path,
                owner,
                size, 
                sizeh, 
                "%.2f" % ( 100 * float( size ) / root_size ),
                uniq, 
                uniqh, 
                "%.2f" % ( 100 * float( uniq ) / root_size ),
                ]
            print( "\t".join( map( str, outitems ) ), file=fh )
    return None

# ---------------------------------------------------------------
# main
# ---------------------------------------------------------------
        
def main( ):
    args      = get_args( )
    path      = args.path
    OVERWRITE = args.overwrite
    CRITSIZE  = args.critsize
    ptmp      = run_du( path, OVERWRITE )
    sizedict  = analyze( ptmp, CRITSIZE )
    report( path, sizedict, args.quota )

if __name__ == "__main__":
    main( )

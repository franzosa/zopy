#! /usr/bin/env python

import os, sys, re, glob, argparse
from zopy.table2 import table, nesteddict2table
from zopy.utils import path2name

def funcLoadCladeProfile ( fileCladeProfile, grep=None, headers=False ):
    """ load a single MetaPhlAn clade profile to a [marker]=value dictionary,
    marker ids are prepended with 'clade|', e.g. 'g__Bacteroides|12345678' """
    dictMarkerValues = {}
    with open( fileCladeProfile ) as fh:
        if headers:
            skip = fh.readline()
            print >>sys.stderr, "skipping header line:", skip
        # reading two lines at a time
        while True:
            marker_line, value_line = fh.readline(), fh.readline()
            if value_line:
                aMarkers = marker_line.strip().split()
                # fix for metaphlan2 markers
                aMarkers = map( lambda x: x.replace( "|", "!" ), aMarkers )
                aValues = value_line.strip().split()
                clade, aValues = aValues[0], aValues[1:]
                if grep is None or re.search( grep, clade ):
                    aMarkers = ["|".join( [clade, marker] ) for marker in aMarkers]
                    if len( aMarkers ) != len( aValues ):
                        sys.exit( "markers and values not the same length" )
                    else:
                        for marker, value in zip( aMarkers, aValues ):
                            # quick fix for metaphlan2 output
                            dictMarkerValues[marker] = float( value )
            else:
                break
    return dictMarkerValues

if __name__ == "__main__":
    # args
    parser = argparse.ArgumentParser()
    parser.add_argument( '-i', '--input', nargs="+", help='One or more MetaPhlAn clade profiles' )
    parser.add_argument( '-o', '--output', help='Marker PCL file' )
    parser.add_argument( '-e', '--headers', action="store_true", help='File has headers' )
    parser.add_argument( '-g', '--grep', default=None, help='grep on clades' )
    parser.add_argument( '-x', '--extension_groups', default=1, type=int, help='.txt is 1, .cp.txt is 2, etc.' )
    args = parser.parse_args()
    # load everything as nested dict [sample][marker]=value
    nesteddictData = {}
    for i, path in enumerate( args.input ):
        print >>sys.stderr, "loading", i+1, "of", len( args.input )
        name = path2name( path, args.extension_groups )
        nesteddictData[name] = funcLoadCladeProfile( path, grep=args.grep, headers=args.headers )
    # convert to a table, substituting 0 for missing values
    tableData = nesteddict2table( nesteddictData, empty=0 )
    # transpose to get markers on the rows, unfloat, save as pcl
    tableData.transpose()
    tableData.unfloat()
    tableData.dump( args.output )

#! /usr/bin/env python

import sys
import argparse
from math import floor, sqrt

from numpy import polyfit

from scipy.stats import pearsonr, spearmanr
from scipy.stats.mstats import mquantiles
from zopy.stats import mutinfo
from zopy.utils import reader
from zopy.table2 import nesteddict2table

c_epsilon = 1e-20

total = 0
bad = 0

parser = argparse.ArgumentParser()
parser.add_argument( 
    '-z', "--zerozero", 
    action="store_true", 
    help="if set: 0,0 points EXCLUDED", )
args = parser.parse_args()

# read in data
rows = []
for row in reader( sys.stdin ):
    total += 1
    if len( row ) == 2:
        row = ["<#s>"] + row
    elif len( row ) == 3 and total == 1:
        print >>sys.stderr, "stratifying on first field, e.g.:", row[0]
    try:
        row[1] = float( row[1] )
        row[2] = float( row[2] )
        rows.append( row )
    except:
        print >>sys.stderr, "ignoring", "\t".join( map( str, row ) )
        bad += 1

# stratify
data = {}
for stratum, x, y in rows:
    data.setdefault( stratum, [] ).append( [x, y] )

# make nested stats table
def pretty( number ):
    if type( number ) is str:
        return number
    elif abs( number - floor( number ) ) < c_epsilon:
        return "%d" % ( number )
    else:
        return "%.4g" % ( number )

def quantform( numbers ):
    quantiles = mquantiles( numbers )
    output = []
    for n in numbers:
        for i, q in enumerate( quantiles ):
            if n <= q:
                output.append( i )
                break
        else:
            output.append( len( quantiles ) )
    return output

def bc( xx, yy, norm=False ):
    if norm:
        t = sum( xx )
        xx = [k/t for k in xx]
        t = sum( yy )
        yy = [k/t for k in yy]
    num, den = 0, 0
    for x, y in zip( xx, yy ):
        num += 2 * min( x, y )
        den += x + y
    return num / den

order = "N r r2 r_p rho rho2 rho_p BC BC_norm NMI slope y-int 1/slope x-int".split()
def row_stats( row ):
    x = [k[0] for k in row]
    y = [k[1] for k in row]
    if args.zerozero:
        test = [xi == yi == 0 for xi, yi in zip( x, y )]
        x = [xi for xi, ti in zip( x, test ) if not ti]
        y = [yi for yi, ti in zip( y, test ) if not ti]
    # check for homogeneity
    stats = {}
    stats["N"] = len( x )
    if len( set( x ) ) < 2 or len( set( y ) ) < 2:
        for s in order[1:]:
            stats[s] = "#N/A"
    else:
        stats["r"], stats["r_p"] = pearsonr( x, y )
        stats["r2"] = stats["r"]**2
        stats["rho"], stats["rho_p"] = spearmanr( x, y )
        stats["rho2"] = stats["rho"]**2
        stats["NMI"] = mutinfo( quantform( x ), quantform( y ), normalized=True )
        stats["BC"] = bc( x, y )
        stats["BC_norm"] = bc( x, y, norm=True )
        slope, y_int = polyfit( x, y, 1 )
        stats["slope"] = slope
        stats["y-int"] = y_int
        stats["1/slope"] = 1/slope
        stats["x-int"] = -y_int/slope
    stats = {k:pretty( v ) for k, v in stats.items()}
    return stats 

for stratum in sorted( data ):
    data[stratum] = row_stats( data[stratum] )
tdata = nesteddict2table( data, aColheads=list( order ), origin="STAT \ LEVEL" )
tdata.transpose()
tdata.dump()
if bad > 0:
    print >>sys.stderr, "%% bad rows: %.2f" % ( 100 * bad / float( total ) )

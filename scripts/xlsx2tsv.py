#!/usr/bin/env python

import os
import sys
import re
import argparse
import csv

from zopy.utils import path2name, die

try:
    import openpyxl as xl
except:
    die( "This script requires the OPENPYXL module" )
    
# argument parsing (python argparse)
parser = argparse.ArgumentParser( ) 
parser.add_argument( "xlsx", help="" )
args = parser.parse_args( )

wb = xl.load_workbook( filename=args.xlsx )

for ws in wb:

    basename = path2name( args.xlsx )
    sheet = ws.title
    sheet = re.sub( "[^A-Za-z0-9]+", "_", sheet )
    newname = "{}.{}.tsv".format( basename, sheet )
    fh = open( newname, "w" )
    ww = csv.writer( fh, csv.excel_tab )
    
    for row in ws.iter_rows( ):
        row2 = []
        for cell in row:
            value = cell.value
            if value is None:
                continue
            try:
                value = value.encode( "utf-8" )
            except:
                value = str( value )
            row2.append( value )
        if len( row2 ) > 0:
            ww.writerow( row2 )

    fh.close( )

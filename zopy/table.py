#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import re
import copy
import csv
from itertools import chain

from scipy.stats import rankdata
from numpy import array

import zopy.utils as zu

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------

c_origin = "#"
c_na = "#N/A"

#-------------------------------------------------------------------------------
# helper functions
#-------------------------------------------------------------------------------

def load_from_nested_dicts( T ):
    if T.origin is None:
        T.origin = c_origin
    if T.rowheads is None:
        T.rowheads = sorted( T.source )
    if T.colheads is None:
        unique = set( )
        for k, v in source.items( ):
            unique.update( v )
        T.colheads = sorted( unique )
    for r in T.rowheads:
        inner = T.source[r]
        T.data.append( [inner.get( c, c_na ) for c in T.colheads] )
    return None

def load_from_nested_lists( T, rows ):
    counter = 0
    for row in rows:
        if counter == 0:
            T.origin = row[0] if not T.headless else c_origin
            T.colheads = row[1:] if not T.headless else list( range( 1, len( row ) + 1 ) )
        else:
            T.rowheads.append( row[0] if not T.headless else counter )
            T.data.append( row[1:] if not T.headless else row )       
        counter += 1
    return None

def load_from_file_handle( T, fh ):
    load_from_nested_lists( T, csv.reader( fh, dialect="excel_tab" ) )
    return None

def load_from_file( T, path ):
    load_from_file_handle( T, zu.try_open( path ) )
    return None

def deduplicate( items ):
    seen = set( )
    deduplicated = False
    for i, k in enumerate( items ):
        while k in seen:
            deduplicated = True
            k += "-dup"
        items[i] = k
        seen.add( k )
    zu.say( "Some fields were deduplicated." )
    return None
        
#-------------------------------------------------------------------------------
# begin main object
#-------------------------------------------------------------------------------

class Table:
    
    def __init__( self, source=None,
                  data=None, colheads=None, rowheads=None,
                  origin=None, missing=None,
                  headless=False, verbose=True ):

        self.source = source
        
        self.data = data if data is not None else []
        self.rowheads = rowheads if rowheads is not None else []
        self.colheads = rowheads if .colheads is not None else []

        self.origin = origin if origin is not None else c_origin
        self.missing = missing if missing is not None else c_na
        
        self.headless = headless
        self.verbose = verbose

        self.sourcename = None
        self.rowmap = None
        self.colmap = None
        self.transposed = False
        
        # decide how to load table
        if isinstance( source, list ):
            self.sourcename = "<list of lists>"
            load_from_nested_lists( T )
        elif isinstance( source, dict ):
            self.sourcename = "<dict of dicts>"
            load_from_nested_dicts( T )
        elif isinstance( source, file ):
            self.sourcename = "<file handle>" )
            load_from_file_hand( T )
        elif os.path.exists( source ):
            self.sourcename = "<{}>".format( source )
            load_from_file( T )
        elif source is None:
            self.sourcename = "<runtime>"
            if not all( data, rowheads, colheads ):
                zu.die( "If no source provided, must provide data/rowheads/colheads" )

        # set up other table elements        
        self.remap( )
        self.report( "new table with size", self.size( ) )

    def remap( self ):

        # integrity checks
        if len( set( [len( row ) for row in self.data] ) ) != 1:
            zu.die( "Table has inconsistent row lengths." )
        if len( self.colheads ) != len( self.data[0] ):
            zu.die( "Table colheads do not align to data." )
        if len( self.rowheads ) != len( self.data ):
            zu.die( "Table rowheads do not align to data." )

        # auto-replace duplicate field names
        deduplicate( self.rowheads )
        deduplicate( self.colheads )
            
        # build fast maps
        self.rowmap = {i:k for i, k in enumerate( self.rowheads )}
        self.colmap = {i:k for i, k in enumerate( self.colheads )}

    #### UTILITY METHODS ####
    
    def rowdex( self, i ):
        return i if isinstance( index, int ) else self.rowmap[i]

    def coldex( self, i ):
        return i if isinstance( index, int ) else self.colmap[i]

    def report( self, *args ):
        if self.verbose:
            zu.say( self.source, ":", " ".join( [str( k ) for k in args] ) )
        return None
            
    def size( self ):
        return "<{} ROW x {} COL{}>".format(
            len( self.rowheads ),
            len( self.colheads ),
            " (transposed)" if self.transposed else "",
        )

    def copy( self ):
        return copy.deepcopy( self )

    def write( self, path=None ):
        fh = sys.stdout
        if path is not None:
            fh = zu.try_open( path, "w" )
        W = csv.writer( fh, dialect="excel_tab" )
        W.writerow( [self.origin] + self.colheads]
        for i, row in enumerate( self.data ):
            W.writerow( [self.rowheads[i]] + row )
        if path is not None:
            fh.close( )
        return None

    def rowsort( self, order=None ):
        order = sorted( self.rowheads ) if order is None else order
        self.data = [self.data[self.rowmap[r]] for r in order]
        self.remap( )
        return None

    def colsort( self, order=None ):
        self.transpose( )
        self.rowsort( order=order )
        self.transpose( )
        # no need for final remap, since it's included in transpose
        return None

    #### SLICE OPERATIONS ####

    def row( self, index ):
        return self.data[self.rowdex( index )]

    def col( self, index ):
        index = self.coldex( index )
        return [row[index] for row in self.data]

    def rowdict( self, index ):
        row = self.row( index )
        return {self.colheads[k]:row[k] for k in range( len( self.colheads ) )}

    def coldict( self, index ):
        col = self.col( index )
        return {self.rowheads[k]:col[k] for k in range( len( self.rowheads ) )}

    def entry( self, r, c ):
        r, c = self.rowdex( r ), self.coldex( c )
        return self.data[r][c]

    #### APPLY FUNCTIONS ####

    def transpose( self ):
        self.data = [[row[i] for row in self.data] for i in range( len( self.colheads ) )]
        self.colheads, self.rowheads = self.rowheads, self.colheads
        self.transposed = not self.transposed
        self.remap( )
        self.report( "Transposed the table." )
        return None
        
    def promote( self, index ):
        """ Pick a row to become the new row[0]; i.e. make it the colhead row """
        self.colheads = self.data.pop( self.rowdex( index ) )
        self.remap( )
        return None

    def set( self, r, c, value ):
        """ Set the ( r, c ) entry of the table """
        r, c = self.rowdex( r ), self.coldex( c )
        self.data[r][c] = value
        return None
        
    def apply_rowheads( self, function ):
        """ applies a function to the rowheads and remaps ( to avoid collisions ) """
        self.rowheads = [function( r ) for r in rowheads]
        self.remap( )
        return None
        
    def apply_colheads( self, function ):
        """ applies a function to the colheads and remaps ( to avoid collisions ) """
        self.colheads = [function( c ) for c in colheads]
        self.remap( )
        return None
        
    def apply_entries( self, function ):
        """ applies a function to each entry in the table """
        # updated to be more efficient; now based on list comprehension not iteration
        for i, row in self.data:
            self.data[i] = [function( k ) for k in row]
        return None

    # ***** PAUSED HERE *****
    
    def apply_row( self, index, function ):
        """ applies a function to each entry in a row """
        rowhead = self.rowdex( index )
        for colhead, value in self.rowdict( rowhead ).items( ):
            self.set( rowhead, colhead, function( value ) )

    def apply_col( self, index, function ):
        """ applies a function to each entry in a col """
        colhead = self.coldex( index )
        for rowhead, value in self.coldict( colhead ).items( ):
            self.set( rowhead, colhead, function( value ) )
                 
    # ---------------------------------------------------------------
    # generators
    # ---------------------------------------------------------------
    
    def iter_rows( self ):
        """ iterate over rows; yields rowhead, row """
        for rowhead in self.rowheads:
            yield rowhead, self.row( rowhead )

    def iter_cols( self ):
        """ iterate over cols; yields colhead, col """                         
        for colhead in self.colheads:
            yield colhead, self.col( colhead )

    def iter_entries( self ):
        """ iterate over entries; yields ( r )owhead, ( c )olhead, entry( r, c ) """
        for i, rowhead in enumerate( self.rowheads ):
            for j, colhead in enumerate( self.colheads ):
                # **** (row|col)heads don't include the origin position, so must offset i,j by 1 ****
                yield rowhead, colhead, self.data[i+1][j+1]

    # ---------------------------------------------------------------
    # reduce method, operates like python's filter on rows
    # ---------------------------------------------------------------

    def reduce( self, function, protect_headers=True, transposed=False, invert=False, in_place=True ):
        """ apply a function to the rows of the table and rebuild with or return true evals """
        # flip?
        if transposed: 
            self.transpose()
        # auto-pass headers?
        data2 = [self.data[0] if protect_headers else []]
        start = 1 if protect_headers else 0
        # apply test to rows
        if not invert:
            data2 += [row for row in self.data[start:] if function( row )]
        else:
            data2 += [row for row in self.data[start:] if not function( row )]
        # (1) rebuild table
        if in_place:
            self.data = data2
            if transposed: 
                self.transpose()
            self.remap()
            self.report( "--> reduced size is", self.size() )
            return None
        # (2) return rows that passed as new table
        else:
            if transposed: 
                self.transpose()
            # rebuild data2 to avoid referencing self.data rows
            data2 = [row[:] for row in data2]
            # this returns to the outer function, which must also return
            new_table = table( data2, verbose=self.isverbose )
            # if we were working on a transposed table, must also transpose selected rows
            if transposed: 
                new_table.transpose()
            return new_table

    # ---------------------------------------------------------------
    # methods that call reduce to do things
    # ---------------------------------------------------------------

    def grep( self, index, patterns, **kwargs ):
        """ restrict rows to those whose col[index] position matches a pattern """
        if isinstance( patterns, str ):
            patterns = [patterns]
        self.report( "applying grep", "index=", index, "patterns=", pretty_list( patterns ), kwargs )
        return self.reduce( lambda row: any( [re.search( k, row[self.coldex( index )] ) for k in patterns] ), **kwargs )

    def select( self, index, choices, **kwargs ):
        """ select rows whose col[index] entry is in choices """
        # this allows us to test if choices is a scalar or list; strange because strings are iterable?
        if isinstance( choices, str ):
            choices = [choices]
        self.report( "applying select", "index=", index, "choices=", pretty_list( choices ), kwargs )
        return self.reduce( lambda row: row[self.coldex( index )] in choices, **kwargs )

    def delete( self, index, choices, **kwargs ):
        """ delete rows whose col[index] entry is in choices """
        if isinstance( choices, str ):
            choices = [choices]
        # this allows us to test if choices is a scalar or list; strange because strings are iterable?
        self.report( "applying delete", "index=", index, "choices=", pretty_list( choices ), kwargs )
        return self.reduce( lambda row: row[self.coldex( index )] not in choices, **kwargs )

    def head( self, index, **kwargs ):
        """ keep only rows up to head; if inverted, delete rows up to head ( useful for stripping metadata ) """
        self.report( "applying head", "index=", index, kwargs )
        return self.reduce( lambda row: self.rowdex( row[0] ) <= self.rowdex( index ), **kwargs )

    def limit( self, index, operation, **kwargs ):
        """ """
        op, threshold = re.search( "([<>=]+)(.*)", operation ).groups()
        threshold = float( threshold )
        choices = { 
            "<" : lambda x: float( x ) <  threshold,
            "<=": lambda x: float( x ) <= threshold,
            ">" : lambda x: float( x ) >  threshold,
            ">=": lambda x: float( x ) >= threshold,
            }
        myfunc = choices[op]
        self.report( "applying limit, requiring field", index, "to be", op, threshold, kwargs )
        return self.reduce( lambda row: myfunc( row[self.coldex( index )] ), **kwargs )

    def unrarify( self, minlevel=0, mincount=1, **kwargs ):
        """ applies to numerical table: keep features ( row ) that exceed specified level in specified # of samples """
        self.report( "applying unrarify", "requiring at least", mincount, "row values exceeding", minlevel, kwargs )
        return self.reduce( lambda row: mincount <= sum( [1 if item > minlevel else 0 for item in row[1:]] ), **kwargs )

    # ---------------------------------------------------------------
    # groupby
    # ---------------------------------------------------------------

    def groupby( self, funcGrouper, funcSummarizer ):
        """ user grouper function on rowheads to cluster rows, then use summarizer function to combine values """ 
        groups = {} # map new rowheads to 1+ old rowheads
        for rowhead in self.rowheads:
            groupdict = groups.setdefault( funcGrouper( rowhead ), {} )
            groupdict[rowhead] = 1
        data2 = [self.data[0]] # colheads
        for group, dictRowheads in groups.items():
            aaRows = [self.row( rowhead ) for rowhead in dictRowheads]
            aaRowsTransposed = [[aRow[i] for aRow in aaRows] for i in range( len( aaRows[0] ) )]
            data2.append( [group] + [funcSummarizer( aRow ) for aRow in aaRowsTransposed] )
        self.data = data2
        self.remap()
        self.report( "applied groupby:", "rowheads now like <%s>" % ( self.rowheads[0] ), "; new size is", self.size() )

    # ---------------------------------------------------------------
    # stratification methods
    # ---------------------------------------------------------------

    def stratify( self, focus ):
        """ stratifies table on focal row value; returns dictionary of tables """
        self.transpose()
        dictDataArrays = {}
        for rowhead, row in self.iter_rows( ):
            stratum = self.entry( rowhead, focus )
            # the default is a copy of this table's rowheads (currently colheads)
            dictDataArrays.setdefault( stratum, [self.data[0][:]] ).append( [rowhead] + row )
        dictTables = {}
        for stratum, aaData in dictDataArrays.items():
            dictTables[stratum] = table( aaData, verbose=self.isverbose )
            dictTables[stratum].transpose( )
        self.transpose()
        self.report( "stratified on", focus, "into", len( dictTables ), "new tables" )
        return dictTables

    def funcify( self, func ):
        """ stratifies table on function return value """
        self.transpose( )
        dictDataArrays = {}
        for rowhead, row in self.iter_rows( ):
            ret = func( rowhead )
            if ret is not None:
                # the default is a copy of this table's rowheads (currently colheads)
                dictDataArrays.setdefault( ret, [self.data[0][:]] ).append( [rowhead] + row )
        dictTables = {}
        for stratum, aaData in dictDataArrays.items( ):
            dictTables[stratum] = table( aaData, verbose=self.isverbose )
            dictTables[stratum].transpose( )
        self.transpose( )
        self.report( "funcified into", len( dictTables ), "new tables" )
        return dictTables

    def groupify( self, funcGrouper ):
        """ stratifies table by return value of function on rowheads; returns dictionary of tables """
        dictDataArrays = {}
        for rowhead, row in self.iter_rows():
            group = funcGrouper( rowhead )
            # the default is a copy of this table's colheads
            dictDataArrays.setdefault( group, [self.data[0][:]] ).append( [rowhead] + row )
        dictTables = {}
        for group, aaData in dictDataArrays.items():
            dictTables[group] = table( aaData, verbose=self.isverbose )
        self.report( "groupified on f( rowhead ) into", len( dictTables ), "new tables" )
        return dictTables

    # ---------------------------------------------------------------
    # conversion methods
    # ---------------------------------------------------------------

    def table2tupledict( self ):
        """ return table as dictionary with tuple keys ~ ( rowheads[i], colheads[j] ) = data[i][j] """
        return {( rowhead, colhead ):value for rowhead, colhead, value in self.iter_entries()}

    def table2nesteddict( self ):
        """ return table as nested dictionary ~ [rowheads[i]][colheads[j]] = data[i][j] """
        return {rowhead:self.rowdict( rowhead ) for rowhead in self.rowheads}

    def table2array( self, last_metadata=None ):
        """ return just quant data as numpy 2d array """
        temp = []
        for rowhead, row in self.iter_rows( ):
            if last_metadata is None or self.rowmap[rowhead] > self.rowmap[last_metadata]:
                temp.append( map( float, row ) )
        return array( [array( row ) for row in temp] )
    
    # ---------------------------------------------------------------
    # methods for extending/combining tables
    # ---------------------------------------------------------------

    def insert( self, index, row ):
        """ inserts a pre-formatted row ( has header; proper order ) into the table before index """
        index = self.rowdex( index )
        self.data.insert( index, row )
        self.remap()

    def augment( self, table2 ):
        """ join table with table2 on colheads """
        setRowheadOverlap = set( self.rowheads ).__and__( set( table2.rowheads ) )
        if len( setRowheadOverlap ) > 0:
            self.report( "augmentee contains", len( setRowheadOverlap ), "duplicate rowheads (skip)" )
        # note: "colhead in dictColmap" much faster than "colhead in aColheads"
        self.data = self.data + [
            [rowhead2] + [table2.entry( rowhead2, colhead ) if colhead in table2.colmap else c_strNA for colhead in self.colheads] 
            for rowhead2 in table2.rowheads if rowhead2 not in self.rowmap
            ]
        self.remap()
        self.report( "augmented with rows from", table2.source, "new size is", self.size() )

    def extend( self, table2 ):
        """ join table with table2 on rowheads """
        setColheadOverlap = set( self.colheads ).__and__( set( table2.colheads ) )
        if len( setColheadOverlap ) > 0:
            self.report( "extendee contains", len( setColheadOverlap ), "duplicate colheads (skip)" )
        # find index for unique cols in table2
        aIndex = [j for j, colhead in enumerate( table2.colheads ) if colhead not in self.colmap]
        for i in range( len( self.data ) ):
            rowhead = self.data[i][0]
            # headers are a special case (may not align on rowhead if 0,0 entries differ)
            if i == 0:
                self.data[0] += [table2.colheads[j] for j in aIndex]
            # a shared row, add new col entries
            elif rowhead in table2.rowmap:
                row = table2.row( rowhead )
                self.data[i] += [row[j] for j in aIndex]
            # a self-specific row, add all NA entries
            else:
                self.data[i] += [c_strNA for j in aIndex]
        self.remap()
        self.report( "extended with cols from", table2.source, "new size is", self.size() )

    def merge( self, table2 ):
        """ slightly faster merge conducted as an extend and augment """
        self.extend( table2 )
        self.augment( table2 )

    # ---------------------------------------------------------------
    # methods for filling "empty" cells
    # ---------------------------------------------------------------

    def blank2na( self, value=c_strNA ):
        """ Anything that doesn't match a non-space char is filled with na """
        self.apply_entries( lambda k: k if re.search( "[^\s]", str( k ) ) else value )
        
    def na2zero( self, value=0 ):
        """ Convert NAs to zero values """
        self.apply_entries( lambda k: value if k == c_strNA else k )

    # ---------------------------------------------------------------
    # methods for working with metadata
    # ---------------------------------------------------------------

    def metasplit( self, last_metadata_row ):
        """ splits a table into top ( metadata ) and bottom ( features ); returns """
        tableMetadata = self.head( last_metadata_row, in_place=False )
        tableFeatures = self.head( last_metadata_row, in_place=False, invert=True )
        return tableMetadata, tableFeatures

    def metamerge( self, tableMetadata ):
        """ merges metadata ON TOP of current table """
        dataTemp = self.data[1:] # data rows
        self.head( 0 )
        self.augment( tableMetadata )
        self.data += dataTemp
        self.remap()
        self.report( "added metadata from", tableMetadata.source, "new size is", self.size() )

    # ---------------------------------------------------------------
    # methods based on math
    # ---------------------------------------------------------------

    def compress_zeroes( self ):
        """ replaces 0.0 with 0 for compression """
        self.apply_entries( lambda k: 0 if k == 0.0 else k )

    def float( self ):
        """ Attempt to float all non-header entries in the table """
        self.apply_entries( float )

    def unfloat( self ):
        """ convert 0.0 to 0 and reduce others to N sig figs for compression """
        self.apply_entries( lambda k: "0" if k == 0.0 else "%.6g" % ( k ) )

    def normalize_columns( self ):
        """ Normalizes the columns. Fails if there are non-numeric entries. """
        # transpose because working on rows is easier
        self.transpose()
        # iter over rows
        for i, header in enumerate( self.rowheads ):
            # note, rowhead 0 is row 1 of main table ***
            row = self.row( header )
            total = float( sum( row ) )
            if total > 0:
                row = [ k/total for k in row ]
            else:
                row = [ 0.0 for k in row ]
                self.report( "WARNING:", "sum of column", header, self.rowdex( header ), "is 0" )
            self.data[i+1] = [header] + row # ***
        # flip back
        self.transpose()
        # report
        self.report( "normalized the columns" )

    def rank_columns( self, normalize=False ):
        """ Ranks the columns. Fails if there are non-numeric entries. """
        # transpose because working on rows is easier
        self.float( )
        self.transpose()
        # iter over rows
        for i, header in enumerate( self.rowheads ):
            # note, rowhead 0 is row 1 of main table ***
            row = self.row( header )
            row = list( rankdata( row ) ) # default return is numpy array
            row = row if not normalize else [k/max( row ) for k in row]
            self.data[i+1] = [header] + row # ***
        # flip back
        self.transpose()

    # ---------------------------------------------------------------
    # end of the table object
    # ---------------------------------------------------------------

# ---------------------------------------------------------------
# table-related methods outside of the table object
# ---------------------------------------------------------------

def pretty_list( items ):
    """ simplifies printing long argument lists """
    items = list( items )
    if len( items ) <= c_iMaxPrintChoices:
        return items
    else:
        return items[0:c_iMaxPrintChoices] + ["{{ + %d others }}" % ( len( items ) - c_iMaxPrintChoices )]

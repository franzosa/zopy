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
c_max_print = 5

#-------------------------------------------------------------------------------
# helper functions
#-------------------------------------------------------------------------------

def load_from_nested_dicts( T, dd ):
    if T.rowheads == []:
        T.rowheads = sorted( dd )
    if T.colheads == []:
        unique = set( )
        for k, inner in dd.items( ):
            unique.update( inner )
        T.colheads = sorted( unique )
    for r in T.rowheads:
        inner = dd.get( r, {} )
        T.data.append( [inner.get( c, T.missing ) for c in T.colheads] )
        
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

def load_from_file_handle( T, fh ):
    load_from_nested_lists( T, csv.reader( fh, dialect="excel-tab" ) )

def load_from_file( T, path ):
    load_from_file_handle( T, zu.try_open( path ) )

def deduplicate( items ):
    seen = set( )
    deduplicated = False
    for i, k in enumerate( items ):
        while k in seen:
            deduplicated = True
            k += "-dup"
        items[i] = k
        seen.add( k )
    if deduplicated: zu.say( "Some fields were deduplicated." )

def pretty_list( items ):
    items = list( items )
    if len( items ) > c_max_print:
        extra = "& {} others".format( len( items ) - c_max_print )
        items = [items[0:c_max_print] + [extra]]
    return items
    
#-------------------------------------------------------------------------------
# begin main object
#-------------------------------------------------------------------------------

class Table:
    
    def __init__( self,
                  source=None,
                  data=None,
                  colheads=None,
                  rowheads=None,
                  origin=None,
                  missing=None,
                  headless=False,
                  transposed=False,
                  verbose=True,
    ):

        self.source = source
        
        self.data = data if data is not None else []
        self.rowheads = rowheads if rowheads is not None else []
        self.colheads = colheads if colheads is not None else []

        self.origin = origin if origin is not None else c_origin
        self.missing = missing if missing is not None else c_na
        
        self.transposed = transposed
        self.headless = headless
        self.verbose = verbose

        self.sourcename = None
        self.rowmap = None
        self.colmap = None
        
        # decide how to load table
        if source is None:
            self.sourcename = "<runtime>"
            if not all( [data, rowheads, colheads] ):
                zu.die( "If no source provided, must provide data/rowheads/colheads" )
        elif isinstance( source, list ):
            self.sourcename = "<list of lists>"
            load_from_nested_lists( self, source )
        elif isinstance( source, dict ):
            self.sourcename = "<dict of dicts>"
            load_from_nested_dicts( self, source )
        elif isinstance( source, file ):
            self.sourcename = "<file handle>"
            load_from_file_handle( self, source )
        elif os.path.exists( source ):
            self.sourcename = "<{}>".format( source )
            load_from_file( self, source )

        # set up other table elements        
        self.remap( )
        self.report( "New table with size {}.".format( self.size( ) ) )

    def remap( self ):

        # integrity checks
        if len( self.data ) > 0:
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
        self.rowmap = {k:i for i, k in enumerate( self.rowheads )}
        self.colmap = {k:i for i, k in enumerate( self.colheads )}

    #### UTILITY METHODS ####
    
    def rowdex( self, index ):
        ret = None
        if isinstance( index, int ) and 0 <= index < len( self.rowheads ):
            ret = index
        elif index in self.rowmap:
            ret = self.rowmap[index]
        else:
            self.report( "Bad row index <{}>.".format( index ), die=True )
            zu.die( )
        return ret

    def coldex( self, index ):
        ret = None
        if isinstance( index, int ) and 0 <= index < len( self.colheads ):
            ret = index
        elif index in self.colmap:
            ret = self.colmap[index]
        else:
            self.report( "Bad col index <{}>.".format( index ), die=True )
        return ret

    def report( self, *args, **kwargs ):
        items = [self.sourcename, "::", " ".join( [str( k ) for k in args] )]
        if kwargs.get( "die", False ):
            zu.die( *items )
        elif self.verbose:
            zu.say( *items )
            
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
        W = csv.writer( fh, dialect="excel-tab" )
        W.writerow( [self.origin] + self.colheads )
        for i, row in enumerate( self.data ):
            W.writerow( [self.rowheads[i]] + row )
        if path is not None:
            fh.close( )

    def rowsort( self, order=None ):
        order = order if order is not None else sorted( self.rowheads )
        self.data = [self.row( r ) for r in order]
        self.rowheads = order
        self.remap( )

    def colsort( self, order=None ):
        # no need for final remap, since it's included in transpose
        self.transpose( )
        self.rowsort( order=order )
        self.transpose( )

    #### SLICE OPERATIONS ####

    def row( self, index ):
        # note full slice to avoid referencing
        return self.data[self.rowdex( index )][:]

    def col( self, index ):
        index = self.coldex( index )
        return [row[index] for row in self.data]

    def rowdict( self, index ):
        row = self.row( index )
        return {self.colheads[k]:row[k] for k in range( len( self.colheads ) )}

    def coldict( self, index ):
        col = self.col( index )
        return {self.rowheads[k]:col[k] for k in range( len( self.rowheads ) )}

    def get( self, r, c ):
        r, c = self.rowdex( r ), self.coldex( c )
        return self.data[r][c]

    #### APPLY FUNCTIONS ####

    def transpose( self ):
        """ transpose the table data in place """
        self.data = [[row[i] for row in self.data] for i in range( len( self.colheads ) )]
        self.colheads, self.rowheads = self.rowheads, self.colheads
        self.transposed = not self.transposed
        self.remap( )
        self.report( "Transposed the table." )
        
    def promote( self, index ):
        """ pick a row to become the new row[0]; i.e. make it the colhead row """
        self.colheads = self.data.pop( self.rowdex( index ) )
        self.remap( )

    def set( self, r, c, value ):
        """ set the ( r, c ) entry of the table """
        r, c = self.rowdex( r ), self.coldex( c )
        self.data[r][c] = value
        
    def apply_rowheads( self, function ):
        """ applies a function to the rowheads and remaps ( to avoid collisions ) """
        self.rowheads = [function( r ) for r in self.rowheads]
        self.remap( )
        
    def apply_colheads( self, function ):
        """ applies a function to the colheads and remaps ( to avoid collisions ) """
        self.colheads = [function( c ) for c in self.colheads]
        self.remap( )
        
    def apply_row( self, index, function ):
        """ applies a function to each entry in a row """
        r = self.rowdex( index )
        self.data[r] = [function( k ) for k in self.data[r]]
        
    def apply_col( self, index, function ):
        """ applies a function to each entry in a col """
        c = self.coldex( index )
        for i, row in enumerate( self.data ):
            self.data[i][c] = function( row[c] )

    def apply_entries( self, function ):
        """ applies a function to each entry in the table """
        for r in self.rowheads:
            self.apply_row( r, function )
            
    #### GENERATORS ####
    
    def iter_rows( self ):
        """ iterate over rows; yields rowhead, row """
        for r in self.rowheads:
            yield r, self.row( r )

    def iter_cols( self ):
        """ iterate over cols; yields colhead, col """                         
        for c in self.colheads:
            yield c, self.col( c )

    def iter_entries( self ):
        """ iterate over entries; yields ( r )owhead, ( c )olhead, entry( r, c ) """
        for r in self.rowheads:
            for c in self.colheads:
                yield r, c, self.get( r, c )

    #### FILTER OPERATIONS ####               

    def filter( self,
                function,
                t=None, transposed=False,
                i=None, invert=False,
                n=None, new=False,
    ):

        """ apply a function to the rows of table (via headers) and rebuild or return true evals """

        # process shortcuts 
        transposed = transposed if t is None else t
        invert = invert if i is None else i
        new = new if n is None else n

        # flip?
        if transposed: self.transpose( )

        # apply test to rows
        mask = [function( r ) for r in self.rowheads]
        mask = mask if not invert else [not k for k in mask]

        # (1) rebuild table
        if not new:
            self.data = [row for test, row in zip( mask, self.data ) if test]
            self.rowheads = [r for test, r in zip( mask, self.rowheads ) if test]
            if transposed: self.transpose( )
            self.remap( )
            self.report( "new size is", self.size( ) )
            return None
        # (2) return rows that passed as new table
        else:
            new_table = Table(
                data = [row[:] for test, row in zip( mask, self.data ) if test],
                rowheads = [r for test, r in zip( mask, self.rowheads ) if test],
                colheads = self.colheads[:],
                origin = self.origin,
                missing = self.missing,
                transposed = self.transposed,
                verbose = self.verbose,
            )
            if transposed:
                self.transpose( )
                new_table.transpose( )
            return new_table

    #### METHODS THAT USE FILTER ####

    def grep( self, patterns, f=None, focus=None, **kwargs ):
        """ restrict rows to those whose focal position matches a pattern """
        focus = focus if f is None else f
        if isinstance( patterns, str ):
            patterns = [patterns]
        self.report( "applying grep", "focus=", focus, "patterns=", pretty_list( patterns ), kwargs )
        anymatch = lambda x: any( [re.search( p, x ) for p in patterns] )
        function = lambda r: anymatch( r if focus is None else self.get( r, focus ) )
        return self.filter( function, **kwargs )

    def select( self, choices, f=None, focus=None, **kwargs ):
        """ select rows whose focal entry is in choices """
        focus = focus if f is None else f
        if isinstance( choices, str ):
            choices = [choices]
        self.report( "applying select", "focus=", focus, "choices=", pretty_list( choices ), kwargs )
        choices = set( choices )
        function = lambda r: (r if focus is None else self.get( r, focus )) in choices
        return self.filter( function, **kwargs )

    def delete( self, choices, f=None, focus=None, **kwargs ):
        """ delete rows whose focal entry is in choices """
        focus = focus if f is None else f
        if isinstance( choices, str ):
            choices = [choices]
        self.report( "applying delete", "focus=", focus, "choices=", pretty_list( choices ), kwargs )
        choices = set( choices )
        # only difference from <select> is <not in> here
        function = lambda r: (r if focus is None else self.get( r, focus )) not in choices
        return self.filter( function, **kwargs )

    # **** tested to here ****
    
    def head( self, header, **kwargs ):
        """ keep only rows up to header """
        self.report( "applying head", "header=", header, kwargs )
        function = lambda r: self.rowdex( r ) <= self.rowdex( header )
        return self.filter( function, **kwargs )

    def limit( self, header, criterion, **kwargs ):
        """ keep only rows where field value satisfies numerical criterion """
        M = re.search( "([<>=]+) *(.*)", criterion ).groups( )
        if M is None:
            zu.die( criterion, "is not a valid limit criterion" )
        op, threshold = M.groups( )
        threshold = float( threshold )
        choices = { 
            "<" : lambda x: float( x ) <  threshold,
            "<=": lambda x: float( x ) <= threshold,
            ">" : lambda x: float( x ) >  threshold,
            ">=": lambda x: float( x ) >= threshold,
            }
        selector = choices[op]
        function = lambda r: selector( self.get( r, header ) )                                       
        self.report( "applying limit, requiring field", index, "to be", op, threshold, kwargs )
        return self.filter( function, **kwargs )

    def nontrivial( self, minvalue=0, mincount=1, **kwargs ):
        """ applies to numerical table: keep features ( row ) that exceed specified level in specified # of samples """
        function = lambda r: mincount <= len( [k for k in self.row( r ) if k >= minlevel] )
        self.report( "applying nontrivial", "requiring at least", mincount, "values exceeding", minlevel, kwargs )
        return self.filter( function, **kwargs )

    # **** updated to here ****
    
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
            stratum = self.get( rowhead, focus )
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
            [rowhead2] + [table2.get( rowhead2, colhead ) if colhead in table2.colmap else c_na for colhead in self.colheads] 
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
                self.data[i] += [c_na for j in aIndex]
        self.remap()
        self.report( "extended with cols from", table2.source, "new size is", self.size() )

    def merge( self, table2 ):
        """ slightly faster merge conducted as an extend and augment """
        self.extend( table2 )
        self.augment( table2 )

    # ---------------------------------------------------------------
    # methods for filling "empty" cells
    # ---------------------------------------------------------------

    def blank2na( self, value=c_na ):
        """ Anything that doesn't match a non-space char is filled with na """
        self.apply_entries( lambda k: k if re.search( "[^\s]", str( k ) ) else value )
        
    def na2zero( self, value=0 ):
        """ Convert NAs to zero values """
        self.apply_entries( lambda k: value if k == c_na else k )

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

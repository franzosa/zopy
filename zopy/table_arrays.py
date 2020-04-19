#!/usr/bin/env python

"""
New zopy table class
"""

# ---------------------------------------------------------------
# imports 
# ---------------------------------------------------------------

import os
import sys
import re
import csv

import numpy as np
from numpy import array, ndarray
from scipy.stats import rankdata

from zopy.utils import reader, try_open, die, warn

# ---------------------------------------------------------------
# constants 
# ---------------------------------------------------------------

c_default_origin    = "#HEADERS"
c_na                = "#N/A"
c_max_print_choices = 3

# ---------------------------------------------------------------
# helper functions
# ---------------------------------------------------------------

def coerce( matrix ):
    if type( matrix ) is ndarray:
        return matrix
    else:
        try:
            return array( matrix )
        except:
            sys.exit( "Could not coerce matrix to 2d array" )

def load_from_path( path ):
    with try_open( path ) as fh:
        return load_from_handle( fh )

def load_from_handle( fh ):
    return coerce( [row for row in reader( fh )] )

def multiplex( choices ):
    return set( choices ) if hasattr( choices, "__iter__" ) else {choices}

def anymatch( string, patterns ):
    test = False
    for p in patterns:
        if re.search( p, string ):
            test = True
            break
    return test

# ---------------------------------------------------------------
# main table class
# ---------------------------------------------------------------

class table:

    """ """
    
    def __init__ ( 
        self, 
        path=None, 
        fh=None, 
        matrix=None, 
        data=None, 
        rowheads=None, 
        colheads=None, 
        headers=True,
        name=None,
        verbose=True,
        numeric=False,
        ):

        """ """

        self.data = None
        self.rowheads = None
        self.colheads = None
        self.axheads = []
        self.origin = c_default_origin
        self.name = name
        self.shape = []
        self.is_verbose = verbose
        self.is_numeric = numeric

        if data is not None:
            self.data = coerce( data )
            self.rowheads = rowheads if rowheads is not None \
                else range( self.data.shape[0] )
            self.colheads = colheads if colheads is not None \
                else range( self.data.shape[1] )
        else:
            if path is not None:
                matrix = load_from_path( path )
            elif fh is not None:
                matrix = load_from_handle( fh )
            elif matrix is not None:
                matrix = coerce( matrix )
            else:
                die( "No loading option." )
            if not headers:
                self.data = matrix
                self.rowheads = range( self.data.shape[0] )
                self.colheads = range( self.data.shape[1] )
            else:
                self.data = matrix[1:, 1:]
                self.rowheads = list( matrix[1:, 0] )
                self.colheads = list( matrix[0, 1:] )
                self.origin = matrix[0][0]
        self.axheads = [self.rowheads, self.colheads]
        self.index()
                                       
    def index( self ):    
        """ """                                   
        self.shape = self.data.shape
        self.nrows, self.ncols = self.shape
        assert len( self.rowheads ) == self.nrows, "Dimension issue"
        assert len( self.colheads ) == self.ncols, "Dimension issue"      
        self.rowmap = {}
        self.colmap = {}
        for i, value in enumerate( self.rowheads ):
            while value in self.rowmap:
                warn( "Duplicate rowhead", value, "defined at", self.rowmap[value] )
                value += "-dup"
                warn( "  trying", value )
            self.rowmap[value] = i
        for j, value in enumerate( self.colheads ):
            while value in self.colmap:
                warn( "Duplicate colhead", value, "defined at", self.colmap[value] )
                value += "-dup"
                warn( "  trying", value )
            self.colmap[value] = j

    # ---------------------------------------------------------------
    # object methods
    # ---------------------------------------------------------------

    def __getitem__( self, coords ):
        return self.data[r, :]

    def __repr__( self ):
        r, c = self.shape
        r = min( r, 5 )
        c = min( c, 5 )
        outline = ""
        outline += "\t".join( map( str, [self.origin] + self.colheads[0:c] ) ) + "\n"
        for i in range( r ):
            outline += "\t".join( map( str, [self.rowheads[i]] + list( self.data[i][0:c] ) ) ) + "\n"
        return outline

    # ---------------------------------------------------------------
    # custom utils
    # ---------------------------------------------------------------
    
    def rowdex( self, index ):
        """ Convert numerical or string rowhead to numerical rowhead index """
        return index if isinstance( index, int ) else self.rowmap[index]

    def coldex( self, index ):
        """ Convert numerical or string colhead to numerical colhead index """
        return index if isinstance( index, int ) else self.colmap[index]

    def report( self, *args ):
        """ generic reporter """
        if self.is_verbose:
            print >>sys.stderr, self.name, ":", " ".join( [str( k ) for k in args] )

    def transpose( self ):
        """ much, much faster than old method """
        self.rowheads, self.colheads = self.colheads, self.rowheads
        self.data = self.data.swapaxes( 0, 1 )
        self.index()
        return self

    def rowsort( self ):
        """ sorts the rows based on rowheads """
        order = sorted( range( self.nrows ), key=lambda x: self.rowheads[x] )
        self.data = self.data[order, :]
        self.rowheads = sorted( self.rowheads )
        self.index()
        return self

    def colsort( self ):
        """ sorts the cols based on colheads """
        order = sorted( range( self.ncols ), key=lambda x: self.colheads[x] )
        self.data = self.data[:, order]
        self.colheads = sorted( self.colheads )
        self.index()
        return self

    # ---------------------------------------------------------------
    # write table to stdout/disk
    # ---------------------------------------------------------------
        
    def write( self, path=None, gzip=False ):
        """ 
        **** implement gzipped writing ****
        """
        with ( try_open( path ) if path is not None else sys.stdout ) as fh: 
            writer = csv.writer( fh, delimiter="\t", quotechar="", quoting=csv.QUOTE_NONE )
            writer.writerow( [self.origin] + list( self.colheads ) )
            for rowhead, row in zip( self.rowheads, self.data ):
                writer.writerow( [rowhead] + list( row ) )

    # ---------------------------------------------------------------
    # appliers
    # ---------------------------------------------------------------

    #def set ( self, r, c, value ):
        
    def apply_rowheads( self, function ):
        self.rowheads = map( function, self.rowheads )
        self.index()
                                    
    def apply_colheads( self, function ):
        self.colheads = map( function, self.colheads )
        self.index

    #def apply_entries( self, func ):
        #vfunc = np.vectorize( func )
        #self.data = vfunc( self.data )

    #def pretty( self ):
        #apply_entries( lambda x: "%.4f" % x )
 
    # ---------------------------------------------------------------
    # slicing
    # ---------------------------------------------------------------

    """
    def segment( self, index, axis=0 ):
        if axis == 0:
            i = self.rowdex( index )
            return self.data[i, :]
        elif axis == 1:
            j = self.coldex( index )
            return self.data[:, j]
            """

    """
    def row ( self, index, start=1 ):      
    def col ( self, index, start=1 ):
    def rowdict ( self, index ):
    def coldict ( self, index ):
    def entry ( self, r, c ):
    """
                            
    # ---------------------------------------------------------------
    # generators
    # ---------------------------------------------------------------
    
    def iter_rows ( self ):
        for i in range( self.nrows ):
            yield self.rowheads[i], self.data[i, :]

    def iter_cols ( self ):
        for j in range( self.ncols ):
            yield self.colheads[j], self.data[:, j]
        
    # ---------------------------------------------------------------
    # filter a table on a function of its headers
    # ---------------------------------------------------------------

    def filter ( self, 
                 function, 
                 vectors=False, 
                 transposed=False, t=False, 
                 invert=False, v=False,
                 new=False, ):
        # process shorthand
        transposed = any( [transposed, t] )
        invert = any( [invert, v] )
        if transposed:
            self.transpose()
        new_rowheads = []
        for header, row in self.iter_rows():
            test = function( header ) if not vectors else function( row )
            if (test and not invert) or (not test and invert):
                new_rowheads.append( header )
        new_data = self.data[[self.rowmap[k] for k in new_rowheads]]
        if not new:
            self.rowheads = new_rowheads
            self.data = new_data
            self.index()
            if transposed:
                self.transpose()
            return self
        else:
            new_table = table( 
                data=new_data, 
                rowheads=new_rowheads[:], 
                colheads=self.colheads[:], 
                )
            if transposed:
                self.transpose()
                new_table.transpose()
            return new_table

    # ---------------------------------------------------------------
    # methods that call filter
    # ---------------------------------------------------------------

    def select( self, choices, field=None, **kwargs ):
        choices = multiplex( choices )
        if field is None:
            def inner( header ):
                return header in choices
        else:
            def inner( header ):
                cpos = self.colmap[field]
                rpos = self.rowmap[header]
                return self.data[rpos, cpos] in choices
        return self.filter( inner, **kwargs )

    def delete( self, choices, **kwargs ):
        return self.select( choices, invert=True, **kwargs )

    def grep( self, choices, field=None, **kwargs ):
        choices = multiplex( choices )
        if field is None:
            def inner( header ):
                return anymatch( header, choices )
        else:
            def inner( header ):
                cpos = self.colmap[field]
                rpos = self.rowmap[header]
                return anymatch( self.data[rpos, cpos], choices )
        return self.filter( inner, **kwargs )

    def head( self, header, **kwargs ):
        return self.filter( lambda k: self.rowdex( k ) <= self.rowdex( header ), **kwargs )

    def apfilter( self, minabund=0, minprev=1, **kwargs ):
        if not self.is_numeric:
            die( "Can't apfilter non-numeric table:", self.name )
        if type( minprev ) is float:
            self.report( "will interpret minimum prevalence", minprev, "as a fraction of samples" )
        if not ( kwargs.get( "t", False ) or kwargs.get( "transposed", False ) ):
            self.report( "using apfilter on non-transposed table is not standard" )
        def inner( vector, minabund=minabund, minprev=minprev ):
            if type( minprev ) is float:
                minprev = int( len( vector ) * minprev )
            return list( vector >= minabund ).count( True ) >= minprev
        return self.filter( inner, vectors=True, **kwargs )

    # ---------------------------------------------------------------
    # mathmatical operations
    # ---------------------------------------------------------------

    def float( self ):
        self.data = self.data.astype( float )
        self.is_numeric = True

    def colnorm( self, basis=1.0 ):
        sums = sum( self.data.transpose() )
        self.data = self.data * basis / sums

#!/usr/bin/env python

import os
import sys
import re
import argparse

from zopy.utils import iter_rows, warn, die

#-------------------------------------------------------------------------------
# helper functions (incomplete)
#-------------------------------------------------------------------------------

def verify_dict( d ):
    bad = False
    ll = set( )
    for k, v in d:
        if type( k ) is not str:
            bad = True
        elif type( v ) is not list:
            bad = True
        ll.add( len( v ) )
    if len( ll ) != 1:
        bad = True
    if bad:
        die( "Can't convert dict to Frame" )

def verify_list_of_lists( aa ):
    bad = False
    ll = set( )
    for a in aa:
        if type( a ) is not list:
            bad = True
        ll.add( len( a ) )
    for k in aa[0]:
        if type( k ) is not str:
            bad = True
    if len( ll ) != 1:
        bad = True
    if bad:
        die( "Can't convert lists to Frame" )

#-------------------------------------------------------------------------------
# class start
#-------------------------------------------------------------------------------
        
class Frame:

    #-------------------------------------------------------------------------------
    # init from file
    #-------------------------------------------------------------------------------
    
    def __init__( self, source=None, allowed=None ):
        self.source = source if source is not None else sys.stdin
        self.data = {}
        rows = iter_rows( self.source )
        self.fields = rows.next( )
        for row in rows:
            for h, v in zip( self.fields, row ):
                if allowed is None or h in allowed:
                    self.data.setdefault( h, [] ).append( v )
        if allowed is not None:
            self.fields = [k for k in self.fields if k in allowed]
        # add robustness to fields-only file
        for f in self.fields:
            self.data.setdefault( f, [] )

    #-------------------------------------------------------------------------------
    # utilities
    #-------------------------------------------------------------------------------
               
    def __getitem__( self, field ):
        if field not in self.data:
            die( "Non-existing field:", field )
        return self.data[field]

    def __repr__( self ):
        nf = len( self.fields )
        nv = len( self[self.fields[0]] )
        return "[Frame from <{}> with <{}> fields of length <{}>]".format( self.source, nf, nv )

    def check( self, fields ):
        if type( fields ) is str:
            fields = [fields]
        # quick test if all fields are accessible
        for f in fields:
            self[f]
        return fields

    def zip( self, fields ):
        for items in zip( *[self[f] for f in self.check( fields )] ):
            yield items

    def rowdicts( self ):
        size = len( self.data[self.fields[0]] )
        for i in range( size ):
            d = {}
            for f in self.fields:
                d[f] = self.data[f][i]
            yield d
            
    #-------------------------------------------------------------------------------
    # map operations
    #-------------------------------------------------------------------------------
    
    def map( self, fields, function ):
        for f in self.check( fields ):
            self.data[f] = map( function, self.data[f] )

    def sub( self, fields, from_str, to_str ):
        self.map( fields, lambda x: re.sub( from_str, to_str, x ) )

    def int( self, fields ):
        self.map( fields, int )

    def float( self, fields ):
        self.map( fields, float )
        
    #-------------------------------------------------------------------------------
    # filter operations
    #-------------------------------------------------------------------------------
        
    def filter( self, fields, function ):
        index = [i for i, args in enumerate( zip( *[self[k] for k in self.check( fields )] ) ) \
                 if function( *args )]
        for f, values in self.data.items( ):
            self.data[f] = [values[i] for i in index]
            
    def intersect( self, fields, collection ):
        self.filter( fields, lambda x: x in collection )

    #-------------------------------------------------------------------------------
    # dict operations
    #-------------------------------------------------------------------------------
        
    def dict( self, key_fields, value_field, append=False ):
        ret = {}
        lossy = False
        # generate keys
        key_fields = self.check( key_fields )
        if len( key_fields ) == 1:
            keys = self.data[key_fields[0]]
        else:
            keys = [tuple_key for tuple_key in zip( *[self[k] for k in key_fields] )]
        # populate dictionary
        for k, v in zip( keys, self[value_field] ):
            if append:
                ret.setdefault( k, [] ).append( v )
            elif k in ret and ret[k] != v:
                lossy = True
            else:
                ret[k] = v
        if lossy:
            warn( "One to many mapping in <{}>: {} --> {}".format(
                self.source,
                key_fields,
                value_field,
            ) )
        return ret

#-------------------------------------------------------------------------------
# class end
#-------------------------------------------------------------------------------

from __future__ import print_function

from zopy.utils import qw
from zopy.table import Table

T1 = qw( """
+ 1 2 3 4 5
A 0 1 0 0 1
B 1 0 0 1 0
C 0 1 1 0 1
D 1 0 1 1 0
""" )

with open( "temp.txt", "w" ) as fh:
    for l in T1:
        print( l.replace( " ", "\t" ), file=fh )

"""
print( "\nTest loading from a nested list" )
aa = [
    ["!", "1", "2"],
    ["A", "X", "Y"],
]
T = Table( aa )
T.write( )
        
print( "\nTest loading from a nested dict" )
dd = {
    "A":{"1":"1", "2":"0"},
    "B":{"2":"0", "3":"1"},
}     
T = Table( dd )
T.write( )

print( "\nTest loading from a nested dict - fixed colheads" )
T = Table( dd, colheads=["1", "3"] )
T.write( )

print( "\nTest loading from a nested dict - fixed rowheads" )
T = Table( dd, rowheads=["B", "A"] )
T.write( )
"""

print( "\nTest loading from file" )
T = Table( "temp.txt" )
T.write( )

"""
print( "\nTest transpose" )
T.transpose( )
T.write( )

print( "\nTest slicing" )
T.transpose( )
print( "Row B=", T.row( "B" ) )
print( "Col 4=", T.col( "4" ) )
print( "Entry B, 4=", T.get( "B", "4" ) )
"""

"""
print( "\nTest sorting" )
T.rowsort( order=["C", "D"] )
T.write( )
T.colsort( order=["4", "3", "2"] )
T.write( )
#T.colsort( order=["5"] )
#T.write( )
"""

"""
print( "\nTest setting" )
T.set( "A", "1", "@" )
T.write( )
"""

"""
print( "\nTest appliers" )
T.apply_rowheads( lambda x: x.lower( ) )
T.apply_colheads( lambda x: x + x )
T.apply_entries( lambda x: -int( x ) )
T.write( )
"""

"""
print( "\nTest grep - new" )
T2 = T.grep( "B|C", new=True )
T2.write( )

print( "\nTest grep - new, inverted" )
T2 = T.grep( "B|C", new=True, i=True )
T2.write( )

print( "\nTest grep - new, transposed" )
T2 = T.grep( "2|3|4", new=True, t=True )
T2.write( )

print( "\nTest grep - in place" )
T.grep( "B|C" )
T.write( )
"""

"""
print( "\nTest grep - focused" )
T.grep( "1", focus="4" )
T.write( )
T.grep( "1", focus="B", t=True )
T.write( )
"""

"""
print( "\nTest select" )
T.select( ["0", "1"], focus="4" )
T.select( "0", focus="D", t=True )
T.write( )
"""

"""
print( "\nTest delete" )
T.delete( ["A", "C"] )
T.delete( "1", focus="B", t=True )
T.write( )
"""

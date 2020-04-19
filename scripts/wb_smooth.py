#! /usr/bin/env python

"""
Compositional Witten-Bell smoothing 
Adapted from Franzosa et al. PNAS 2014
===============================================
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

import csv, argparse

c_fNonCompDelta = 0.01

def funcLoadTable ( strPath ):
	with open( strPath ) as fh:
		astrHeaders = None
		astrFeatures = []
		aafData = []
		for astrLine in csv.reader( fh, dialect="excel-tab" ):
			if astrHeaders is None:
				astrHeaders = astrLine
			else:
				astrFeatures.append( astrLine[0] )
				aafData.append( map( float, astrLine[1:] ) )
	return aafData, astrFeatures, astrHeaders
	
def funcTranspose ( aaData ):
	return [[aaData[iRow][iCol] for iRow in range( len( aaData ) )] \
		for iCol in range( len( aaData[0] ) )]
	
def funcWBSmooth ( afSample ):
	assert abs( sum( afSample ) - 1.0 ) < c_fNonCompDelta, \
		"This doesn't look like compositional data (col sum !~ 1.0)"
	afNonZero = filter( lambda x: x > 0, afSample )
	iN = int( 1 / min( afNonZero ) )
	iT = len( afNonZero )
	iZ = len( afSample ) - iT
	def funcInner ( fValue ):
		if fValue == 0:
			return iT / float( iZ ) / float( iN + iT )
		else:
			return ( fValue * iN ) / float( iN + iT )
	return map( funcInner, afSample )

def main ( ):
	parser = argparse.ArgumentParser()
	parser.add_argument( '-i', "--input",
		help="Input compositional PCL file" )
	parser.add_argument( '-o', "--output", 
		help="Output Witten-Bell smoothed compositional PCL file" )
	args = parser.parse_args()
	aafData, astrFeatures, astrHeaders = funcLoadTable( args.input )
	aafData = funcTranspose( map( funcWBSmooth, funcTranspose( aafData ) ) )
	with open( args.output, "wb" ) as fh:
		Writer = csv.writer( fh, dialect="excel-tab" )
		Writer.writerow( astrHeaders )
		for iRow, afValues in enumerate( aafData ):
			Writer.writerow( [astrFeatures[iRow]] + afValues )

if __name__ == "__main__":
	main( ) 

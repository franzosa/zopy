#! /usr/bin/env python

"""
Make the raw material for the strain specific marker plots
"""

import os, sys, re, glob, argparse
import numpy as np
from scipy.stats.mstats import mquantiles
import matplotlib as mpl
import matplotlib.pyplot as plt
from zopy.utils import path2name
from zopy.table2 import table
import zopy.mplutils as mplutils
from zopy.stats import trunc_mean

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

c_iReadLength = 100
c_fDivisor = 1000 / float( c_iReadLength )
c_fMinCoverage = 0.05

# ---------------------------------------------------------------
# rescaling function
# ---------------------------------------------------------------

def funcMinNonZero ( aValues ):
	aNonZero = [k for k in aValues if k > 0]
	return min( aNonZero ) if len( aNonZero ) > 0 else None

def funcTrimmedMax( values ):
	# flatten
	if isinstance( values[0], list ):
		values = [k for row in values for k in row]
	q1, q2, q3 = mquantiles( values )
	upper_inner_fence = q3 + 1.5 * ( q3 - q1 )
	outliers = [k for k in values if k > upper_inner_fence]
	if len( outliers ) > 0:
		print >>sys.stderr, "Outliers removed in trimmed max:", len( outliers ), len( outliers ) / float( len( values ) )
	return max( [k for k in values if k <= upper_inner_fence] )

def funcRescale ( aaData, **kwargs ):
	""" rescales the data in place """
	scaling = kwargs["scaling"]
	bins = kwargs["bins"]
	gmax = max( [max( aRow ) for aRow in aaData] )
	gmin_nonzero = min( [funcMinNonZero( aRow ) for aRow in aaData if max( aRow ) > 0] )
	trimmed_gmax = funcTrimmedMax( aaData )
	for i, aRow in enumerate( aaData ):
		multiplier = 0.25 if trunc_mean( aRow ) / c_fDivisor < c_fMinCoverage else 1
		rmax = max( aRow )
		rmin_nonzero = funcMinNonZero( aRow )
		trimmed_rmax = funcTrimmedMax( aRow )
		for j, value in enumerate( aRow ):
			if value == 0:
				continue
			elif scaling == "binary":
				aaData[i][j] = 1
			elif scaling == "norm":
				aaData[i][j] = aaData[i][j] / float( gmax )
			elif scaling == "rownorm":
				aaData[i][j] = aaData[i][j] / float( rmax )
			elif scaling == "trimnorm":
				aaData[i][j] = aaData[i][j] / float( trimmed_gmax ) if aaData[i][j] < trimmed_gmax else 1
			elif scaling == "trimrownorm":
				aaData[i][j] = aaData[i][j] / float( trimmed_rmax ) if aaData[i][j] < trimmed_rmax else 1
			elif scaling == "special":
				aaData[i][j] = np.sqrt( aaData[i][j] / float( trimmed_rmax ) ) if aaData[i][j] < trimmed_rmax else 1
				aaData[i][j] *= multiplier
			elif scaling == "bins":
				for k, b in enumerate( bins ):
					if value <= b:
						aaData[i][j] = ( k + 1 ) / float( 1 + len( bins ) )
						break
				else:
					aaData[i][j] = 1
			"""
			THESE DON'T REALLY WORK SINCE THEY FORCE THE MIN TO ZERO
			elif scaling == "lognorm" and value > 0:
				aaData[i][j] = ( np.log10( value ) - np.log10( gmin_nonzero ) ) / ( np.log10( gmax ) - np.log10( gmin_nonzero ) )
			elif scaling == "rowlognorm" and value > 0:
				aaData[i][j] = ( np.log10( value ) - np.log10( rmin_nonzero ) ) / ( np.log10( rmax ) - np.log10( rmin_nonzero ) )
			"""

# ---------------------------------------------------------------
# main function
# ---------------------------------------------------------------

def barcoder ( ax, aaData, aaHighlight=None, aLabels=None, show_xticks=True, show_border=True, 
			   color="0.5", highlight_color="orange", background="white", linewidth=0.5,
			   scaling="binary", bins=None, show_coverage=False ):
	""" makes a 'recruitment plot' a.k.a. metaphlan marker barcode """
	aaData_original = [row[:] for row in aaData] 
	funcRescale( aaData, scaling=scaling, bins=bins )
	aLabels = aLabels if aLabels is not None else [str( k ) for k in range( len( aaData ) )]
	aColors = color if isinstance( color, list ) else [color for aRow in aaData]
	# set for "book style" reading (first row at the top)
	aLabels.reverse()
	aaData.reverse()
	if aaHighlight is not None:
		aaHighlight.reverse()
	# configure ax size
	ax.set_xlim( 0, len( aaData[0] ) )
	ax.set_ylim( 0, len( aLabels ) )
	# plot the bars
	for i, aRow in enumerate( aaData ):
		for j, value in enumerate( aRow ):
			if value > 0:
				ax.bar( 
					j,
					value,
					bottom = i + 0.5 - value / 2.0,
					width=1.0,
					#edgecolor=highlight_color if ( aaHighlight is not None and aaHighlight[i][j] == True ) else "none",
					edgecolor="none",
					color=highlight_color if ( aaHighlight is not None and aaHighlight[i][j] == True ) else aColors[i],
					zorder=2 if ( aaHighlight is not None and aaHighlight[i][j] == True ) else 1,
					)

	# misc graphical settings
	ax.patch.set_facecolor( background )
	mplutils.funcSetTickParams( ax )
	ax.set_yticks( [k + 0.5 for k in range( len( aLabels ) )] )
	ax.set_yticklabels( aLabels, size=7 )
	aMinorTicks = [k for k in range( 1, len( aLabels ) )]
	ax.yaxis.set_ticks( aMinorTicks, minor=True )
	mplutils.funcGrid( ax, xaxis=False, minor=True, linewidth=linewidth, color=background, zorder=3 )
	mplutils.funcHideY( ax, major=False )
	# configure the border
	mplutils.funcBorder( ax, linewidth=linewidth, color=background, visible=show_border )
	# on off graphical settings
	if not show_xticks:
		mplutils.funcHideX( ax )
	else:
		[tick.label.set_fontsize( 7 ) for tick in ax.xaxis.get_major_ticks()]
		ax.set_xlabel( "clade-specific markers" )
	# show coverage stats
	if show_coverage:
		# note: aaData is transformed; must use original (which isn't reversed yet)
		coverage = [trunc_mean( row ) / c_fDivisor for row in aaData_original]
		coverage.reverse()
		coverage = map( lambda x: "%.1fx" % ( x ), coverage )
		ax2 = ax.twinx()
		ax2.tick_params( axis="y", which="major", direction="out", left="off", right="on", width=1.0 )
		ax2.set_ylim( ax.get_ylim() )
		ax2.set_yticks( ax.get_yticks() )
		ax2.set_yticklabels( coverage, size=7 )
		ax2.set_ylabel( "coverage estimate" )

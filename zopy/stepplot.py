#! /usr/bin/env python

"""
---------------------------------------
Eric Franzosa ( eric.franzosa@gmail.com )
"""

import os, sys, re, glob, argparse
from math import log10
import numpy as np
import matplotlib.pyplot as plt
import zopy.mplutils as mu

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

c_fStepWidth = 0.4
c_fHalfStepWidth = c_fStepWidth / 2.0
c_fStepBuffer = 0.1

# ---------------------------------------------------------------
# functions for making step plots
# ---------------------------------------------------------------

def stepplot ( ax, aaData, colors=None, sample_colors=None, thickness=3.0, alpha=0.5, connect_color="gray", median=False ):
    """
    The rows of aaData are samples
    The columns are a type of step (~group in a barplot)
    """
    iGroups = len( aaData[0] )
    aGroupIndex = mu.funcGroupIndex( ax, iGroups )
    if colors is None:
        colors = ["cornflowerblue" for k in aGroupIndex]
    elif type( colors ) is str:
        colors = [colors for k in aGroupIndex]
    # draw hashes
    for i, aSteps in enumerate( aaData ):
        for j in range( len( aSteps ) ):
            if aSteps[j] is not None:
                aX = [ aGroupIndex[j] - c_fHalfStepWidth, 
                       aGroupIndex[j] + c_fHalfStepWidth ]
                aY = [ aSteps[j], aSteps[j] ]
                color = colors[j]
                if sample_colors is not None:
                    color = sample_colors[i]
                ax.add_line( plt.Line2D( aX, aY, alpha=alpha, lw=thickness, color=color ) )   
    # draw connections
    for i, aSteps in enumerate( aaData ):
        for j in range( len( aSteps ) ):
            if j > 0:
                if aSteps[j] is not None and aSteps[j-1] is not None:
                    aX = [ aGroupIndex[j-1] + c_fHalfStepWidth + c_fStepBuffer, 
                           aGroupIndex[j]   - c_fHalfStepWidth - c_fStepBuffer ]
                    aY = [ aSteps[j-1],      aSteps[j]      ]
                    color = connect_color
                    if sample_colors is not None:
                        color = sample_colors[i]
                    ax.add_line( plt.Line2D( aX, aY, alpha=alpha, lw=thickness / 2.0, color=color ) )
    # typical ax settings
    ax.xaxis.set_ticks( aGroupIndex )
    # add median?
    if median:
        mdata = [[] for k in aaData[0]]
        for i in range( len( aaData[0] ) ):
            for sample in aaData:
                mdata[i].append( sample[i] )
        mdata = [map( np.median, mdata )]
        stepplot( ax, mdata, colors="black", thickness=thickness*2, alpha=1.0, connect_color="black" )

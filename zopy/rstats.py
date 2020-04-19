#! /usr/bin/env python

import os, sys, re, glob, argparse
from rpy import r
from zopy.table2 import table, nesteddict2table

def spearman ( values1, values2 ):
    """ python wrapper for R's spearman """
    result = r.cor_test( values1, values2, method="spearman" )
    return result["estimate"]["rho"], result["p.value"]

def wilcoxon ( values1, values2, paired=False ):
    """ python wrapper for R's wilcoxon, optionally paired ( default=False ) """
    return r.wilcox_test( values1, values2, paired=paired )["p.value"]

def anova ( values, factor1, factor1name="factor1" ):
    """ python wrapper for a one-way ANOVA in R """
    # build a dataframe for R
    dataframe = {}
    dataframe["feature"] = values
    dataframe["factor1"] = factor1
    r.assign( "df", dataframe )
    r( "df$factor1 <- factor( df$factor1 )" )
    # run the model
    results = r( "anova( lm( df$feature ~ df$factor1 ) )" )
    r( "rm( list=ls() )" )
    # convert R results to table
    colheads = ["Df", "Sum Sq", "Mean Sq", "F value", "Pr( >F )"]
    rowheads = [factor1name, "error"]
    ndictData = {}
    for rowhead in results.keys():
        for index, name in zip( range( len( rowheads ) ), rowheads ):
            dictName = ndictData.setdefault( name, {} )
            dictName[rowhead] = results[rowhead][index]
    # return as zopy table
    return nesteddict2table( ndictData, rowheads, colheads )

def anova2 ( values, factor1, factor2, factor1name="factor1", factor2name="factor2", interaction=True ):
    """ python wrapper for a two-way anova in R with optional interaction term ( default=True ) """
    # build a dataframe for R
    dataframe = {}
    dataframe["feature"] = values
    dataframe["factor1"] = factor1
    dataframe["factor2"] = factor2
    r.assign( "df", dataframe )
    r( "df$factor1 <- factor( df$factor1 )" )
    r( "df$factor2 <- factor( df$factor2 )" )
    # run the model
    results = r( "anova( lm( df$feature ~ df$factor1 %s df$factor2 ) )" % ( "*" if interaction else "+" ) )
    r( "rm( list=ls() )" )
    # convert R results to table
    colheads = ["Df", "Sum Sq", "Mean Sq", "F value", "Pr( >F )"]
    rowheads = [factor1name, factor2name]
    rowheads += ["int term", "error"] if interaction else ["error"]
    ndictData = {}
    for rowhead in results.keys():
        for index, name in zip( range( len( rowheads ) ), rowheads ):
            dictName = ndictData.setdefault( name, {} )
            dictName[rowhead] = results[rowhead][index]
    # return as zopy table
    return nesteddict2table( ndictData, rowheads, colheads )

"""
# test spearman
if __name__ == "__main__":
    from scipy.stats import spearmanr
    from random import random, choice
    x = [random() for k in range( 30 )]
    y = [x[i] + random() for i in range( len( x ) )]
    print spearman( x, y )
    print spearmanr( x, y )
    x = [choice( range( 5 ) ) for k in range( 30 )]
    y = [x[i] + random() for i in range( len( x ) )]
    print spearman( x, y )
    print spearmanr( x, y )
"""

"""
# test anova
if __name__ == "__main__":
    from random import random, choice
    def test ( n=100, s=1 ):
            f1 = [choice( [-s,0,s] ) for i in range( n )]
            v = [random() + f1[i] for i in range( n )]
            return v, f1
    def tableprint ( t ):
        for row in t.data:
            print "\t".join( [str( k ) for k in row] )
    # print "test 1: high signal2noise"
    v, f1 = test()
    tableprint( anova( v, f1 ) )
    # print "test 2: low signal2noise
    v, f1 = test( s=0.1 )
    tableprint( anova( v, f1 ) )
"""

"""
# test anova2
if __name__ == "__main__":
    from random import random, choice
    def test ( n=100, s=1, interact=1 ):
            f1 = [choice( [-s,0,s] ) for i in range( n )]
            f2 = [choice( [-s,0,s] ) for i in range( n )]
            v = [random() + f1[i] + f2[i] + interact * f1[i] * f2[i] for i in range( n )]
            return v, f1, f2
    def tableprint ( t ):
        for row in t.data:
            print "\t".join( [str( k ) for k in row] )
    # print "test 1: high signal2noise with interaction"
    v, f1, f2 = test()
    tableprint( anova2( v, f1, f2 ) )
    # print "test 2: high signal2noise with no interaction"
    v, f1, f2 = test( interact=0 )
    tableprint( anova2( v, f1, f2 ) )
    # print "test 3: low signal2noise with no interaction"
    v, f1, f2 = test( s=0.1, interact=0 )
    tableprint( anova2( v, f1, f2 ) )
    # print "test 4: low signal2noise with no interaction, interaction unmodeled"
    v, f1, f2 = test( s=0.1, interact=0 )
    tableprint( anova2( v, f1, f2, interaction=False ) )
"""

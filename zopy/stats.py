#!/usr/bin/env python

import os
import sys
import re
import glob
import random
import math

from numpy import median, mean, std
from scipy.stats import binom, rankdata, spearmanr, mannwhitneyu
from scipy.stats import fisher_exact as scipy_fisher_exact
from scipy.stats.mstats import mquantiles
from collections import Counter

from zopy.utils import warn, die

# ---------------------------------------------------------------
# utilities
# ---------------------------------------------------------------

def pretty_pvalue ( pvalue ):
    return "***" if pvalue < 1e-3 else ( "**" if pvalue < 1e-2 else ( "*" if pvalue < 0.05 else "ns" ) )

def is_homogeneous ( array ):
    result = False
    # quick check will exclude most arrays
    if array[0] == array[1]:
        if len( set( array ) ) == 1:
            result = True
    return result

# ---------------------------------------------------------------
# robust stats
# ---------------------------------------------------------------

def trunc_mean ( aValues, tail=0.1 ):
    """ truncated mean """
    low, high = mquantiles( aValues, [tail, 1-tail] )
    return mean( [k for k in aValues if low <= k <= high] )

def trunc_spearman ( aX, aY, minlevel=0, clean=True, verbose=True ):
    """ wrapper around spearman that warns about 0,0 points """
    counter = 0
    aX2, aY2 = [], []
    for x, y in zip( aX, aY ):
        bad = ( x <= minlevel and y <= minlevel )
        counter += 1 if bad else 0
        if not clean or not bad:
            aX2.append( x )
            aY2.append( y )
    if verbose:
        report = "%d ( %.1f%% ) min,min pairs" % ( counter, 100 * counter / float( len( aX ) ) )
        print >>sys.stderr, "spearman with", report, "excluded" if clean else "included ( WARNING! )"
    return spearmanr( aX2, aY2 )

def safe_spearman ( aX, aY, critical_dup_level=1.1 ):
    """ more safe spearman options """
    # do something with ties in the future?
    r, p = 0.0, 1.0
    if len( aX ) > 1 and len( aY ) > 1:
        if not is_homogeneous( aX ) and not is_homogeneous( aY ):
            r, p = trunc_spearman( aX, aY )
        else:
            print >>sys.stderr, "trivial spearman (one or more homogeneous rows)"
    else:
        print >>sys.stderr, "trivial spearman (one or more tiny rows)"
    return r, p

def fisher_exact ( focus_and_feature, focus_total, feature_total, total_total ):
    """
    Performs fisher exact test given fold enrichment numbers, i.e.
    ( focus_and_feature / focus_total ) / ( feature_total / total_total )
    Returns fold enrich and two-tailed fisher exact P-value
    """
    focus_and_not_feature = focus_total - focus_and_feature
    feature_and_not_focus = feature_total - focus_and_feature
    neither_focus_nor_feature = total_total - focus_total - feature_and_not_focus
    aaData = [
        [focus_and_feature, focus_and_not_feature], 
        [feature_and_not_focus, neither_focus_nor_feature]
        ]
    pvalue = scipy_fisher_exact( aaData )[1]
    fold_enrich = ( focus_and_feature / float( focus_total ) ) / ( feature_total / float( total_total ) )
    return fold_enrich, pvalue

# ---------------------------------------------------------------
# rank transformation methods
# ---------------------------------------------------------------

def values2ranks ( aValues, normalize=False ):
    """ rank transform a list of values ( base-1 ); average tied ranks; optionally normalize """
    aRanks = list( rankdata( aValues ) )
    return aRanks if not normalize else [ k/max( aRanks ) for k in aRanks ]

def dictvalues2ranks ( dictKeyValue, normalize=False ):
    """ rank transform a dictionary of values; optionally normalize """
    aKeys = []
    aVals = []
    for k, v in dictKeyValue.items():
        aKeys.append( k )
        aVals.append( v )
    aVals = values2ranks( aVals, normalize=normalize )
    return { aKeys[i]:aVals[i] for i in range( len( aKeys ) ) }

# ---------------------------------------------------------------
# outlier detection
# ---------------------------------------------------------------

def find_outliers ( dictValues, fence="inner" ):
    """ "slices" dictionary of outliers from [key]=value dictionary """
    scale = {"inner":1.5, "outer":3.0}[fence]
    q1, q2, q3 = mquantiles( dictValues.values() )
    iqrange = q3 - q1
    dictOutliers = {}
    for k, v in dictValues.items():
        if v > q3 + scale * iqrange:
            dictOutliers[k] = v
        if v < q1 - scale * iqrange:
            dictOutliers[k] = v
    return dictOutliers

# ---------------------------------------------------------------
# bootstrap methods
# ---------------------------------------------------------------

def funcResample ( aValues ):
    """ resample ( with replacement ) one list """
    return [random.choice( aValues ) for k in aValues]

def funcResample2 ( aValues1, aValues2 ):
    """ resample ( with replacement ) a pair of lists, maintaining pairing """
    aIndex = range( len( aValues1 ) )
    aIndex = [random.choice( aIndex ) for k in aIndex] # bootstrap the positions
    aValues1 = [aValues1[k] for k in aIndex]
    aValues2 = [aValues2[k] for k in aIndex]
    return aValues1, aValues2

def funcInterval ( aValues, interval ):
    """ use mquantiles to get the endpoints of the ci interval, e.g. 2.5% and 97.5% for 95%CI """
    delta = ( 1 - interval ) / 2.0
    return list( mquantiles( aValues, [delta, 1 - delta] ) )

def boot ( aValues, func=mean, trials=1e3, interval=0.95, stderr=False ):
    """ estimate the ci/standard error of a measure by bootstrapping """
    aResults = []
    for i in range( int( trials ) ):
        aTemp = funcResample( aValues )
        aResults.append( func( aTemp ) )
    # test for consistency
    actual, bootmean = func( aValues ), mean( aResults )
    if abs( actual - bootmean ) / float( actual ) > 0.05:
        print >>sys.stderr, "WARNING: bootstraps not comparable, actual=", actual, "bootmean=", bootmean
    return std( aResults ) if stderr else funcInterval( aResults, interval )

def boot2 ( aValues1, aValues2, func=lambda x, y: spearmanr( x, y )[0], interval=0.95, trials=1e3, stderr=False ):
    """ estimate the ci/standard error of a coupling measure by bootstrapping """
    aResults = []
    for i in range( int( trials ) ):
        aTemp1, aTemp2 = funcResample2( aValues1, aValues2 )
        aResults.append( func( aTemp1, aTemp2 ) )
    # test for consistency
    actual, bootmean = func( aValues1, aValues2 ), mean( aResults )
    if abs( actual - bootmean ) / float( actual ) > 0.05:
        print >>sys.stderr, "WARNING: bootstraps not comparable, actual=", actual, "bootmean=", bootmean
    return std( aResults ) if stderr else funcInterval( aResults, interval )

# ---------------------------------------------------------------
# permutation methods
# ---------------------------------------------------------------

def funcPerror ( p, trials ):
    """ estimates the stderr of pvalue by treating as a proportion of trials """
    return math.sqrt( p * ( 1 - p ) / float( trials ) )

def perm_membership ( aX, aY, func=mean, trials=1e3 ):
    """ permutation-style test for difference between two groups """
    extremes = 0
    diff_actual = func( aX ) - func( aY )
    aZ = aX + aY
    for i in range( int( trials ) ):
        random.shuffle( aZ )
        aXrand = aZ[0:len( aX )]
        aYrand = aZ[len( aX ):]
        diff_random = func( aXrand ) - func( aYrand )
        if abs( diff_random ) >= abs( diff_actual ):
            extremes += 1
    # note: treating the actual value as observation; prevents p=0
    if extremes == 0: print >>sys.stderr, "never observed more extreme in", trials, "trials"
    pvalue = ( 1 + extremes ) / float( trials )
    return pvalue #, funcPerror( pvalue, trials )

def perm_coupling ( aX, aY, func=lambda x, y: spearmanr( x, y )[0], trials=1e3 ):
    """ permutation-style test for coupling between two vectors """
    aYcopy = aY[:]
    coupling_actual = func( aX, aYcopy )
    extremes = 0
    for i in range( int( trials ) ):
        random.shuffle( aYcopy )
        coupling_random = func( aX, aYcopy )
        if abs( coupling_random ) >= abs( coupling_actual ):
            extremes += 1
    # note: treating the actual value as observation; prevents p=0
    if extremes == 0: print >>sys.stderr, "never observed more extreme in", trials, "trials"
    pvalue = ( 1 + extremes ) / float( trials )
    return pvalue #, funcPerror( pvalue, trials )

# ---------------------------------------------------------------
# information theory
# ---------------------------------------------------------------

def shannon ( aX ):
    """ computes the shannon entropy for an event vector """
    pX = Counter()
    for x in aX:
        pX[x] += 1
    total = float( sum( pX.values() ) )
    result = 0
    for x, count in pX.items():
        prob = count / total
        result += -1 * prob * math.log( prob ) / math.log( 2 )
    return result

def sqrt_bin ( a ):
    n = len( a )
    b = int( math.sqrt( n ) )
    a2 = sorted( a )
    bins = [a2[int( n * k / float( b ) ) - 1] for k in range( 1, b+1 )]
    a3 = []
    for i, x in enumerate( a ):
        for b in bins:
            if x <= b:
                a3.append( b )
                break
    return a3

def mutinfo ( aX, aY, normalized=False ):
    """ computes the mutual information for a pair of event vectors """
    pX = Counter()
    pY = Counter()
    pJoint = Counter()
    for x, y in zip( aX, aY ):
        pX[x] += 1
        pY[y] += 1
        pJoint[( x, y )] += 1
    for d in [pX, pY, pJoint]:
        total = float( sum( d.values() ) )
        for k in d:
            d[k] /= total
    result = 0
    for ( x, y ), joint in pJoint.items():
        result += joint * math.log( joint / pX[x] / pY[y] ) / math.log( 2 )
    return result if not normalized else result / min( shannon( aX ), shannon( aY ) )

# ---------------------------------------------------------------
# binomial error model (inspired by metaphlan soft coreness)
# ---------------------------------------------------------------

def binomial_error( errors, trials, error_rate ):
    """ 
    returns chances of seeing >= errors given trials + rate
    if nontrivial (e.g. >5%) then the result (e.g. missing data)
    could reasonably have occurred at random
    """
    return 1 - binom.cdf( errors - 1, trials, error_rate )

# ---------------------------------------------------------------
# class for aiding in weighted random choice
# ---------------------------------------------------------------

class WeightedChooser( ):
    def __init__( self, weights ):
        self.intervals = []
        total = float( sum( weights.values() ) )
        last = 0
        for item in sorted( weights, key=lambda x: weights[x], reverse=True ):
            delta = weights[item] / total
            self.intervals.append( (item, last, last + delta) )
            last += delta
    def choice( self ):
        i = 0
        step = len( self.intervals )
        r = random.random()
        while not ( self.intervals[i][1] <= r <= self.intervals[i][2] ):
            step = max( 1, step / 2 )
            if r > self.intervals[i][1]:
                i += step
            else:
                i -= step
        return self.intervals[i][0]
    def iter_choice( self, n ):
        for i in range( n ):
            yield self.choice( )

#-------------------------------------------------------------------------------
# roc analysis
#-------------------------------------------------------------------------------

def calc_auc( tprs, fprs ):
    auc = 0
    n = len( tprs )   
    for i in range( n - 1 ):
        height = ( tprs[i] + tprs[i+1] ) / 2.0
        width = fprs[i+1] - fprs[i]
        auc += height * width
    return auc

def curve_check( labels, scores ):
    if not set( labels ) <= set( [0, 1] ):
        die( "non-binary [0, 1] labels vector" )
    if not len( labels ) == len( scores ):
        die( "labels and scores have non-equal lengths" )
    return None
        
def roc_curve( labels, scores ):
    curve_check( labels, scores )
    # track unique scores and associated pos/neg cases
    sdict = {}
    for l, s in zip( labels, scores ):
        sdict.setdefault( s, [] ).append( l )
    ptot = float( sum( labels ) )
    ntot = len( labels ) - ptot
    tp = 0
    fp = 0
    tprs = []
    fprs = []
    # work backward through unique scores; most stringent first
    for s in sorted( sdict, reverse=True ):
        calls = sdict[s]
        tp += sum( calls )
        fp += len( calls ) - sum( calls )
        tprs.append( tp / ptot )
        fprs.append( fp / ntot )
    # attach extremes (make no calls / all calls positive)
    tprs = [0] + tprs + [1]
    fprs = [0] + fprs + [1]
    # return with auc value
    return tprs, fprs, calc_auc( tprs, fprs )

def pr_curve( labels, scores ):
    curve_check( labels, scores )
    # track unique scores and associated pos/neg cases
    sdict = {}
    for l, s in zip( labels, scores ):
        sdict.setdefault( s, [] ).append( l )
    ptot = float( sum( labels ) )
    tp = 0
    fp = 0
    # tpr = recall / ppv = precision
    tprs = []
    ppvs = []
    # work backward through unique scores; most stringent first
    for s in sorted( sdict, reverse=True ):
        calls = sdict[s]
        tp += sum( calls )
        fp += len( calls ) - sum( calls )
        tprs.append( tp / ptot )
        ppvs.append( tp / float( tp + fp ) )
    # attach extremes (make no calls / all calls positive)
    tprs = [0] + tprs + [1]
    ppvs = [1] + ppvs + [ptot / float( len( labels ) )]
    # return with auc value
    return ppvs, tprs, calc_auc( ppvs, tprs )
    
# ---------------------------------------------------------------
# testing
# ---------------------------------------------------------------

if __name__ == "__main__":
    # perm/boot tests
    x = [random.random() for k in range( 100 )]
    y = [random.random() + 0.1 * x[i] for i in range( len( x ) )]
    print "mean x, mean y, spearman( x,y )", mean( x ), mean( y ), spearmanr( x, y )[0]
    print "boot x CI95", boot( x )
    print "boot x SErr", boot( x, stderr=True )
    print "boot xy corr CI95", boot2( x, y )
    print "boot xy corr SErr", boot2( x, y, stderr=True )
    print "perm xy diff pval", perm_membership( x, y )
    print "perm xy corr pval", perm_coupling( x, y )



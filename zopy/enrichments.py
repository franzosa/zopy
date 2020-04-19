#!/usr/bin/env python

import os
import sys

import numpy as np
from scipy.stats import fisher_exact, mannwhitneyu

from zopy.utils import qw, say
from zopy.fdr import pvalues2qvalues as apply_fdr

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------

c_eps = 1e-20

c_fisher_fields = qw( """
term
overlap
expected_overlap
fold_enrichment
p_value
q_value
""" )

c_rank_fields = qw( """
term
overlap
overlap_median
background_median
p_value
q_value
""" )

# ---------------------------------------------------------------
# helper classes
# ---------------------------------------------------------------

class Link:

    def __init__( self, key, value ):
        self.key = key
        self.value = value
    
class Result:

    def __init__( self, fields ):
        self.fields = fields
        self.values = {f:None for f in fields}

    def header_row( self ):
        return [field.upper( ) for field in self.fields]

    def row( self ):
        return [str( self.values[f] ) for f in self.fields]

    def populate( self ):
        for field, value in self.values.items( ):
            setattr( self, field, value )

    def __getitem__( self, field ):
        return self.values[field]

    def __setitem__( self, field, value ):
        self.values[field] = value

    def __repr__( self ):
        return "\t".join( self.row( ) )

#-------------------------------------------------------------------------------
# helper functions
#-------------------------------------------------------------------------------

def generate_background( annotations ):
    """
    extract the list of members from an annotations [term][member] nested dictionary
    """
    background = set( )
    for term, members in annotations.items( ):
        background.update( members )
    return background

def preprocess_annotations( annotations, min_size ):
    ni = nf = len( annotations )
    if min_size is not None:
        annotations = {k:v for k, v in annotations.items( ) if len( v ) >= min_size}
        nf = len( annotations )
    say( "Annotations:" )
    say( "  Loaded: {:,}".format( ni ) )
    if ni != nf:
        say( "  After filtering: {:,} ({:.1f}%)".format( nf, 100.0 * nf / ni ) )
    return annotations
 
def annotation_report( message, linking, annotations ):
    is_linked = not all( [k == v for k, v in linking.items( )] )
    say( message )
    is_annotated = generate_background( annotations )
    n_keys = len( linking )
    n_keys_annotated = len( {key for key, link in linking.items( ) if link in is_annotated} )
    is_link = set( linking.values( ) )
    n_links = len( is_link )
    n_links_annotated = len( is_link.__and__( is_annotated ) )
    # outer key results
    say( "  Total keys: {:,}".format( n_keys ) )
    say( "  Annotated keys: {:,} ({:.1f}%)".format(
        n_keys_annotated, 100 * n_keys_annotated / (c_eps + n_keys) ) )
    # inner key (link) results
    if is_linked:
        say( "  Total links: {:,}".format( n_links ) )
        say( "  Annotated links: {:,} ({:.1f}%)".format(
            n_links_annotated, 100 * n_links_annotated / (c_eps + n_links) ) )
    return None

def progress( counter, annotations ):
    say( "Testing annotation {: >5d} of {: >5d}".format(
        counter, len( annotations ) ) )

def attach_q_values( results ):
    p_values = [R["p_value"] for R in results]
    q_values = apply_fdr( p_values )
    for R, q in zip( results, q_values ):
        R["q_value"] = q

#-------------------------------------------------------------------------------
# fisher-style enrichment
#-------------------------------------------------------------------------------

def fisher_enrich( sample,
                   annotations, 
                   depletions=True,
                   background=None,
                   intersect_background=False,
                   intersect_annotated=False,
                   min_fold=None,
                   min_expected_overlap=None, 
                   fdr=None, 
                   verbose=False, ):
    """
    Perform fisher-style enrichment over a set of keys, key sets, and optional background
    """
    # enable linking
    if type( sample ) is not dict:
        sample = {key:key for key in sample}
    if background is None:
        background = generate_background( annotations )
    if type( background ) in [list, set]:
        background = {key:key for key in background}
    annotations = {term:set( links ) for term, links in annotations.items( )}
    # remove useless annotations (size < min_expected_overlap)
    annotations = preprocess_annotations( annotations, min_expected_overlap )
    # restrict sample and annotation space to background?
    if intersect_background:
        sample = {key:link for key, link in sample.items( ) if key in background}
        background_members = set( background.values( ) )
        new_annotations = {}
        for term, members in annotations.items( ):
            members = members.__and__( background_members )
            # may result in empty annotations (removed)
            if len( members ) > 0:
                new_annotations[term] = members
        annotations = new_annotations
    # restrict sample and background space to annotated members
    if intersect_annotated:
        is_annotated = generate_background( annotations )
        sample = {key:link for key, link in sample.items( ) \
                if link in is_annotated}
        background = {key:link for key, link in background.items( ) \
                if link in is_annotated}
    # report
    annotation_report( "Sample:", sample, annotations )
    annotation_report( "Background:", background, annotations )
    # allows much faster grouping of keys into terms via links
    link_groups = {}
    for key, link in background.items( ):
        link_groups.setdefault( link, set( ) ).add( key )
    # calculate results
    results = []
    counter = 0
    for term, members in annotations.items( ):
        counter += 1
        if verbose:
            progress( counter, annotations )
        # overlap between members with term and members of sample
        overlap = [key for key, link in sample.items( ) if link in members]
        # counts
        count_overlap         = len( overlap )
        count_background      = len( background )
        count_sample          = len( sample )
        count_term            = len( [key for link in members for key in link_groups.get( link, [] )] )
        count_sample_not_term = count_sample - count_overlap
        count_term_not_sample = count_term - count_overlap
        count_remainder       = count_background - count_overlap - count_term_not_sample - count_sample_not_term
        # test overlap
        expected_overlap      = count_sample * count_term / float( count_background )
        # fold enrichment
        fold_enrichment       = count_overlap / expected_overlap
        # contingency table for fisher exact
        table = [
            [ count_overlap,         count_sample_not_term ],
            [ count_term_not_sample, count_remainder       ]
            ]
        # calculate pvalue and store results; note: [0] is odds ratio  
        p_value = fisher_exact( table )[1]
        # populate a new Result
        R = Result( c_fisher_fields )
        R["term"]             = term
        R["overlap"]          = count_overlap
        R["expected_overlap"] = expected_overlap
        R["fold_enrichment"]  = fold_enrichment
        R["p_value"]          = p_value
        results.append( R )
    # compute and attach q values
    attach_q_values( results )
    # rank and filter results
    ret = []
    for R in sorted( results, key=lambda R: R["q_value"] ):
        include = True
        R.populate( )
        if min_fold is not None and 1.0 / min_fold < R.fold_enrichment < min_fold:
            include = False
        if not depletions and R.fold_enrichment < 1:
            include = False
        if fdr is not None and R.q_value > fdr:
            include = False
        if min_expected_overlap is not None and R.expected_overlap < min_expected_overlap:
            include = False
        if include:
            ret.append( R )
    return ret

#-------------------------------------------------------------------------------
# rank-style enrichment
#-------------------------------------------------------------------------------

def rank_enrich( quants, 
                 annotations, 
                 depletions=True, 
                 intersect_annotated=False,
                 min_overlap=None, 
                 min_fold=None, 
                 fdr=None, 
                 verbose=False, ):
    """
    Perform rank-based enrichment over a set of keys, key sets, and optional background
    Values is a dictionary mapping from key to value OR key to Link( key', value )
    Links are used to connect keys into an annotation system
    """
    # adjust basic map to link map
    for key, value in quants.items( ):
        if type( value ) is not Link:
            quants[key] = Link( key, value )
    # remove useless annotations (size < min_overlap)
    annotations = preprocess_annotations( annotations, min_overlap )
    # restrict quants to annotated members?
    if intersect_annotated:
        is_annotated = generate_background( annotations )
        quants = {key:link for key, link in quants.items( ) if link.key in is_annotated}
    # report
    linking = {key:link.key for key, link in quants.items( )}
    annotation_report( "Input keys:", linking, annotations )
    # arrays for fast compute
    kk = [link.key for link in quants.values( )]
    vv = [link.value for link in quants.values( )]
    vv = np.array( vv )
    # run analysis
    counter = 0
    results = []
    for term, members in annotations.items( ):
        counter += 1
        if verbose:
            progress( counter, annotations )
        index = [i for i, k in enumerate( kk ) if k in members]
        xx = vv[index]
        yy = np.delete( vv, index )
        if len( xx ) == 0:
            # causes error in computation
            continue
        elif min_overlap is not None and len( xx ) < min_overlap:
            continue
        xmed = np.median( xx )
        ymed = np.median( yy )
        # [0] is the test statistic
        p_value = mannwhitneyu( xx, yy, alternative="two-sided" )[1]
        # populate a new result
        R = Result( c_rank_fields )
        R["term"]              = term
        R["overlap"]           = len( xx )
        R["overlap_median"]    = xmed
        R["background_median"] = ymed
        R["p_value"]           = p_value
        results.append( R )
    # compute and attach q-values
    attach_q_values( results )
    # filter results
    ret = []
    for R in sorted( results, key=lambda R: R["q_value"] ):
        R.populate( )
        include = True
        if fdr is not None and R.q_value > fdr:
            include = False
        if not depletions and R.overlap_median < R.background_median:
            include = False
        if min_fold is not None:
            test1 = R.overlap_median / (R.background_median + c_eps) < min_fold
            test2 = R.background_median / (R.overlap_median + c_eps) < min_fold
            include = not (test1 and test2)
        if include:
            ret.append( R )
    return ret

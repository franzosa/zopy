#!/usr/bin/env python

import os
import sys
import re
import argparse
from shutil import move, copy

from zopy.utils import iter_lines, qw

parser = argparse.ArgumentParser( )
parser.add_argument( "input" )
parser.add_argument( "--execute", action="store_true" )
args = parser.parse_args( )

# note: if a prefix is a prefix of another prefix, it must come later in list
prefixes = qw( """
int
float
str
list
dict
set
hash
func
i
f
a
""" )
pre_pattern = "^(" + "|".join( prefixes ) + ")+"

def wordish( char ):
    return True if re.search( "[A-Za-z0-9_]", char ) else False

def next_span( text, index ):
    start = index
    is_word = wordish( text[index] )
    while( index < len( text ) and ( is_word == wordish( text[index] ) ) ):
        index += 1
    stop = index
    return start, stop, is_word

def find_spans( text ):
    spans = []
    start = 0
    while start < len( text ):
        spans.append( next_span( text, start ) )
        start = spans[-1][1]
    return spans

def remove_hungarian( word ):
    # micro-prefix
    micro = ""
    if re.search( "^._", word ):
        micro = word[0:2]
        word = word[2:]
    # remove types
    working = False
    if re.search( pre_pattern + "[A-Z]", word ):
        working = True
        word = re.sub( pre_pattern, "", word )
    # remove camel case
    if working:
        chars1 = [k for k in word]
        chars2 = []
        for i, c in enumerate( chars1 ):
            chars2.append( c.lower( ) )
            if i+1 < len( chars1 ):
                if re.search( "[a-z][A-Z]", word[i:i+2] ):
                    chars2.append( "_" )
        word = "".join( chars2 )
    return micro + word

temp_path = args.input + ".temp"
fh = open( temp_path, "w" ) if args.execute else sys.stdout

words = {}
for line in iter_lines( sys.argv[1] ):
    spans = find_spans( line )
    line2 = []
    for start, stop, is_word in spans:
        span = line[start:stop]
        if is_word:
            word = line[start:stop]
            word2 = remove_hungarian( word )
            if word2 != word:
                span = word2
                words.setdefault( word, [] ).append( word2 )
        line2.append( span )
    line2 = "".join( line2 )
    print >>fh, line2
                
for k in sorted( words, key=lambda x: len( words[x] ) ):
    print k, "-->", words[k][0], "::", len( words[k] )

if args.execute:
    copy( args.input, args.input + ".bak" )
    move( temp_path, args.input )

fh.close( )

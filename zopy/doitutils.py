#!/usr/bin/env python

import os
import sys
import re
import glob
import subprocess
import shutil

from doit.tools import config_changed

from zopy.utils import say

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

c_default_alias = {
    "DAT": "data",
    "IN":  "input",
    "TMP": "output/tmp",
    "OUT": "output",
    "SRC": "src",
}

# ---------------------------------------------------------------
# task helper functions
# ---------------------------------------------------------------

def mkdirs( *targets ):
    for t in targets:
        d = os.path.split( t )[0]
        if not os.path.isdir( d ) and d not in ["", ".", ".."]:
            os.makedirs( d )
            print >>sys.stderr, "\tcreated dir path (%s) re: target (%s)" % ( d, t )   

def clean_targets( *targets ):
    for t in targets:
        if os.path.exists( t ):
            if os.path.isdir( t ):
                shutil.rmtree( t )
                print >>sys.stderr, "\tremoved existing target dir (%s)" % ( t )
            else:
                os.remove( t )
                print >>sys.stderr, "\tremoved existing target file (%s)" % ( t )

def status( query ):
    try:
        status = ""
        cmdstring = "ls -lR {}".format( query )
        cmd = subprocess.Popen( cmdstring, shell=True, stdout=subprocess.PIPE )
        for line in cmd.stdout:
            status += line
        return status
    except:
        return ""

# ---------------------------------------------------------------
# convert formatted string to doit dict
# ---------------------------------------------------------------

def dodict( action, alias=None, name=None, always=False, clean=False ):
    to_clean = []
    cstrings = {}
    # long actions can be supplied as list
    if type( action ) is list:
        action = " ".join( action )
    cstrings["action_original"] = action
    # replace aliased items via python formatting
    if alias is None:
        alias = {}
    for old, new in c_default_alias.items():
        if old in alias and alias[old] != new:
            print >>sys.stderr, "warning, default alias overwrite:", old, alias[old], "<--", new
        alias[old] = new
    action = action.format( **alias )
    # process file deps
    cstrings["action_formatted"] = action
    file_dep = []
    for match in re.finditer( "([Dd]):(.*?)(\s|$)", action ):
        flag, item, other = match.groups( )
        if flag == "d":
            file_dep.append( item )
        elif flag == "D":
            cstrings[item] = status( item )
    action = re.sub( "[Dd]:", "", action )
    # process targets
    targets = []
    for match in re.finditer( "([Tt]):(.*?)(\s|$)", action ):
        flag, item, other = match.groups( )
        if flag == "t":
            targets.append( item )
        elif flag == "T":
            if not clean:
                sys.exit( "Lethal Error: Folder target 'T:' used without invoking clean=True" )
            targets.append( item )
            to_clean.append( item )
    action = re.sub( "[Tt]:", "", action )
    if len( targets ) == 0:
        say( "Action has no targets?\n\t{}".format( cstrings["action_original"] ) )
    # remove commented items
    action = re.sub( " +#.*", "", action )
    cstrings["action_uncommented"] = action
    # expected task dictionary (augmented below)
    doitdict = { 
        "targets":targets, 
        "file_dep":file_dep,
        "actions":[(clean_targets, to_clean), (mkdirs, targets), action],
        "uptodate":[not always, config_changed( cstrings )],
        "verbosity":2,
    }
    if name is not None:
        if type( name ) is not str:
            name = ":".join( [str( k ) for k in name] )       
        doitdict["name"] = name    
    # return task dictionary
    return doitdict

# ---------------------------------------------------------------
# other helper functions
# ---------------------------------------------------------------

def check( command, expect, local=False ):
    try:
        result = subprocess.check_output( 
            command,
            stderr=subprocess.STDOUT,
            shell=True,
            )
    except:
        sys.exit( "Check failed: '{}'\n\tCould not evaluate.".format( command ) )
    if not local and result.strip() != expect:
        sys.exit( "Check failed: '{}'\n\tExpected:'{}'\n\tObserved:'{}'".format( 
                command, expect, result ) )
    elif local:
        for line in result.split( "\n" ):
            if expect in result:
                break
        else:
            sys.exit( "Check failed: '{}' not in STDOUT for '{}'".format( 
                    expect, command ) )

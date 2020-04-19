#!/usr/bin/env python

from memoize import memoize

class Node:

    def __init__( self, name ):
        self.name = name
        self.children = set( )
        self.parents = set( )
        self.is_root = True
        self.is_leaf = True

    def __repr__( self ):
        return self.name

    def add_parent( self, node ):
        self.parents.add( node )
        node.children.add( self )
        self.is_root = False
        node.is_leaf = False

    def add_child( self, node ):
        self.children.add( node )
        node.parents.add( self )
        self.is_leaf = False
        node.is_root = False
    
    @memoize
    def get_progeny( self ):
        progeny = {k for k in self.children}
        for n in self.children:
            if not n.is_leaf:
                progeny.update( n.get_progeny( ) )
        return progeny

    @memoize
    def get_ancestors( self ):
        ancestors = {k for k in self.parents}
        for n in self.parents:
            if not n.is_root:
                ancestors.update( n.get_ancestors( ) )
        return ancestors

    @memoize
    def get_lineages( self ):
        lineages = []
        for p in self.parents:
            priors = [[]] if p.is_root else p.get_lineages()
            for l in priors:
                lineages.append( [p] + l )
        return lineages

class DAG:

    def __init__( self ):
        self.node_dict = {}

    def add( self, node ):
        self.node_dict[node.name] = node

    def get( self, name ):
        if name not in self.node_dict:
            self.add( Node( name ) )
        return self.node_dict[name]

    def nodes( self ):
        for name in sorted( self.node_dict ):
            yield self.node_dict[name] 

    def items( self ):
        for name, node in node_dict.items( ):
            yield name, node

    @memoize
    def leafs( self ):
        return {node for node in self.nodes( ) if node.is_leaf}

    @memoize
    def roots( self ):
        return {node for node in self.nodes( ) if node.is_root}

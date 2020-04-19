#! /usr/bin/env python

import sys, time

class timer:
    def __init__ ( self ):
        self.last = time.time()     
        self.frozen = False
    def update ( self ):
        self.last = time.time()
    def check ( self ):
        print >>sys.stderr, "%5.1f seconds" % ( time.time() - self.last )
    def interval ( self ):
        self.check()
        if not self.frozen:
            self.update()
    def freeze ( self ):
        self.frozen = True
    def unfreeze ( self ):
        if self.frozen:
            self.update()
        self.frozen = False

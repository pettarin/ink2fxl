#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014-2015 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.3'
__date__        = '2015-01-31'
__description__ = 'Represent a CSS color'

### BEGIN changelog ###
#
# 0.0.2 2014-07-14 Fixed old-style raise
# 0.0.1 2014-07-10 Initial release, nearly verbatim from https://github.com/shogo82148/svg2css
#
### END changelog ###

import re

class CSSColor:
    __re_hex = re.compile("^#([0-9a-f][0-9a-f])([0-9a-f][0-9a-f])([0-9a-f][0-9a-f])$", re.I)
    def __init__(self, *larg, **darg):
        if (len(larg) == 1):
            # hex value
            m = CSSColor.__re_hex.match(larg[0])
            if (m):
                self.r = int(m.group(1), 16)
                self.g = int(m.group(2), 16)
                self.b = int(m.group(3), 16)
                self.a = 1.0
                return
            raise TypeError("Bad color value: '%s'" % (larg[0]))
        elif (len(larg) == 3):
            # (r,g,b) tuple
            self.r = int(larg[0])
            self.g = int(larg[1])
            self.b = int(larg[2])
            self.a = 1.0
        elif (len(larg) == 4):
            # (r,g,b,a) tuple
            self.r = int(larg[0])
            self.g = int(larg[1])
            self.b = int(larg[2])
            self.a = float(larg[3])
        else:
            # (r,g,b,1) tuple
            self.r = int(darg.get("r", "0"))
            self.g = int(darg.get("g", "0"))
            self.b = int(darg.get("b", "0"))
            self.a = float(darg.get("a", "1"))

    def toHex(self):
        return "#%02x%02x%02x" % (self.r, self.g, self.b)
    
    def toRGB(self):
        return "rgb(%d,%d,%d)" % (self.r, self.g, self.b)
        
    def toRGBA(self):
        return "rgba(%d,%d,%d,%f)" % (self.r, self.g, self.b, self.a)
    
    @classmethod
    def gradient(cls, a, b, offset):
        ioffset = 1 - offset
        return CSSColor(
            ioffset * a.r + offset * b.r,
            ioffset * a.g + offset * b.g,
            ioffset * a.b + offset * b.b,
            ioffset * a.a + offset * b.a
        )
            
    def __repr__(self):
        # TODO ugly
        if (self.a > 0.999):
            return self.toHex()
        else:
            return self.toRGBA()

    def __str__(self):
        # TODO ugly
        if (self.a > 0.999):
            return self.toHex()
        else:
            return self.toRGBA()

def main():
    print "This is a test\n"
    c = CSSColor(255, 0, 0, 0.5)
    print "Cast:   " + str(c)
    print "toHex:  " + c.toHex()
    print "toRGB:  " + c.toRGB()
    print "toRGBA: " + c.toRGBA()
    print "\n"
    return

if __name__=="__main__":
    main()

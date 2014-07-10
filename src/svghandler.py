#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.1'
__date__        = '2014-07-10'
__description__ = 'Generic abstract SVG handler (calling actual SAX handlers)'

### BEGIN changelog ###
#
# 0.0.1 2014-07-10 Initial release, nearly verbatim from https://github.com/shogo82148/svg2css
#
### END changelog ###

class SVGHandler:
    def svg(self, x):
        pass
        #for a in x:
        #    a.callHandler(self)
    
    def title(self, x):
        pass
    
    def group(self, x):
        pass
        #for a in x:
        #    a.callHandler(self)
    
    def define(self, x):
        pass
    
    def linearGradient(self, x):
        pass

    def radialGradient(self, x):
        pass
   
    def stop(self, x):
        pass

    def clipPath(self, x):
        pass
    
    def rect(self, x):
        pass
    
    def arc(self, x):
        pass

    # no longer used
    #def path(self, x):
    #    pass

    def native(self, x):
        pass

    def text(self, x):
        pass
        #for a in x:
        #    a.callHandler(self)

    def tspan(self, x):
        pass
        #for a in x:
        #    a.callHandler(self)
            
    def image(self, x):
        pass
            
    def characters(self, x):
        pass
        
    def filter(self, x):
        pass
        
    def metadata(self, x):
        pass

    def unknown(self, x):
        pass


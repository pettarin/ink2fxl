#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.1'
__date__        = '2014-07-10'
__description__ = 'ink2fxl is an Inkscape plugin to export XHTML+CSS suitable for EPUB FXL ebooks'

### BEGIN changelog ###
#
# 0.0.1 2014-07-10 Initial release, inspired by SAWS (https://code.google.com/p/saws/) but completely rewritten from scratch
#
### END changelog ###

import inkex
import commands, os, re, sys
from options import Options
from svgexporter import SVGExporter

class Ink2FXL(inkex.Effect):
    
    # global variables
    output_dom = None
    output_css = ""
    log = None
    current_fragment_id = None

    # init plugin
    def __init__(self):
        # call super
        inkex.Effect.__init__(self)

        # initialize options
        commandLineOptions = Options.getOptions()
        for opt in commandLineOptions:
            if (opt["short"] != None):
                self.OptionParser.add_option(
                        opt["short"],
                        opt["long"],
                        dest=opt["dest"],
                        action="store",
                        type=opt["type"],
                        default=opt["default"],
                        help=opt["help"]
                        ) 
            else:
                self.OptionParser.add_option(
                        opt["long"],
                        dest=opt["dest"],
                        action="store",
                        type=opt["type"],
                        default=opt["default"],
                        help=opt["help"]
                        )

    # debug
    def show(self, string):
        inkex.debug(str(string))
    def output(self):
        pass

    # the magic happens here
    def effect(self):
        svg_file_path = self.args[-1]
        options = Options.convertToDict(self.options)
        isOK, message = Options.verifyOptions(options)
        if (isOK):
            converter = SVGExporter(svg_file_path, options)
            converter.parse()
            converter.output()
            converter.log()

# let's go!
effect = Ink2FXL()
effect.affect()


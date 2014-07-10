#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.1'
__date__        = '2014-07-10'
__description__ = 'Converts a SVG file into XHTML+CSS'

### BEGIN changelog ###
#
# 0.0.1 2014-07-10 Initial release
#
### END changelog ###

import codecs, os, re, sys, tempfile
import svgparser
from lxml import etree
from options import Options
from optparse import OptionParser
from xhtmlcsswriter import XHTMLCSSWriter
from rasterwriter import RasterWriter
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr

class SVGExporter():
     
    def __init__(self, svg_file_path, options):
        self.__svg_file_path = svg_file_path
        self.__options = options
        self._replace_options()
        self.writer = None
        self.log_string = ""
        self._log("Input SVG: %s" % (self.__svg_file_path))
        self._log("Options:")
        for k in sorted(self.__options.keys()):
            self._log(" %s: '%s'" % (k, self.__options[k]))

    def parse(self):
        # get the custom representation of the input SVG document
        f = open(self.__svg_file_path, 'r')
        original_svg = etree.parse(f)
        f.close()
        parser = svgparser.Parser()
    	parsed_svg_root = parser.parse(self.__svg_file_path)
        
        # set the appropriate writer
        of = self.__options["outputformat"]
        self._log("Output format: %s" % of)
        if (of in ["vector", "mixed"]):
            self._log("Writer: XHTMLCSSWriter")
            self.writer = XHTMLCSSWriter(self.__options, original_svg, self.__svg_file_path, self._log)
        elif (of == "raster"):
            self._log("Writer: RasterWriter")
            self.writer = RasterWriter(self.__options, self.__svg_file_path, self._log)

        # do the parsing
        if (self.writer is not None):
            self._log("Parsing...")
            parsed_svg_root.callHandler(self.writer)
            self._log("Parsing... completed")

    def output(self):
        if (self.writer is not None):
            output_dir_path = self.__options["outputdirectory"]
            if (not os.path.exists(output_dir_path)):
                os.makedirs(output_dir_path) 
            # vector or mixed
            of = self.__options["outputformat"]
            if (of in ["vector", "mixed"]):
                output_xhtml_file = os.path.join(output_dir_path, self.__options["outputxhtmlfile"])
                output_css_file = os.path.join(output_dir_path, self.__options["outputcssfile"])
                if (Options.isTrue(self.__options["outputcss"])):
                    # separate CSS
                    html_data = self.writer.getXHTML(cssfile=self.__options["outputcssfile"])
                    html = codecs.open(output_xhtml_file, "w", "utf-8")
                    html.write(html_data)
                    css = codecs.open(output_css_file, "w", "utf-8")
                    css.write(self.writer.getCSS())
                else:
                    # CSS embedded in the XHTML
                    html_data = self.writer.getXHTML()
                    html = codecs.open(output_xhtml_file, "w", "utf-8")
                    html.write(html_data)
                
                # in mixed mode, images are output immediately
                #if (of == "mixed"):
                #    # output images
                #    self.writer.getImages()

            # raster
            if (of == "raster"):
                # output images
                self.writer.getImages()
            
            return True
        else:
            self._log("No writer selected.", t="ERROR")
            return False

    # output log
    def log(self):
        try:
            logfile = self.__options["logfile"]
            logdelete = self.__options["logdelete"]
            if ((logfile == None) or (logfile == "")):
                log_file = tempfile.NamedTemporaryFile(mode="w", prefix="svgexporter-", suffix=".log", delete=logdelete)
            else:
                log_file = open(logfile, "w")
            log_file.write(self.log_string)
            log_file.close()
        except:
            pass

    # log the given string
    def _log(self, s, t="INFO"):
        self.log_string += ("[%s] %s\n" % (t, s))

    # TODO generalize this
    def _replace_options(self):
        self.__options["pagetitle"] = self.__options["pagetitle"].replace("%f", os.path.basename(os.path.splitext(self.__svg_file_path)[0]))











def main():
    # TODO switch to argparse
    # init option parser
    commandLineOptions = Options.getOptions()
    parser = OptionParser(usage = "Usage: %prog [options] file.svg")
    for opt in commandLineOptions:
        # exclude dummy options (starting with "zzz") needed only for Inkscape plugin window
        d = opt["dest"]
        if (not d.startswith("zzz")):
            t = opt["type"]
            if (t == "inkbool"):
                t = "string"
            if (opt["short"] != None):
                parser.add_option(
                    opt["short"],
                    opt["long"],
                    dest=opt["dest"],
                    type=t,
                    default=opt["default"],
                    help=opt["help"]
                ) 
            else:
                parser.add_option(
                    opt["long"],
                    dest=opt["dest"],
                    type=t,
                    default=opt["default"],
                    help=opt["help"]
                ) 
    (options, args) = parser.parse_args()
    if (len(args) == 0):
        parser.print_help()
        return
    
    # get svg file name 
    svgfile_path = args[0]
    
    # convert to a regular dict()
    options = Options.convertToDict(options)
    
    # verify options
    isOK, message = Options.verifyOptions(options)
   
    if (isOK):
        # do the job
        print "[INFO] Initializing..."
        converter = SVGExporter(svgfile_path, options)
        print "[INFO] Parsing input..."
        converter.parse()
        print "[INFO] Producing output..."
        converter.output()
        print "[INFO] Writing log..."
        converter.log()
        print "[INFO] Completed!"
    else:
        print "[ERROR] %s" % (message)

if __name__ == "__main__":
	main()

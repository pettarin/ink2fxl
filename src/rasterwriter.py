#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014-2015 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.3'
__date__        = '2015-01-31'
__description__ = 'Produce raster output from parsed SVG'

### BEGIN changelog ###
#
# 0.0.3 2015-01-31 Replace "," with "." after matching INKSCAPE_AREA_PATTERN (fixes issue #2)
# 0.0.2 2014-07-14 Read config from file, added JPEG output 
# 0.0.1 2014-07-10 Initial release
#
### END changelog ###

import os, re, subprocess
from options import Options
from svgelements import *
from svghandler import SVGHandler

class RasterWriter(SVGHandler):

    # value of meta generator
    META_GENERATOR = "ink2fxl"

    # custom prefix for element id's
    ELEMENT_ID_PREFIX = "svg-"

    # inkscape export switches
    INKSCAPE_WITHOUT_GUI = "--without-gui"
    INKSCAPE_EXPORT_PNG = "--export-png"
    INKSCAPE_EXPORT_ID = "--export-id"
    INKSCAPE_EXPORT_ID_ONLY = "--export-id-only"
    INKSCAPE_EXPORT_AREA_PAGE = "--export-area-page"
    INKSCAPE_AREA_PATTERN = re.compile(r"Area ([^:]*):([^:]*):([^:]*):([^ ]*) ")

    # initialize writer
    def __init__(self, options, input_svg_path, log):
        self.__options = options
        self.__input_svg_path = input_svg_path
        self.__log = self.__fake_log
        if (log):
            self.__log = log
        self.__id = 0
        self.__zindex = 0
        self.__clipnames = {}
        self.__page_width = 0
        self.__page_height = 0 
        self.__svg_defs = {}
        self._exported_file_names = {}
        self.__log("RW: initialization completed")

    # fake log
    def __fake_log(self, s):
        pass

    # generate a new name for the element
    def _getNewName(self, elem=None, use_label=False):
        # always increment, so self.__id is surely unique
        self.__id += 1
        
        # first attempt: create an id like "svg-000001"
        tmp_id = self.ELEMENT_ID_PREFIX + "%06d" % self.__id
        
        if (not self.__options["renameidattributes"]):
            # try keeping using the original svg id
            if ((elem) and (isinstance(elem, SVGElement))):
                if (use_label):
                    # use layer label
                    tmp_id = self.ELEMENT_ID_PREFIX + elem.label
                    # clean id
                    tmp_id = re.sub(r"[^A-Za-z0-9-_]", "_", tmp_id)
                else:
                    # use element id
                    tmp_id = self.ELEMENT_ID_PREFIX + elem.id
                
                # check that the id is indeed unique
                i = 1
                while (tmp_id in self._exported_file_names):
                    tmp_id += "-%s" % str(i).zfill(6)
                    i += 1
        
        return tmp_id

    # perform output
    def getImages(self):
        for k in self._exported_file_names.keys():
            elem_id = self._exported_file_names[k]
            od = self.__options["outputdirectory"]
            relative_file_path = k
            if (len(self.__options["rasterimagesubdirectory"]) > 0):
                relative_file_path = os.path.join(self.__options["rasterimagesubdirectory"], relative_file_path)
            absolute_file_path = os.path.join(od, relative_file_path)
            raster_format = self.__options["rasterformat"]
            self.__log("RW: Exporting id '%s' to file '%s.%s' ..." % (elem_id, absolute_file_path, raster_format))
            rx, ry = RasterWriter.exportRaster(
                    absolute_file_path,
                    elem_id,
                    self.__input_svg_path,
                    self.__options["rasterlayerboundingbox"],
                    raster_format, 
                    self.__log
            )
            self.__log("RW: Exporting id '%s' to file '%s.%s' ... completed" % (elem_id, absolute_file_path, raster_format))

    # exports the element with given id in the input SVG to a raster image
    @classmethod
    def exportRaster(cls, dest, elem_id, input_svg_path, crop_to_bounding_box, raster_format, log):
        # TODO error handling
        try:
            # make sure the output directory exists
            output_dir_path = os.path.dirname(dest)
            if (not os.path.exists(output_dir_path)):
                os.makedirs(output_dir_path)
                if (log):
                    log("RW: Creating directory '%s'" % (str(output_dir_path)))
            
            # we need to export to PNG from Inkscape first 
            dest_png = dest + ".png"

            # TODO hidden layers are not exported correctly: they still appear as hidden
            # TODO use direct bindings?
            # call: $ inkscape --export-png=DEST --export-id=LAYER_ID --export-id-only ORIGINAL_FILE.SVG
            parameters = [
                    Options.getInkscapePath(),
                    cls.INKSCAPE_WITHOUT_GUI,
                    cls.INKSCAPE_EXPORT_PNG, dest_png,
                    cls.INKSCAPE_EXPORT_ID, elem_id,
                    cls.INKSCAPE_EXPORT_ID_ONLY
            ]
            if (not crop_to_bounding_box):
                # export the whole page, not just the bounding box
                parameters.append(cls.INKSCAPE_EXPORT_AREA_PAGE)
            parameters.append(input_svg_path)
            if (log):
                log("RW: Calling Inkscape with parameters '%s'" % (str(parameters)))
            p = subprocess.Popen(parameters,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = p.communicate()
            p.stdout.close()
            p.stdin.close()
            p.stderr.close()
            # TODO this is very fragile
            rx = 0
            ry = 0
            for l in stdoutdata.splitlines():
                m = re.match(cls.INKSCAPE_AREA_PATTERN, l)
                if (m):
                    rx = float(m.group(1).replace(",", "."))
                    ry = float(m.group(4).replace(",", "."))
            if (log):
                log("RW: Coordinates for id '%s' rx: %f ry: %f" % (elem_id, rx, ry))
            
            if (raster_format in ["jpg", "jpeg"]):
                # convert to JPEG
                dest_jpg = dest + "." + raster_format
                # TODO use direct bindings?
                # TODO do we need to pass other parameters?
                convert_parameters = [
                        Options.getConvertPath(),
                        dest_png,
                        dest_jpg
                ]
                if (log):
                    log("RW: Calling convert with parameters '%s'" % (str(convert_parameters)))
                p = subprocess.Popen(convert_parameters,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                (stdoutdata, stderrdata) = p.communicate()
                p.stdout.close()
                p.stdin.close()
                p.stderr.close()

                # delete PNG
                os.remove(dest_png)

            return [rx, ry]
        except:
            # TODO error handling
            if (log):
                log("RW: Exception in exportRaster while processing id '%s'" % (elem_id))
            pass

    # process <svg> element
    def svg(self, elem):
        self.__log("RW: Parsing...")
        
        # TODO are multiple <svg> elements allowed? if so, this must go
        self.__page_width = elem.width.px()
        self.__page_height = elem.height.px()
        self.__log("RW: Page width: %fpx" % self.__page_width)
        self.__log("RW: Page height: %fpx" % self.__page_height)

        # visit children 
        for a in elem:
            a.callHandler(self)
        
        self.__log("RW: Parsing... completed")

    # process <defs> element
    def define(self, elem):
        pass

    # process <linearGradient> element
    def linearGradient(self, elem):
        pass 
    
    # process <radialGradient> element
    def radialGradient(self, elem):
        pass 

    # process <stop> element
    def stop(self, elem):
        pass

    # export as SVG island
    def native(self, elem):
        pass

    # process <rect> element
    def rect(self, elem):
        pass

    # process <path sodipodi:type="arc" ...> element
    def arc(self, elem):
        pass

    # process <g> element
    def group(self, elem):
        
        # is it a layer?
        if ((elem.groupmode) and (elem.groupmode == "layer")):

            if ((elem.style.get("display", "inline") == "none") and
                (not self.__options["exporthiddenlayers"])):
                # hidden layer, and the user does not want to export it 
                self.__log("RW: Skipping hidden layer with id '%s'" % elem.id)
                return

            # ok, we need to export this
            name = self._getNewName(elem)
            if ((elem.label) and (len(elem.label) > 0) and (self.__options["uselayerlabels"])):
                name = self._getNewName(elem, True)
        
            # store the layer name and its original id in the SVG document
            self._exported_file_names[name] = elem.id
            self.__log("RW: Exporting layer with id '%s' to '%s'" % (elem.id, name))

    # process <text> element
    def text(self, elem):
        pass

    # process <image> element
    def image(self, elem):
        pass

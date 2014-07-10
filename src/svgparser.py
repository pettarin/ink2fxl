#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.1'
__date__        = '2014-07-10'
__description__ = 'Parse a SVG document using SAX'

### BEGIN changelog ###
#
# 0.0.1 2014-07-10 Initial release, nearly verbatim from https://github.com/shogo82148/svg2css
#
### END changelog ###

import math, re, sys, xml.sax
from namespaces import NS
from svgelements import *

class Parser:
    # initialize everything!
    def __init__(self):
        self.__parser = xml.sax.make_parser()
        self.__handler = SVGContentHandler()
        self.__parser.setContentHandler(self.__handler)
        self.__parser.setFeature(xml.sax.handler.feature_external_ges, False)
        self.__parser.setFeature(xml.sax.handler.feature_namespaces, True)
        
    # parse the SVG document and
    # return a pointer to the <svg> root element
    def parse(self, data):
        self.__parser.parse(data)
        return self.__handler.getSVGRoot()
    

class SVGContentHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.__container = None
        self.__svg_root = None
        self.__elements = {
            "rect": SVGRect,
            "g": SVGGroup,
            "defs": SVGDefine,
            "linearGradient": SVGLinearGradient,
            "radialGradient": SVGRadialGradient,
            "stop": SVGStop,
            "clipPath": SVGClipPath,
            "text": SVGText,
            "tspan": SVGTSpan,
            "image": SVGImage,
            "filter": SVGFilter,
            "feGaussianBlur": SVGFEGaussianBlur,
            "title": SVGTitle,
            "metadata": SVGMetadata,
            #"path": SVGPath # now using nativePath and nativeRect
        }
        
    def startElementNS(self, name, qname, attrs):
        s =  attrs.get((None, "style"), "")
        if ((s) and ("filter:url" in s)):
            # we have a filter: export as native SVG
            if ((name[0] == NS.SVG) and (name[1] in ["rect", "path"])):
                self.__container.append(SVGNative(attrs))
            else:
                # unknown
                e = SVGUnknowElement(attrs, tag=name)
                self.__container.append(e)
                self.__container = e
        elif (name == (NS.SVG, "path")):
            type = attrs.get((NS.SODIPODI, "type"), "")
            if (type == "arc"):
                # <path sodipodi:type="arc" ...> element
                self.__container.append(SVGPathArc(attrs))
            else:
                # native path
                self.__container.append(SVGNative(attrs))
        else:
            # no filter here
            if (name == (NS.SVG, "svg")):
                self.__container = SVGSVG(attrs)
                self.__svg_root = self.__container
            elif ((name[0] == NS.SVG) and (name[1] in self.__elements)):
                element = self.__elements[name[1]]
                e = element(attrs)
                self.__container.append(e)
                if issubclass(element, SVGContainer):
                    self.__container = e
            else:
                e = SVGUnknowElement(attrs, tag=name)
                self.__container.append(e)
                self.__container = e

    def endElementNS(self, name, qname):
        if ((name[0] == NS.SVG) and 
                (name[1] in self.__elements) and
                (issubclass(self.__elements[name[1]], SVGContainer))):
            self.__container = self.__container.getParent()
        elif (isinstance(self.__container, SVGUnknowElement) and
                (self.__container.tag == name)):
            self.__container = self.__container.getParent()
    
    def characters(self, content):
        if isinstance(self.__container, (SVGTSpan, SVGTitle, SVGUnknowElement)):
            self.__container.append(SVGCharacters(content))
    
    def getSVGRoot(self):
        return self.__svg_root


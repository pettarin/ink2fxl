#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014-2015 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.3'
__date__        = '2015-01-31'
__description__ = 'Produce HTML+CSS output from parsed SVG'

### BEGIN changelog ###
#
# 0.0.2 2014-07-14 Read config from file, added JPEG output 
# 0.0.1 2014-07-10 Initial release
#
### END changelog ###

import math, os, re
from csscolor import CSSColor
from cssstyle import CSSStyle
from lxml import etree
from namespaces import NS
from rasterwriter import RasterWriter
from svgelements import *
from svghandler import SVGHandler
from xml.sax.saxutils import escape
from xml.sax.saxutils import quoteattr

class XHTMLCSSWriter(SVGHandler):

    # compile it here for performance
    RE_URL = re.compile("url\(#(.*)\)")
    def getURL(self, s):
        m = self.RE_URL.match(s)
        if (m):
            return m.group(1)
        return None

    # value of meta generator
    META_GENERATOR = "ink2fxl"

    # custom prefix for element id's
    ELEMENT_ID_PREFIX = "svg-"
   
    # xml preamble
    XML_PREAMBLE = '<?xml version="1.0" encoding="UTF-8"?>'

    # TODO let the user choose
    # namespaces map
    NS_MAP = {
        None: NS.XHTML,
        "epub": NS.EPUB,
        #"ev": NS.EV,
        #"ibooks": NS.IBOOKS,
        #"xml": NS.XML
    }
  
    # TODO ugly
    NBSP = u" "
    OFFSET = 10000
    TEXT_VERTICAL_OFFSET = "10000px"

    # z-index per layer
    Z_INDEX_OFFSET = 1000

    # filter settings

    # placeholders that might help postproduction hacking 
    PLACEHOLDER_PREFIX = "ink2fxl_"
    PLACEHOLDER_PRE_HEAD      = PLACEHOLDER_PREFIX + "pre_head"
    PLACEHOLDER_IN_HEAD_FIRST = PLACEHOLDER_PREFIX + "in_head_first"
    PLACEHOLDER_IN_HEAD_LAST  = PLACEHOLDER_PREFIX + "in_head_last"
    PLACEHOLDER_POST_HEAD     = PLACEHOLDER_PREFIX + "post_head"
    PLACEHOLDER_PRE_BODY      = PLACEHOLDER_PREFIX + "pre_body"
    PLACEHOLDER_IN_BODY_FIRST = PLACEHOLDER_PREFIX + "in_body_first"
    PLACEHOLDER_IN_BODY_LAST  = PLACEHOLDER_PREFIX + "in_body_last"
    PLACEHOLDER_POST_BODY     = PLACEHOLDER_PREFIX + "post_body"
    PLACEHOLDER_PRE_PAGE      = PLACEHOLDER_PREFIX + "pre_page"
    PLACEHOLDER_IN_PAGE_FIRST = PLACEHOLDER_PREFIX + "in_page_first"
    PLACEHOLDER_IN_PAGE_LAST  = PLACEHOLDER_PREFIX + "in_page_last"
    PLACEHOLDER_POST_PAGE     = PLACEHOLDER_PREFIX + "post_page"

    # initialize writer
    def __init__(self, options, original_svg, input_svg_path, log):
        self.__options = options
        self.__original_svg = original_svg
        self.__input_svg_path = input_svg_path
        self.__log = self.__fake_log
        if (log):
            self.__log = log
        self.__id = 0
        self.__zindex = 0
        self.__clipnames = {}
        self.__html = None
        self.__head = None
        self.__body = None
        self.__page_div_id = None
        self.__page_width = 0
        self.__page_height = 0 
        self.__svg_defs = {}
        self._css_data = []
        self._html_elements = {}
        self._svg_to_html = {}
        self._css_classes = set()
        self._exported_file_names = {}
        self._initDOM()
        self.__log("XW: initialization completed")

    # fake log
    def __fake_log(self, s):
        pass

    # initialize XHTML DOM
    def _initDOM(self):
        # root (html)
        html = etree.Element("html", nsmap=self.NS_MAP)
        
        # head
        self._append_placeholder(html, self.PLACEHOLDER_PRE_HEAD)
        head = etree.SubElement(html, "head")
        head_id = self.ELEMENT_ID_PREFIX + "head"
        head.attrib["id"] = head_id
        self._html_elements[head_id] = head 
        self._append_placeholder(head, self.PLACEHOLDER_IN_HEAD_FIRST)
        self._append_placeholder(html, self.PLACEHOLDER_POST_HEAD)
        
        # head > title
        title = etree.SubElement(head, "title")
        title.text = self.__options["pagetitle"]
        
        # head > generator
        generator = etree.SubElement(head, "meta")
        generator.attrib["name"] = "generator"
        generator.attrib["content"] = self.META_GENERATOR

        # head > charset
        charset = etree.SubElement(head, "meta")
        charset.attrib["name"] = "charset"
        charset.attrib["content"] = "utf-8"

        # moved inside the <svg> block
        # head > viewport
        #viewport = etree.SubElement(head, "meta")
        #viewport.attrib["name"] = "viewport"
        #viewport.attrib["content"] = "width=%s, height=%s" % (svg_width, svg_height)

        # head > css/js references
        settings_includefiles_array = self.__options["includefiles"].split(",")
        css_references = []
        js_references = []
        if (self.__options["outputcss"]):
            css_references.append(self.__options["outputcssfile"])
        for i in settings_includefiles_array:
            if (i.endswith(".css")):
                css_references.append(i)
            if (i.endswith(".js")):
                js_references.append(i)
        for c in css_references:
            css = etree.SubElement(head, "link")
            css.attrib["rel"] = "stylesheet"
            css.attrib["type"] = "text/css"
            css.attrib["href"] = c 
        for j in js_references:
            js = etree.SubElement(head, "script")
            js.attrib["type"] = "text/javascript"
            js.attrib["src"] = j
        
        # body
        self._append_placeholder(html, self.PLACEHOLDER_PRE_BODY)
        body = etree.SubElement(html, "body")
        self._append_placeholder(html, self.PLACEHOLDER_POST_BODY)
        
        # store in _html_elements dictionary
        body_id = self.ELEMENT_ID_PREFIX + "body"
        body.attrib["id"] = body_id
        self._html_elements[body_id] = body

        # store nodes
        self.__html = html
        self.__head = head
        self.__body = body
    
        # set element-level tags
        body_style = "position:absolute;margin:0px;padding:0px;"
        self._css(tag="body", style=body_style)
        div_style = "position:absolute;margin:0px;padding:0px;"
        self._css(tag="div", style=div_style)
        span_style = "position:absolute;margin:0px;padding:0px;"
        self._css(tag="span", style=span_style)

        

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
                while (tmp_id in self._html_elements):
                    tmp_id += "-%s" % str(i).zfill(6)
                    i += 1
        
        # if it was an element, add to svg_id to html_id dictionary
        if ((elem) and (isinstance(elem, SVGElement))):
            self._svg_to_html[elem.id] = tmp_id
        return tmp_id

    # get the (XHTML/CSS) id of the parent of the given SVGElement
    def _get_parent_id(self, element):
        parent_id = None
        if (element):
            svg_id = element.getParent().id
            if (svg_id in self._svg_to_html):
                parent_id = self._svg_to_html[svg_id]
        if (parent_id == None):
            # TODO should never happen, but check this
            parent_id = self.__page_div_id
        return parent_id 
    
    # accumulates CSS directives 
    def _css(self, s=None, tag=None, cls=None, id=None, style=None):
        if (s):
            self._css_data.append(s)
        if ((tag) and (style)):
            self._css_data.append("%s{%s}" % (tag, str(style)))
        if ((cls) and (style)):
            self._css_data.append(".%s{%s}" % (cls, str(style)))
        if ((id) and (style)):
            self._css_data.append("#%s{%s}" % (id, str(style)))
    
    # append element to DOM
    def _html(self, d):
        el_tag = d["tag"]
        parent = None
        if ("parent" in d):
            # get the parent node
            p_id = d["parent"]
            parent = None
            if (p_id in self._html_elements):
                parent = self._html_elements[p_id]
        
        if ((el_tag == "comment") and (parent != None)):
            # append comment
            self._append_placeholder(parent, d["placeholder"])
        elif ((el_tag in ["div", "img", "span", "svg", "defs", "path", "xml"]) and (parent != None)):
            # create node and append
            if (el_tag == "xml"):
                parent.append(d["node"])
            else:
                el = etree.SubElement(parent, el_tag)
                el_id = d["id"]
                el.attrib["id"] = el_id
                self._html_elements[el_id] = el
               
                for a in ["alt", "class", "src"]:
                    if (a in d):
                        el.attrib[a] = d[a]

                if ("content" in d):
                    el.text = d["content"]
               
                if (el_tag == "svg"):
                    el.attrib["version"] = "1.1"
                    el.attrib["xmlns"] = NS.SVG
                    el.attrib["width"] = d["width"] # already has "px" a the end
                    el.attrib["height"] = d["height"] # idem
                    el.attrib["viewBox"] = "0px 0px %s %s" % (d["width"], d["height"]) # idem
                    if ("style" in d):
                        el.attrib["style"] = d["style"]

                if (el_tag == "path"):
                    for k in ["d", "style", "transform"]:
                        if (k in d):
                            if (len(d[k]) > 0):
                                el.attrib[k] = d[k]

    # append a placeholder to the given element
    def _append_placeholder(self, parent, placeholder):
        if (self.__options["insertplaceholders"]):
            parent.append(etree.Comment(" %s " % placeholder))

    # get XHTML as string
    def getXHTML(self, title=None, cssfile=None):
        
        # if we have to output CSS inside the XHTML
        if (not self.__options["outputcss"]):
            css = etree.SubElement(self.__head, "style")
            css.attrib["type"] = "text/css"
            css.attrib["rel"] = "stylesheet"
            css.text = "\n" + self.getCSS()

        # return a pretty print of the XHTML
        return self.XML_PREAMBLE + "\n" + etree.tostring(self.__html, pretty_print=True)
       
    # get CSS as string
    def getCSS(self):
        ret = ""
        for c in sorted(self._css_data):
            ret += c + "\n"
        return ret
   
    # process <svg> element
    def svg(self, elem):
        self.__log("XW: Parsing...")

        # TODO are multiple <svg> elements allowed? if so, this must go
        # set the viewport property in 
        # head > viewport
        self.__page_width = elem.width.px()
        self.__page_height = elem.height.px()
        self.__log("XW: Page width: %fpx" % self.__page_width)
        self.__log("XW: Page height: %fpx" % self.__page_height)            
        viewport = etree.SubElement(self.__head, "meta")
        viewport.attrib["name"] = "viewport"
        viewport.attrib["content"] = "width=%.03fpx, height=%.03fpx" % (self.__page_width, self.__page_height)
        self._html({"tag": "comment", "placeholder": " %s " % self.PLACEHOLDER_IN_HEAD_LAST, "parent": self.__head.attrib["id"]})
        
        # add page element
        svg_id = self.ELEMENT_ID_PREFIX + "page"
        self.__page_div_id = svg_id
        
        # add style
        svg_style = ""
        svg_style += "top:%dpx;" % (int(self.__options["pageoffsettop"]))
        svg_style += "left:%dpx;" % (int(self.__options["pageoffsetleft"]))
        svg_style += "width:%.03fpx;" % (self.__page_width)
        svg_style += "height:%.03fpx;" % (self.__page_height)
        #svg_style += "position:absolute;"
        #svg_style += "margin:0px;"
        #svg_style += "padding:0px;"
        # add background-color, if requested
        if (self.__options["pagebackgroundcolor"]):
            cls = self.__options["pagebackgroundcolorstyle"].strip()
            if ((cls) and (len(cls) > 0)):
                svg_style += "background-color:" + cls + ";"
        # add border, if requested
        if (self.__options["pageborder"]):
            cls = self.__options["pageborderstyle"].strip()
            if ((cls) and (len(cls) > 0)):
                svg_style += "border:" + cls + ";"
        self._css(id=svg_id, style=svg_style)

        # append to DOM
        self._html({"tag": "comment", "placeholder": " %s " % self.PLACEHOLDER_IN_BODY_FIRST, "parent": self.__body.attrib["id"]})
        self._html({"tag": "comment", "placeholder": " %s " % self.PLACEHOLDER_PRE_PAGE, "parent": self.__body.attrib["id"]})
        self._html({"tag": "div", "id": svg_id, "parent": self.__body.attrib["id"]})
        self._html({"tag": "comment", "placeholder": " %s " % self.PLACEHOLDER_IN_PAGE_FIRST, "parent": svg_id})

        # visit children 
        for a in elem:
            a.callHandler(self)
        
        # append to DOM
        self._html({"tag": "comment", "placeholder": " %s " % self.PLACEHOLDER_IN_PAGE_LAST, "parent": svg_id})
        self._html({"tag": "comment", "placeholder": " %s " % self.PLACEHOLDER_POST_PAGE, "parent": self.__body.attrib["id"]})
        self._html({"tag": "comment", "placeholder": " %s " % self.PLACEHOLDER_IN_BODY_LAST, "parent": self.__body.attrib["id"]})
        
        self.__log("XW: Parsing... completed")

    # process <defs> element
    def define(self, elem):
        # visit children 
        for a in elem:
            a.callHandler(self)
            self.__svg_defs[a.id] = a

    # process <linearGradient> element
    def linearGradient(self, elem):
        # visit children 
        for a in elem:
            a.callHandler(self)
    
    # process <radialGradient> element
    def radialGradient(self, elem):
        # visit children 
        for a in elem:
            a.callHandler(self)

    # process <stop> element
    def stop(self, elem):
        pass

    # export as SVG island
    def native(self, elem):
        self.__log("XW: Native object with id '%s'" % (elem.id))
        
        # div container
        div_id = self._getNewName(elem)
        parent_id = self._get_parent_id(elem)
        self._html({"tag": "div", "id": div_id, "parent": parent_id})
        div_style = ""
        div_style += "top:0px;"
        div_style += "left:0px;"
        div_style += "width:%.03fpx;" % (self.__page_width)
        div_style += "height:%.03fpx;" % (self.__page_height)
        #div_style += "position:absolute;"
        self._css(id=div_id, style=div_style)

        # svg island
        svg_id = div_id + "-svg"
        parent_id = div_id
        svg_style = "overflow:visible;"
        self._html({"tag": "svg", "id": svg_id, "parent": parent_id, "width": str(self.__page_width), "height": str(self.__page_height), "style": svg_style})
        self.__log("XW: Added <svg> with id '%s'" % (svg_id))
        # defs element
        defs_id = self._getNewName()
        self._html({"tag": "defs", "id": defs_id, "parent": svg_id})
        self.__log("XW: Added <defs> with id '%s'" % (defs_id))
        
        # import needed fill
        self.__log("XW: Processing fill...")
        #path_style = re.sub(r"fill:url\([^)]*\)", "fill:#00ff00", path_style)
        self.__injectSVGDefs(elem.style.get("fill", ""), defs_id)
       
        # import needed filter 
        self.__log("XW: Processing filter...")
        #path_style = re.sub(r"filter:url\([^)]*\)[;]*", "", path_style)
        self.__injectSVGDefs(elem.style.get("filter", ""), defs_id)
      
        # add element 
        self.__log("XW: Processing native object with id '%s' ..." % (elem.id))
        self.__addNativeElementFromID(elem.id, svg_id)
        self.__log("XW: Processing native object with id '%s' ... done" % (elem.id))

    # gets an SVG element from its id, adds it to the DOM, and returns it as an etree node
    def __addNativeElementFromID(self, element_id, parent_id):
        # get the original SVG node with the given id
        elem = self.__original_svg.xpath("//*[@id='%s']" % (element_id))
        if (len(elem) > 0):
            # element found
            self._html({"tag": "xml", "parent": parent_id, "node": elem[0]})
            self.__log("XW: Added native object to parent_id '%s'" % (parent_id))
            return elem[0]
        return None

    # if the passed attribute (fill or filter) has an url(#...),
    # then gets the corresponding SVG element using the referenced id,
    # adds it to the DOM (inside the <defs> of the <svg> island),
    # and checks if it has an href: if so, include also the referenced filter/effect
    def __injectSVGDefs(self, attribute_string, parent_id):
        referenced_id = self.getURL(attribute_string)
        if ((referenced_id) and (referenced_id in self.__svg_defs)):
            elem = self.__addNativeElementFromID(referenced_id, parent_id)
            if (elem is not None):
                # is referencing something else? (e.g., radialGradient referencing linearGradient)
                xlink_id = elem.get("{%s}href" % NS.XLINK)
                if (xlink_id):
                    xlink_id = xlink_id[1:] # remove initial #
                    self.__log("XW: Adding referenced object to xlink_id '%s'" % (xlink_id))
                    self.__addNativeElementFromID(xlink_id, parent_id)


    # process <rect> element
    def rect(self, elem):
        self.__round_rect(
            element = elem,
            x = elem.x,
            y = elem.y,
            width = elem.width,
            height = elem.height,
            rx = elem.rx,
            ry = elem.ry
        )
   

    # process <path sodipodi:type="arc" ...> element
    def arc(self, elem):
        self.__round_rect(
            element = elem,
            x = elem.cx - elem.rx,
            y = elem.cy - elem.ry,
            width = elem.rx * 2,
            height = elem.ry * 2,
            rx = elem.rx,
            ry = elem.ry
        )

    # unified rect/rounded rect
    def __round_rect(self, element, x, y, width, height, rx=0, ry=0):
        blur = 0
        filterURL = self.getURL(element.style.get("filter", ""))
        if (filterURL):
            filter = element.getRoot().getElementById(filterURL)
            if ((filter) and (isinstance(filter[0], SVGFEGaussianBlur))):
                blur = filter[0].stdDeviation * 1.7
                try:
                    self.__blured_round_rect(element, x, y, width, height, rx, ry, blur)
                    return
                except:
                    pass
    
        name = self._getNewName(element)
        if (name not in self._css_classes):
            self._css_classes.add(name)
            css = CSSStyle()
            stroke = SVGLength(0)
            self.__clipPath(name, element)
            if (("stroke" in element.style) and (element.style["stroke"] != "none")):
                try:
                    stroke = SVGLength(element.style.get("stroke-width", 0))
                    stroke_dasharray = element.style.get("stroke-dasharray", "none")
                    css["border-width"] = stroke
                    color = CSSColor(element.style["stroke"])
                    if ("stroke-opacity" in element.style):
                        color.a = float(element.style["stroke-opacity"])
                    css["border-color"] = color
                    if (stroke_dasharray == "none"):
                        css["border-style"] = "solid"
                    else:
                        # default: dashed
                        css["border-style"] = "dashed"
                        s = stroke_dasharray.split(",")
                        # this sis an heuristic,
                        # as CSS has only basic styling
                        if (len(s) > 1):
                            s0 = float(s[0])
                            s1 = float(s[1])
                            if ((s0 > 2) or (s0 > s1)):
                                css["border-style"] = "dashed"
                            else:
                                css["border-style"] = "dotted"
                except:
                    pass
            #css["position"] = "absolute"
            css["top"] = y - stroke/2
            css["left"] = x - stroke/2
            css["width"] = width - stroke
            css["height"] = height - stroke
            if ((rx) and (ry)):
                css["border-radius"] = "%s/%s" % (str(rx + stroke/2), str(ry + stroke/2))
            elif (rx):
                css["border-radius"] = rx + stroke/2
            elif (ry):
                css["border-radius"] = ry + stroke/2
            css.addFill(element)
            if (element.transform):
                transform = element.transform.toMatrix()
                transform = transform * SVGTransform.SVGTranslate(x + width/2, y + height/2)
                transform = SVGTransform.SVGTranslate(-x - width/2, -y - height/2) * transform
                css["left"] += transform.e
                css["top"] += transform.f
                transform.e = 0
                transform.f = 0
                css["transform"] = transform
            if ("opacity" in element.style):
                css["opacity"] = element.style["opacity"]
            self._css(id=name, style=css)

        # get parent_id
        parent_id = self._get_parent_id(element)
        if (name in self.__clipnames):
            clipname = self.__clipnames[name]
            self._html({"tag": "div", "id": clipname, "parent": parent_id})
            self._html({"tag": "div", "id": clipname + "inverse", "parent": clipname})
            self._html({"tag": "div", "id": name, "parent": clipname + "inverse"})
            return
        self._html({"tag": "div", "id": name, "parent": parent_id})

    # TODO merge/refactor with the above
    def __blured_round_rect(self, element, x, y, width, height, rx=0, ry=0, blur=0):
        name = self._getNewName(element)
        namefill = name + "-fill"
        namestroke = name + "-stroke"
        hasfill = ("fill" in element.style) and (element.style["fill"] != "none")
        hasstroke = ("stroke" in element.style) and (element.style["stroke"] != "none")
        
        if (not hasstroke and hasfill):
            if (namefill not in self._css_classes):
                self._css_classes.add(namefill)
                css = CSSStyle()
                self.__clipPath(namefill, element)
                #css["position"] = "absolute"
                css["top"] = y - self.OFFSET
                css["left"] = x - self.OFFSET
                css["width"] = width
                css["height"] = height
                if ((rx) and (ry)):
                    css["border-radius"] = "%s/%s" % (rx, ry)
                elif (rx):
                    css["border-radius"] = rx
                elif (ry):
                    css["border-radius"] = ry
                css.addFill(element)
                css["box-shadow"] = "%dpx %dpx %s %s" % (self.OFFSET, self.OFFSET, blur, css["background-color"])
                css["-webkit-box-shadow"] = "%dpx %dpx %s %s" % (self.OFFSET, self.OFFSET, blur * 1.8, css["background-color"])
                css["-o-box-shadow"] = "%dpx %dpx %s %s" % (self.OFFSET, self.OFFSET, blur * 1.8, css["background-color"])
                if (element.transform):
                    transform = element.transform.toMatrix()
                    transform = transform * SVGTransform.SVGTranslate(x - self.OFFSET + width/2, y - self.OFFSET + height/2)
                    transform = SVGTransform.SVGTranslate(-x + self.OFFSET - width/2, -y + self.OFFSET - height/2) * transform
                    css["left"] += transform.e
                    css["top"] += transform.f
                    transform.e = 0
                    transform.f = 0
                    css["transform"] = transform
                if ("opacity" in element.style):
                    css["opacity"] = element.style["opacity"]
                self._css(id=namefill, style=css)
       
            # get parent_id
            parent_id = self._get_parent_id(element)
            if (namefill in self.__clipnames):
                clipname = self.__clipnames[namefill]
                self._html({"tag": "div", "id": clipname, "parent": parent_id})
                self._html({"tag": "div", "id": clipname + "inverse", "parent": clipname})
                self._html({"tag": "div", "id": name, "parent": clipname + "inverse"})
                return
            self._html({"tag": "div", "id": namefill, "parent": parent_id})
        
        if (hasstroke):
            if (namestroke not in self._css_classes):
                self._css_classes.add(namestroke)
                css = CSSStyle()
                self.__clipPath(namestroke, element)
                #css["position"] = "absolute"
                css["top"] = y
                css["left"] = x
                css["width"] = width
                css["height"] = height
                if ((rx) and (ry)):
                    css["border-radius"] = "%s/%s" % (str(rx), str(ry))
                elif (rx):
                    css["border-radius"] = rx
                elif (ry):
                    css["border-radius"] = ry
                stroke = SVGLength(element.style.get("stroke-width", 0))
                color = CSSColor(element.style["stroke"])
                if ("stroke-opacity" in element.style):
                    color.a = float(element.style["stroke-opacity"])
                css["box-shadow"] = "0px 0px %s %s %s" % (blur, stroke/2, color) + ", 0px 0px %s %s %s inset" % (blur, stroke/2, color)
                css.addFill(element)
                if (element.transform):
                    transform = element.transform.toMatrix()
                    transform = transform * SVGTransform.Translate(x + width/2, y + height/2)
                    transform = SVGTransform.SVGTranslate(-x - width/2, -y - height/2) * transform
                    css["left"] += transform.e
                    css["top"] += transform.f
                    transform.e = 0
                    transform.f = 0
                    css["transform"] = transform
                if ("opacity" in element.style):
                    css["opacity"] = element.style["opacity"]
                self._css(id=namestroke, style=css)

            # get parent_id
            parent_id = self._get_parent_id(element)
            if (namestroke in self.__clipnames):
                namestroke = self.__clipnames[name]
                self._html({"tag": "div", "id": clipname, "parent": parent_id})
                self._html({"tag": "div", "id": clipname + "inverse", "parent": clipname + "inverse"})
                self._html({"tag": "div", "id": name, "parent": name})
                return
            self._html({"tag": "div", "id": namestroke, "parent": parent_id})


    # process <g> element
    def group(self, elem):
        
        is_inkscape_layer = ((elem.groupmode) and (elem.groupmode == "layer"))
        
        if ((is_inkscape_layer) and
                (elem.style.get("display", "inline") == "none") and
                (not self.__options["exporthiddenlayers"])):
            # hidden layer, and the user does not want to export it 
            self.__log("XW: Skipping hidden layer with id '%s'" % elem.id)
            return

        # ok, we need to export this
        name = self._getNewName(elem)
        if ((is_inkscape_layer) and (elem.label) and (len(elem.label) > 0)):
            # it is a layer
            if (self.__options["uselayerlabels"]):
                name = self._getNewName(elem, True)

        self.__log("XW: Exporting layer with id '%s' to '%s'" % (elem.id, name))
        if ((is_inkscape_layer) and (self.__options["outputformat"] == "mixed")):
            # a layer and we are in mixed mode
            # store the layer name and its original id in the SVG document
            elem_id = elem.id
            self._exported_file_names[name] = elem_id
            od = self.__options["outputdirectory"]
            relative_file_path = name
            if (len(self.__options["rasterimagesubdirectory"]) > 0):
                relative_file_path = os.path.join(self.__options["rasterimagesubdirectory"], relative_file_path)
            absolute_file_path = os.path.join(od, relative_file_path)
            raster_format = self.__options["rasterformat"]
            rx, ry = RasterWriter.exportRaster(
                    absolute_file_path,
                    elem_id,
                    self.__input_svg_path, 
                    self.__options["rasterlayerboundingbox"],
                    raster_format,
                    self.__log
            )
            relative_file_path += "." + raster_format 
            absolute_file_path += "." + raster_format 
            self.__log("XW: Exporting id '%s' to file '%s' ... completed" % (elem_id, absolute_file_path))
             
            # create XHTML <div> structure
            css = CSSStyle()
            #css["position"] = "absolute"
            #css["margin"] = "0px"
            #css["padding"] = "0px"
            css["top"] = "%.03fpx" % (self.__page_height - ry)
            css["left"] = "%.03fpx" % (rx)
            # no transform
            if ("opacity" in elem.style):
                css["opacity"] = elem.style["opacity"]
            if (elem.style.get("display", "inline") == "none"):
                css["display"] = "none"
            # add z-index
            self.__zindex += self.Z_INDEX_OFFSET
            if (self.__options["explicitzindex"]):
                css["z-index"] = self.__zindex
            self._css(id=name, style=css)
            parent_id = self._get_parent_id(elem)
            self._html({"tag": "div", "id": name, "parent": parent_id})
            # TODO set alt text
            self._html({"tag": "img", "id": name + "-img", "src": relative_file_path, "alt": "", "parent": name})
        else:
            # either not a layer or we are in vector mode
            # do normal processing
            if (name not in self._css_classes):
                self._css_classes.add(name)
                css = CSSStyle()
                self.__clipPath(name, elem)
                #css["position"] = "absolute"
                #css["margin"] = "0px"
                #css["padding"] = "0px"
                if (elem.transform):
                    transform = elem.transform.toMatrix()
                    css["transform"] = transform
                if ("opacity" in elem.style):
                    css["opacity"] = elem.style["opacity"]
                if (elem.style.get("display", "inline") == "none"):
                    css["display"] = "none"
                if (is_inkscape_layer):
                    # add z-index
                    self.__zindex += self.Z_INDEX_OFFSET
                    if (self.__options["explicitzindex"]):
                        css["z-index"] = self.__zindex
                self._css(id=name, style=css)

            # get parent_id
            parent_id = self._get_parent_id(elem)
            if (name in self.__clipnames):
                clipname = self.__clipnames[name]
                self._html({"tag": "div", "id": clipname, "parent": parent_id})
                self._html({"tag": "div", "id": clipname + "inverse", "parent": clipname})
            self._html({"tag": "div", "id": name, "parent": parent_id}) 
            
            # visit children
            for a in elem:
                a.callHandler(self)


    # process <text> element
    def text(self, elem):
        name = self._getNewName(elem)

        # get parent_id
        parent_id = self._get_parent_id(elem)
        if (name in self.__clipnames):
            clipname = self.__clipnames[name]
            self._html({"tag": "div", "id": clipname, "parent": parent_id})
            self._html({"tag": "div", "id": clipname + "inverse", "parent": clipname})

        blur = 0
        filterURL = self.getURL(elem.style.get("filter", ""))
        if (filterURL):
            filter = elem.getRoot().getElementById(filterURL)
            if ((filter) and (isinstance(filter[0], SVGFEGaussianBlur))):
                blur = filter[0].stdDeviation * 1.7

        self._html({"tag": "div", "id": name, "parent": parent_id})
        parent_id = name
        # TODO can we remove this?
        self._html({"tag": "span", "id": name + "-sep", "class": "svg-text-adj", "parent": parent_id, "content": self.NBSP})
        for a in elem:
            if isinstance(a, SVGTSpan):
                self.__text_contents(a, elem.x, elem.y, blur, parent_id)
            elif isinstance(a, SVGCharacters):
                # TODO can we wrap this into a <span> ?
                self._html_elements[parent_id].text = escape(a.content)

        if (name not in self._css_classes):
            self._css_classes.add(name)
            css = CSSStyle()
            self.__clipPath(name, elem)
            #css["position"] = "absolute"
            #css["margin"] = "0px"
            #css["padding"] = "0px"
            if ("font-size" in elem.style):
                css["font-size"] = SVGLength(elem.style["font-size"])
            if ("fill" in elem.style):
                css["color"] = CSSColor(elem.style["fill"])
                if ("fill-opacity" in elem.style):
                    css["color"].a = float(elem.style["fill-opacity"])
                # TODO ugly
                if (blur > 0.001):
                    css["text-shadow"] = "0px 0px %s %s" % (blur, css["color"])
                    css["color"] = [css["color"], CSSColor(0, 0, 0, 0)]
            for stylename in ["font-style", "font-weight", "font-family"]:
                if (stylename in elem.style):
                    css[stylename] = elem.style[stylename]
            css["top"] = elem.y - SVGLength(self.TEXT_VERTICAL_OFFSET)
            css["left"] = elem.x
            if (elem.transform):
                transform = elem.transform.toMatrix()
                css["transform"] = transform
            css["white-space"] = "pre"
            self._css(id=name, style=css)
           
        # TODO can we delete this? 
        if ("svg-text-adj" not in self._css_classes):
            self._css_classes.add("svg-text-adj")
            css_style = "position:relative;font-size:0px;vertical-align:%s;" % (self.TEXT_VERTICAL_OFFSET)
            self._css(cls="svg-text-adj", style=css_style)

    # used in text()
    def __text_contents(self, elem, x=0, y=0, blur=0, parent_id=None):
        name = self._getNewName(elem)
        if (name not in self._css_classes):
            self._css_classes.add(name)
            css = CSSStyle()
            if ("font-size" in elem.style):
                css["font-size"] = SVGLength(elem.style["font-size"])
            if ("fill" in elem.style):
                css["color"] = CSSColor(elem.style["fill"])
                if ("fill-opacity" in elem.style):
                    css["color"].a = float(elem.style["fill-opacity"])
                # TODO ugly
                if (blur > 0.001):
                    css["text-shadow"] = "0px 0px %s %s" % (blur, css["color"])
                    css["color"] = [css["color"], CSSColor(0, 0, 0, 0)]
            for stylename in ["font-style", "font-weight", "font-family"]:
                if (stylename in elem.style):
                    css[stylename] = elem.style[stylename]
            if (elem.role == "line"):
                css["display"] = "block"
            if ((elem.x) or (elem.y)):
                #css["position"] = "absolute"
                css["top"] = elem.y - y
                css["left"] = elem.x - x
            self._css(id=name, style=css)

        self._html({"tag": "span", "id": name, "parent": parent_id})
        parent_id = name
        if ((elem.x) or (elem.y)):
            # TODO can we remove this?
            self._html({"tag": "span", "id": name + "-sep", "class": "svg-text-adj", "parent": parent_id, "content": self.NBSP})
        for a in elem:
            if isinstance(a, SVGTSpan):
                self.__text_contents(a, elem.x, elem.y, blur, parent_id)
            elif isinstance(a, SVGCharacters):
                # TODO can we wrap this into a <span> ?
                #self._html({"tag": "span", "id": name + "-text", "parent": parent_id, "content": escape(a.content)})
                self._html_elements[parent_id].text = escape(a.content)


    # TODO check this
    # process <image> element
    def image(self, elem):
        name = self._getNewName(elem)
        if (name not in self._css_classes):
            self._css_classes.add(name)
            css = CSSStyle()
            stroke = SVGLength(0)
            self.__clipPath(name, elem)
            #css["position"] = "absolute"
            css["top"] = elem.y
            css["left"] = elem.x
            css["width"] = elem.width
            css["height"] = elem.height
            if (elem.transform):
                transform = elem.transform.toMatrix()
                transform = transform * SVGTransform.SVGTranslate(elem.x + elem.width/2, elem.y + elem.height/2)
                transform = SVGTransform.SVGTranslate(-elem.x - elem.width/2, -elem.y - elem.height/2) * transform
                css["transform"] = transform
            self._css(id=name, style=css)

        # get parent_id
        parent_id = self._get_parent_id(elem)
        if (name in self.__clipnames):
            clipname = self.__clipnames[name]
            self._html({"tag": "div", "id": clipname, "parent": parent_id})
            self._html({"tag": "div", "id": clipname + "inverse", "parent": clipname})
            self._html({"tag": "img", "id": name, "src": quoteattr(os.path.basename(elem.href)), "parent": clipname + "inverse"})
            return
        self._html({"tag": "img", "id": name, "src": quoteattr(os.path.basename(elem.href)), "parent": parent_id})




    # TODO do we really need this? looks like it is never used
    # used in: text(), image(), group(), __round_rect(), __blured_round_rect()
    def __clipPath(self, element_name, element):
       
        # look for a clip path
        if (not element.clip_path):
            return
        m = re.match("^url\(#(.*)\)$", element.clip_path)
        if (not m):
            return
        
        # get the clip path
        target = element.getRoot().getElementById(m.group(1))[0]
        name = self._getNewName()
        css = CSSStyle()
        invtransform = SVGTransform("")
        
        if (isinstance(target, SVGRect)):
            #css["position"] = "absolute"
            css["top"] = target.y
            css["left"] = target.x
            css["width"] = target.width
            css["height"] = target.height
            if ((target.rx) and (target.ry)):
                css["border-radius"] = "%s/%s" % (str(target.rx), str(target.ry))
            elif (target.rx):
                css["border-radius"] = target.rx
            elif (target.ry):
                css["border-radius"] = target.ry
            if ((target.transform) or (element.transform)):
                transform = element.transform.toMatrix() * target.transform.toMatrix()
                invtransform.append(transform.inverse())
                transform = transform * SVGTransform.SVGTranslate(target.x + target.width/2, target.y + target.height/2)
                transform = SVGTransform.SVGTranslate(-target.x - target.width/2, -target.y - target.height/2) * transform
                css["transform"] = transform
            invtransform.append(SVGTransform.SVGTranslate(-target.x, -target.y))
            css["overflow"] = "hidden"
        
        elif (isinstance(target, SVGPathArc)):
            #css["position"] = "absolute"
            css["top"] = target.cy - target.ry
            css["left"] = target.cx - target.rx
            css["width"] = target.rx * 2
            css["height"] = target.ry * 2
            css["border-radius"] = "%s/%s" % (str(target.rx), str(target.ry))
            if ((target.transform) or (element.transform)):
                transform = element.transform.toMatrix() * target.transform.toMatrix()
                invtransform.append(transform.inverse())
                transform = transform * SVGTransform.SVGTranslate(target.cx, target.cy)
                transform = SVGTransform.SVGTranslate(-target.cx, -target.cy) * transform
                css["transform"] = transform
            invtransform.append(SVGTransform.SVGTranslate(-target.cx + target.rx, -target.cy + target.ry))
            css["overflow"] = "hidden"

        self._css(id=name, style=css)
       
        # add inverse
        css = CSSStyle()
        #css["position"] = "absolute"
        css["transform"] = invtransform.toMatrix()
        self._css(id=name+"inverse", style=css)
       
        # add to clipnames
        self.__clipnames[element_name] = name
        
        return name

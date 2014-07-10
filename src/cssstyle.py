#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.1'
__date__        = '2014-07-10'
__description__ = 'Represent a CSS style'

### BEGIN changelog ###
#
# 0.0.1 2014-07-10 Initial release, refactored and extended from https://github.com/shogo82148/svg2css
#
### END changelog ###

import math, re
from csscolor import CSSColor

# TODO decouple this
from svgelements import *

class CSSStyle(dict):
    
    def __str__(self):
        s = ""
        for name, style in sorted(self.iteritems(), key=lambda x: len(x[0])):
            if (name == "transform"):
                s += CSSStyle.__transform(style)
                continue
            if (isinstance(style, list)):
                s += "".join(["%s:%s;" % (name, s) for s in style])
                continue
            if (not isinstance(style, str)):
                style = str(style)
            s += "%s:%s;" % (name, style)
        return s
    
    @classmethod
    def __transform(cls, transform):
        style = str(transform)
        s = ""
        # no longer needed
        #for name in ["transform", "-ms-transform", "-o-transform", "-webkit-transform"]:
        #    s += "%s:%s;" % (name, style)
        #if ((isinstance(transform, str)) or (isinstance(transform, unicode))):
        #    s += "-moz-transform:%s;" % transform
        #else:
        #    s += "-moz-transform:%s;" % transform.toStringMoz()
        for name in ["transform", "-moz-transform", "-ms-transform", "-o-transform", "-webkit-transform"]:
            s += "%s:%s;" % (name, style)
        return s
    
    __re_fill_url = re.compile("url\(#(.*)\)")
    def addFill(self, element):
        svgstyle = element.style
        if (("fill" not in svgstyle) or (svgstyle["fill"] == "none")):
            return
            
        try:
            fill = svgstyle["fill"]
            m = CSSStyle.__re_fill_url.match(fill)
            if (m):
                fill = element.getRoot().getElementById(m.group(1))
                if (isinstance(fill, SVGLinearGradient)):
                    self.__addLinearGradient(element, fill)
                elif (isinstance(fill, SVGRadialGradient)):
                    self.__addRadialGradient(element, fill)
                return
            color = CSSColor(fill)
            if ("fill-opacity" in svgstyle):
                color.a = float(svgstyle["fill-opacity"])
            self["background-color"] = color
        except Exception, e:
            #print svgstyle["fill"], e
            pass
    
    def __addLinearGradient(self, element, fill):
        root = fill.getRoot()
        stops = fill
        while ((len(stops) == 0) and (stops.href)):
            stops = root.getElementById(stops.href[1:])
        background = []
        
        point1 = SVGPoint(fill.x1, fill.y1)
        point2 = SVGPoint(fill.x2, fill.y2)
        point1 = fill.gradientTransform.toMatrix() * point1
        point2 = fill.gradientTransform.toMatrix() * point2
        if (fill.gradientUnits == "userSpaceOnUse"):
            stroke = SVGLength(element.style.get("stroke-width", 0))
            point1 = SVGPoint(
                point1.x - SVGLength(self["left"]) - stroke,
                point1.y - SVGLength(self["top"]) - stroke
            )
            point2 = SVGPoint(
                point2.x - SVGLength(self["left"]) - stroke,
                point2.y - SVGLength(self["top"]) - stroke
            )

        def svgOffsetToPoint(offset):
            return point1 * (1 - offset) + point2 * offset
        
        rad = -math.atan2(point2.y - point1.y, point2.x - point1.x)
        vec = SVGPoint(math.cos(rad), -math.sin(rad))
        deg = rad / math.pi * 180
        width = SVGLength(self["width"])
        height = SVGLength(self["height"])
        point0 = SVGPoint(0, 0)
        if (0 < deg < 90):
            point0 = SVGPoint(0, height)
        elif (90 <= deg):
            point0 = SVGPoint(width, height)
        elif (deg < -90):
            point0 = SVGPoint(width, 0)
        gradientlen = (SVGPoint(width, height) - point0 * 2) * vec

        def pointToCSSOffset(point):
            offset = (point - point0) * vec / gradientlen
            return offset
        
        def svgOffsetToCSSOffset(offset):
            return pointToCSSOffset(svgOffsetToPoint(offset))

        gradient = "(%.1fdeg" % deg
        color_stops = []
        for stop in stops:
            color = CSSColor(stop.style["stop-color"])
            if (float(stop.style.get("stop-opacity", "1")) <= 0.999):
                color.a = float(stop.style.get("stop-opacity", "1"))
            gradient += ",%s %.1f%%" % (color, svgOffsetToCSSOffset(stop.offset) * 100)
            
        gradient += ")"
        background.append("linear-gradient" + gradient)
        background.append("-o-linear-gradient" + gradient)
        background.append("-moz-linear-gradient" + gradient)
        background.append("-ms-linear-gradient" + gradient)
        background.append("-webkit-linear-gradient" + gradient)
        
        #webkit
        webkit = "-webkit-gradient(linear,%f %f,%f %f," % (point1.x.px(), point1.y.px(), point2.x.px(), point2.y.px())
        color = CSSColor(stops[0].style["stop-color"])
        if (float(stops[0].style.get("stop-opacity", "1")) <= 0.999):
            color.a = float(stops[0].style.get("stop-opacity", "1"))
        webkit += "from(%s)," % color
        if (len(stops) > 2):
            for stop in stops[1:-1]:
                color = CSSColor(stop.style["stop-color"])
                if (float(stop.style.get("stop-opacity", "1")) <= 0.999):
                    color.a = float(stop.style.get("stop-opacity", "1"))
                webkit += "color-stop(%f,%s)," % (stop.offset, color)
        color = CSSColor(stops[-1].style["stop-color"])
        if (float(stops[-1].style.get("stop-opacity", "1")) <= 0.999):
            color.a = float(stops[-1].style.get("stop-opacity", "1"))
        webkit += "to(%s))" % color
        background.append(webkit)

        self["background"] = background
        
    def __addRadialGradient(self, element, fill):
        root = fill.getRoot()
        stops = fill
        while ((len(stops) == 0) and (stops.href)):
            stops = root.getElementById(stops.href[1:])
        background = []
        
        # TODO
        gradientTransform = fill.gradientTransform.toMatrix()
        center = SVGPoint(fill.cx, fill.cy)
        finish = SVGPoint(fill.fx, fill.fy)
        center = gradientTransform * center
        finish = gradientTransform * finish
        
        if (fill.gradientUnits == "userSpaceOnUse"):
            stroke = SVGLength(element.style.get("stroke-width", 0))
            center = SVGPoint(
                center.x - SVGLength(self["left"]) - stroke,
                center.y - SVGLength(self["top"]) - stroke
            )
            finish = SVGPoint(
                finish.x - SVGLength(self["left"]) - stroke,
                finish.y - SVGLength(self["top"]) - stroke
            )
        
        # TODO
        zero = SVGLength("0")
        point0 = gradientTransform * SVGPoint(zero, zero)
        rx = SVGLength((abs(gradientTransform * SVGPoint(fill.r, zero) - point0)), "px")
        ry = SVGLength((abs(gradientTransform * SVGPoint(zero, fill.r) - point0)), "px")
        r = fill.r
       
        gradient = ""
        for stop in stops:
            color = CSSColor(stop.style["stop-color"])
            if (float(stop.style.get("stop-opacity", "1")) <= 0.999):
                color.a = float(stop.style.get("stop-opacity", "1"))
            gradient += ",%s %.1f%%" % (color, stop.offset*100)
        background.append("radial-gradient(%s %s,%s %s%s)" % (center.x, center.y, rx, ry, gradient))
        background.append("-o-radial-gradient(%s %s,%s %s%s)" % (center.x, center.y, rx, ry, gradient))
        background.append("-moz-radial-gradient(%s %s,circle%s)" % (center.x, center.y, gradient))
        background.append("-moz-radial-gradient(%s %s,%s %s%s)" % (center.x, center.y, rx, ry, gradient))
        background.append("-ms-radial-gradient(%s %s,%s %s%s)" % (center.x, center.y, rx, ry, gradient))
        background.append("-webkit-radial-gradient(%s %s,%s %s%s)" % (center.x, center.y, rx, ry, gradient))

        self["background"] = background


def main():
    print "This is a test\n"
    style = {
        "display": "block",
        "left": "100px",
        "right": "200px",
        "transform": "translate(10px,10px)"
            }
    s = CSSStyle(style)
    print "Cast:   " + str(s)
    print "\n"
    return

if __name__=="__main__":
    main()

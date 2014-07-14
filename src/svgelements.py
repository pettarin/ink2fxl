#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.2'
__date__        = '2014-07-14'
__description__ = 'Parse a SVG document'

### BEGIN changelog ###
#
# 0.0.2 2014-07-14 Fixed old-style raise
# 0.0.1 2014-07-10 Initial release, nearly verbatim from https://github.com/shogo82148/svg2css
#
### END changelog ###

import math, re, xml.sax
from namespaces import NS

# generic SVG element
class SVGElement:
    def __init__(self, attrs, parent=None, default={}):
        self.__parent = parent
        self.__default = default
        self.__root = None
        self.id = attrs.get((None,"id"), "")
        self.attrs = attrs.copy()
        self.transform = SVGTransform(attrs.get((None, "transform"), ""))
        if (attrs.has_key((NS.XLINK, "href"))):
            self.href = attrs.get((NS.XLINK, "href"))
        else:
            self.href = None

    def callHandler(self, handler):
        pass
    
    def getParent(self):
        return self.__parent

    def setParent(self, p):
        self.__parent = p
        self.__root = None

    def getRoot(self):
        if (self.__parent):
            self.__root = self.__parent.getRoot()
        else:
            self.__root = self
        return self.__root
    
    def getElementById(self, id):
        if (self.id == id):
            return self
        return None

# generic SVG container element
class SVGContainer(SVGElement, list):
    def __init__(self, attrs, parent=None):
        SVGElement.__init__(self, attrs, parent)
        list.__init__(self)
        self.__childids = {}
        
    def append(self, x):
        list.append(self, x)
        self.__appendChild(x)
        
    def extend(self, L):
        list.extend(self, L)
        for x in L:
            self.__appendChild(x)
    
    def insert(self, i, x):
        list.insert(self, i, x)
        self.__appendChild(x)

    def remove(self, x):
        list.remove(self, x)
        self.__removeChild(x)
    
    def pop(self, i=-1):
        x = list.pop(self, i)
        self.__removeChild(x)
        return x
    
    def __removeChild(self, x):
        x.setParent(None)
        self.__removeId(x)
        
    def __appendChild(self, x):
        parent = x.getParent()
        if (parent == self):
            return
        if (parent):
            index = parent.index(x)
            parent.remove(index)
        x.setParent(self)
        self.__appendId(x)
    
    def __removeId(self, x):
        if (x.id):
            del self.__childids[x.id]
        if (isinstance(x, SVGContainer)):
            for id, child in x.__childids.iteritems():
                del self.__childids[id]
        if (self.getParent()):
            self.getParent().__removeId(x)
    
    def __appendId(self, x):
        id = x.id
        if (id):
            self.__childids[id] = x
        if (isinstance(x, SVGContainer)):
            for id, child in x.__childids.iteritems():
                self.__childids[id] = child
        if (self.getParent()):
            self.getParent().__appendId(x)
    
    def getElementById(self, id):
        if (self.id == id):
            return self
        return self.__childids.get(id, None)

# <svg> element
class SVGSVG(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        self.x = SVGLength(attrs.get((None, "x"), "0"))
        self.y = SVGLength(attrs.get((None, "y"), "0"))
        self.width = SVGLength(attrs.get((None, "width"), "0"))
        self.height = SVGLength(attrs.get((None, "height"), "0"))
        
    def callHandler(self, handler):
        handler.svg(self)

# synthetic: a generic unknown element
class SVGUnknowElement(SVGContainer):
    def __init__(self, attrs, parent=None, tag=None):
        SVGContainer.__init__(self, attrs, parent)
        self.tag = tag
        
    def callHandler(self, handler):
        handler.unknown(self)

# <title> element
class SVGTitle(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        
    def callHandler(self, handler):
        handler.title(self)
    
    def getTitle(self):
        title = ""
        for node in self:
            if (isinstance(node, SVGCharacters)):
                title += node.content
        return title

# <metadata> element
class SVGMetadata(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        self.__author = ""
        self.__description = ""
        self.__language = ""
        self.__license = ""
        self.__keywords = []
        
    def callHandler(self, handler):
        handler.metadata(self)
    
    def __getContent(self, node):
        content = ""
        for n in node:
            if (isinstance(n, SVGCharacters)):
                content += n.content
        return content

    def __getCreator(self, node):
        if (isinstance(node, SVGUnknowElement)):
            tag = node.tag
            if (tag == (SVGMetadata.__dc, "title")):
                self.__author = self.__getContent(node)
                return
        if (isinstance(node, SVGContainer)):
            for n in node:
                self.__getCreator(n)

    def __getMetadata(self, node):
        if (isinstance(node, SVGUnknowElement)):
            tag = node.tag
            if (tag == (SVGMetadata.__dc, "language")):
                self.__language = self.__getContent(node)
                return
            elif (tag == (SVGMetadata.__dc, "description")):
                self.__description = self.__getContent(node)
                return
            elif (tag == (SVGMetadata.__dc, "creator")):
                self.__getCreator(node)
                return
            elif (tag == (SVGMetadata.__cc, "license")):
                self.__license = node.attrs.get((Metadata.__rdf, "resource"), "")
                return
            elif (tag == (SVGMetadata.__rdf, "li")):
                self.__keywords.append(self.__getContent(node))
                return
        if (isinstance(node, SVGContainer)):
            for n in node:
                self.__getMetadata(n)

    def getAuthor(self):
        self.__getMetadata(self)
        return self.__author
    
    def getDescription(self):
        self.__getMetadata(self)
        return self.__description
        
    def getLanguage(self):
        self.__getMetadata(self)
        return self.__language
    
    def getLicense(self):
        self.__getMetadata(self)
        return self.__license
    
    def getKeywords(self):
        self.__keywords = []
        self.__getMetadata(self)
        return self.__keywords

# <rect> element
class SVGRect(SVGElement):
    def __init__(self, attrs, parent=None):
        SVGElement.__init__(self, attrs, parent)
        self.x = SVGLength(attrs.get((None, "x"), "0"))
        self.y = SVGLength(attrs.get((None, "y"), "0"))
        self.width = SVGLength(attrs.get((None, "width"), "0"))
        self.height = SVGLength(attrs.get((None, "height"), "0"))
        if (attrs.has_key((None, "rx"))):
            self.rx = SVGLength(attrs[(None, "rx")])
        else:
            self.rx = None
        if (attrs.has_key((None, "ry"))):
            self.ry = SVGLength(attrs[(None, "ry")])
        else:
            self.ry = None
        self.style = SVGStyle(attrs.get((None, "style"), ""))
        self.clip_path = attrs.get((None, "clip-path"), "")
        
    def callHandler(self, handler):
        handler.rect(self)

# no longer used
## <path> element
#class SVGPath(SVGElement):
#    def __init__(self, attrs, parent=None):
#        SVGElement.__init__(self, attrs, parent)
#        self.d = attrs.get((None, "d"), "")
#        self.style = SVGStyle(attrs.get((None, "style"), ""))
#        self.style_raw = attrs.get((None, "style"), "")
#        self.transform_raw = attrs.get((None, "transform"), "")
#        
#    def callHandler(self, handler):
#        handler.path(self)

# synthetic: simply embed a native SVG element
class SVGNative(SVGElement):
    def __init__(self, attrs, parent=None):
        SVGElement.__init__(self, attrs, parent)
        self.style = SVGStyle(attrs.get((None, "style"), ""))
        self.style_raw = attrs.get((None, "style"), "")
        
    def callHandler(self, handler):
        handler.native(self)

# synthetic: a <path sodipodi:type="arc" ...> element
class SVGPathArc(SVGElement):
    def __init__(self, attrs, parent=None):
        SVGElement.__init__(self, attrs, parent)
        self.cx = SVGLength(attrs.get((NS.SODIPODI, "cx"), "0"))
        self.cy = SVGLength(attrs.get((NS.SODIPODI, "cy"), "0"))
        self.rx = SVGLength(attrs.get((NS.SODIPODI, "rx"), "0"))
        self.ry = SVGLength(attrs.get((NS.SODIPODI, "ry"), "0"))
        self.style = SVGStyle(attrs.get((None, "style"), ""))
        self.clip_path = attrs.get((None, "clip-path"), "")
        self.d = attrs.get((None, "d"), "")
        
    def callHandler(self, handler):
        handler.arc(self)

# <g> element
class SVGGroup(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        self.clip_path = attrs.get((None, "clip-path"), "")
        self.groupmode = attrs.get((NS.INKSCAPE, "groupmode"), "")
        self.label = attrs.get((NS.INKSCAPE, "label"), "")
        self.style = SVGStyle(attrs.get((None, "style"), ""))

    def callHandler(self, handler):
        handler.group(self)

# <defs> element
class SVGDefine(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        
    def callHandler(self, handler):
        handler.define(self)

# <text> element
class SVGText(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        self.x = SVGLength(attrs.get((None, "x"), "0"))
        self.y = SVGLength(attrs.get((None, "y"), "0"))
        self.style = SVGStyle(attrs.get((None, "style"), ""))
        self.clip_path = attrs.get((None, "clip-path"), "")
        
    def callHandler(self, handler):
        handler.text(self)

# <tspan> element
class SVGTSpan(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        if ((None, "x") in attrs):
            self.x = SVGLength(attrs.get((None, "x")))
        else:
            self.x = None
        if ((None, "y") in attrs):
            self.y = SVGLength(attrs.get((None, "y")))
        else:
            self.y = None
        self.style = SVGStyle(attrs.get((None, "style"), ""))
        self.role = attrs.get((NS.SODIPODI, "role"))
        
    def callHandler(self, handler):
        handler.tspan(self)

# synthetic: a sequence of SVG characters (like text inside a <tspan>)
class SVGCharacters(SVGElement):
    def __init__(self, content, parent = None):
        SVGElement.__init__(self, {}, parent)
        self.content = content
    
    def callHandler(self, handler):
        handler.characters(self)

# <linearGradient> element
class SVGLinearGradient(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        self.x1 = SVGLength(attrs.get((None, "x1"), "0"))
        self.y1 = SVGLength(attrs.get((None, "y1"), "0"))
        self.x2 = SVGLength(attrs.get((None, "x2"), "0"))
        self.y2 = SVGLength(attrs.get((None, "y2"), "0"))
        self.gradientUnits = attrs.get((None, "gradientUnits"), "objectBoundingBox")
        self.gradientTransform = SVGTransform(attrs.get((None, "gradientTransform"), ""))
        
    def callHandler(self, handler):
        handler.linearGradient(self)

# <radialGradient> element
class SVGRadialGradient(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        self.cx = SVGLength(attrs.get((None, "cx"), "0"))
        self.cy = SVGLength(attrs.get((None, "cy"), "0"))
        self.fx = SVGLength(attrs.get((None, "fx"), "0"))
        self.fy = SVGLength(attrs.get((None, "fy"), "0"))
        self.r = SVGLength(attrs.get((None, "r"), "0"))
        self.gradientUnits = attrs.get((None, "gradientUnits"), "objectBoundingBox")
        self.gradientTransform = SVGTransform(attrs.get((None, "gradientTransform"), ""))
        
    def callHandler(self, handler):
        handler.radialGradient(self)

# <stop> element
class SVGStop(SVGElement):
    def __init__(self, attrs, parent=None):
        SVGElement.__init__(self, attrs, parent)
        self.offset = float(attrs.get((None, "offset"), "0"))
        self.style_raw = attrs.get((None, "style"), "")
        self.style = SVGStyle(attrs.get((None, "style"), ""))

    def callHandler(self, handler):
        handler.stop(self)

# <clipPath> element
class SVGClipPath(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        self.gradientUnits = attrs.get((None, "clipPathUnits"), "objectBoundingBox")
        
    def callHandler(self, handler):
        handler.clipPath(self)

# <image> element
class SVGImage(SVGElement):
    def __init__(self, attrs, parent=None):
        SVGElement.__init__(self, attrs, parent)
        self.x = SVGLength(attrs.get((None, "x"), "0"))
        self.y = SVGLength(attrs.get((None, "y"), "0"))
        self.width = SVGLength(attrs.get((None, "width"), "0"))
        self.height = SVGLength(attrs.get((None, "height"), "0"))
        self.clip_path = attrs.get((None, "clip-path"), "")

    def callHandler(self, handler):
        handler.image(self)

# <filter> element
class SVGFilter(SVGContainer):
    def __init__(self, attrs, parent=None):
        SVGContainer.__init__(self, attrs, parent)
        
    def callHandler(self, handler):
        handler.filter(self)

# <filterEffect> element
class SVGFilterEffect(SVGElement):
    def __init__(self, attrs, parent=None):
        SVGElement.__init__(self, attrs, parent)

# <feGaussianBlur> element
class SVGFEGaussianBlur(SVGFilterEffect):
    def __init__(self, attrs, parent=None):
        SVGFilterEffect.__init__(self, attrs, parent)
        self.stdDeviation = SVGLength(attrs.get((None, "stdDeviation"), "0"))


# represents a SVG length
class SVGLength:
    __length_re = re.compile(r"^(?P<length>[+\-0-9e.]*)(?P<unit>[%a-z]*)$")
    __px_per_unit = {
        "px": 1.0,
        "in": 90.0,
        "mm": 90.0/25.4,
        "cm": 90.0/2.54,
    }
    
    def __init__(self, length, unit = None):
        if (unit):
            self.__length = float(length)
            self.__unit = unit
        elif (isinstance(length, SVGLength)):
            self.__length = length.__length
            self.__unit = length.__unit
        else:
            m = SVGLength.__length_re.match(str(length))
            if (not m):
                raise TypeError("Bad length value: '%s'" % (str(length)))
            self.__length = float(m.group("length"))
            self.__unit = m.group("unit") or "px"
    
    def px(self):
        return self.__length * SVGLength.__px_per_unit[self.__unit]
        
    def __repr__(self):
        return "%.2f%s" % (self.__length, self.__unit)
        
    def __str__(self):
        return "%.2f%s" % (self.__length, self.__unit)
    
    def __add__(a, b):
        if (isinstance(b, SVGLength)):
            return SVGLength(a.px() + b.px(), "px")
        else:
            return SVGLength(a.px() + b, "px")

    def __sub__(a, b):
        if (isinstance(b, SVGLength)):
            return SVGLength(a.px() - b.px(), "px")
        else:
            return SVGLength(a.px() - b, "px")
    
    def __mul__(a, b):
        return SVGLength(a.__length * b, a.__unit)
    
    def __rmul__(a, b):
        return SVGLength(a.__length * b, a.__unit)
    
    def __div__(a, b):
        if (isinstance(b, SVGLength)):
            return a.px()/b.px()
        else:
            return SVGLength(a.__length / b, a.__unit)
        
    def __neg__(a):
        return SVGLength(-a.__length, a.__unit)
    
    def __pos__(a):
        return a;
    
    def __abs__(a):
        return SVGLength(abs(a.__length), a.__unit)
    
    def __float__(a):
        return a.px()
    
    def __lt__(a, b):
        return a.px() < SVGLength(b).px()
        
    def __le__(a, b):
        return a.px() <= SVGLength(b).px()
    
    def __eq__(a, b):
        return a.px() == SVGLength(b).px()
        
    def __ne__(a, b):
        return a.px() != SVGLength(b).px()
        
    def __gt__(a, b):
        return a.px() > SVGLength(b).px()
        
    def __ge__(a, b):
        return a.px() >= SVGLength(b).px()


# represent a SVG style
class SVGStyle(dict):
    def __init__(self, style=""):
        for item in style.split(";"):
            a = item.split(":")
            if (len(a) == 2):
                self[a[0]] = a[1]


# represent a SVG transform
class SVGTransform(list):
    class SVGBaseTransform:
        def toMatrix(self):
            raise TypeError("toMatrix can be called only on subclasses of SVGBaseTransform")
        
        def __mul__(self, a):
            return self.toMatrix() * a
        
        # no longer needed
        #def toStringMoz(self):
        #    return str(self)
        
        def inverse(self):
            return self.toMatrix().inverse()
            
    class SVGTranslate(SVGBaseTransform):
        def __init__(self, x, y="0"):
            self.x = SVGLength(x)
            self.y = SVGLength(y)
        
        def __str__(self):
            return "translate(%s,%s)" % (str(self.x), str(self.y))
        
        def __mul__(self, a):
            if (isinstance(a, SVGPoint)):
                return SVGPoint(a.x + self.x, a.y + self.y)
            elif (isinstance(a, SVGTransform.SVGTranslate)):
                return SVGTransform.SVGTranslate(a.x + self.x, a.y + self.y)
            elif isinstance(a, SVGTransform.SVGBaseTransform):
                m = a.toMatrix()
                return SVGTransform.SVGMatrix(m.a, m.b, m.c, m.d, m.e+self.x.px(), m.f+self.y.px())
            else:
                raise TypeError("Bad factor value: '%s'" % (str(a)))
        
        def toMatrix(self):
            return SVGTransform.SVGMatrix(1, 0, 0, 1, self.x, self.y)
        
        def inverse(self):
            return SVGTransform.SVGTranslate(-self.x, -self.y)

    class SVGMatrix(SVGBaseTransform):
        def __init__(self, a, b, c, d, e, f):
            self.a = float(a)
            self.b = float(b)
            self.c = float(c)
            self.d = float(d)
            self.e = float(e)
            self.f = float(f)
        
        def __str__(self):
            return "matrix(%f,%f,%f,%f,%f,%f)" % (self.a, self.b, self.c, self.d, self.e, self.f)
                
        def __mul__(self, a):
            if (isinstance(a, SVGPoint)):
                return SVGPoint(
                    self.a * a.x + self.c * a.y + self.e,
                    self.b * a.x + self.d * a.y + self.f)
            elif (isinstance(a, SVGTransform.SVGBaseTransform)):
                m = a.toMatrix()
                return SVGTransform.SVGMatrix(
                    self.a * m.a + self.c * m.b,
                    self.b * m.a + self.d * m.b,
                    self.a * m.c + self.c * m.d,
                    self.b * m.c + self.d * m.d,
                    self.a * m.e + self.c * m.f + self.e,
                    self.b * m.e + self.d * m.f + self.f
                )
            else:
                raise TypeError("Bad factor value: '%s'" % (str(a)))
        
        def toMatrix(self):
            return self
        
        def inverse(self):
            det = self.a * self.d - self.b * self.c
            return SVGTransform.SVGMatrix(
                self.d / det,
                -self.b / det,
                -self.c / det,
                self.a / det,
                0,
                0
            ) * SVGTransform.SVGTranslate(-self.e, -self.f)
            
        # no longer needed
        #def toStringMoz(self):
        #    return "matrix(%f,%f,%f,%f,%fpx,%fpx)" % (
        #        self.a,
        #        self.b,
        #        self.c,
        #        self.d,
        #        self.e,
        #        self.f
        #    )

    class SVGScale(SVGBaseTransform):
        def __init__(self, sx, sy=None):
            self.sx = float(sx)
            if (sy):
                self.sy = float(sy)
            else:
                self.sy = float(sx)
        
        def __str__(self):
            return "scale(%f,%f)" % (self.sx, self.sy)
                
        def __mul__(self, a):
            if (isinstance(a, SVGPoint)):
                return SVGPoint(self.sx * a.x, self.sy * a.y)
            elif (isinstance(a, SVGTransform.SVGScale)):
                return SVGTransform.Scale(self.sx * a.sx, self.sy * a.sy)
            elif (isinstance(a, SVGTransform.SVGBaseTransform)):
                m = a.toMatrix()
                return SVGTransform.SVGMatrix(
                    self.sx*m.a,
                    self.sy*m.b,
                    self.sx*m.c,
                    self.sy*m.d,
                    self.sx*m.e,
                    self.sy*m.f
                )
            else:
                raise TypeError("Bad factor value: '%s'" % (str(a)))
        
        def toMatrix(self):
            return SVGTransform.SVGMatrix(self.sx, 0, 0, self.sy, 0, 0)
        
        def inverse(self):
            return SVGTransform.SVGScale(1.0 / self.sx, 1.0 / self.sy)

    class SVGRotate(SVGBaseTransform):
        def __init__(self, angle, cx=None, cy=None):
            self.angle = float(angle)
            if (cx and cy):
                self.cx = SVGLength(cx)
                self.cy = SVGLength(cy)
            else:
                self.cx = None
                self.cy = None
        
        def __str__(self):
            if cx and cy:
                return "rotate(%fdeg)" % self.angle
            else:
                return str(self.toMatrix())
        
        def toMatrix(self):
            a = math.radians(self.angle)
            m = SVGTransform.SVGMatrix(math.cos(a), math.sin(a), -math.sin(a), math.cos(a), 0, 0)
            if (cx and cy):
                m = SVGTransform.SVGTranslate(self.cx, self.cy) * m * SVGTransform.SVGTranslate(-self.cx, -self.cy)
            return m
        
        def inverse(self):
            return SVGTransform.SVGRotate(-self.angle, self.cx, self.cy)

    class SVGSkewX(SVGBaseTransform):
        def __init__(self, angle):
            self.angle = float(angle)
        
        def __str__(self):
            return "skewX(%fdeg)" % self.angle
        
        def toMatrix(self):
            a = math.radians(self.angle)
            m = SVGTransform.SVGMatrix(1, 0, math.tan(a), 1, 0, 0)
            return m

    class SVGSkewY(SVGBaseTransform):
        def __init__(self, angle):
            self.angle = float(angle)
        
        def __str__(self):
            return "skewY(%fdeg)" % self.angle
        
        def toMatrix(self):
            a = math.radians(self.angle)
            m = SVGTransform.SVGMatrix(1, math.tan(a), 0, 1, 0, 0)
            return m

    __filter_re = re.compile(r"(?P<name>[a-z]+)\((?P<args>[e+\-0-9,.]*)\)", re.I)
    __transforms_dict = {
        "translate": SVGTranslate,
        "matrix": SVGMatrix,
        "scale": SVGScale,
        "rotate": SVGRotate,
        "skewX": SVGSkewX,
        "skewY": SVGSkewY,
    }
    def __init__(self, s):
        list.__init__(self)
        s = s.replace(" ", "").replace("\t", "")
        for m in SVGTransform.__filter_re.finditer(s):
            name = m.group("name")
            args = m.group("args").split(",")
            transform = SVGTransform.__transforms_dict[name](*args)
            self.append(transform)
        
    def __str__(self):
        return " ".join([str(f) for f in self])
        
    def toMatrix(self):
        ret = SVGTransform.SVGMatrix(1, 0, 0, 1, 0, 0)
        for m in self:
            ret = m * ret
        return ret


# represent a SVG point
class SVGPoint:
    def __init__(self, x, y):
        self.x = SVGLength(x)
        self.y = SVGLength(y)
    
    def __add__(a, b):
        return SVGPoint(a.x + b.x, a.y + b.y)
    
    def __sub__(a, b):
        return SVGPoint(a.x - b.x, a.y - b.y)
    
    def __mul__(a, b):
        if (isinstance(b, SVGPoint)):
            return a.x * b.x + a.y * b.y
        else:
            return SVGPoint(a.x * b, a.y * b)

    def __div__(a, b):
        return SVGPoint(a.x / b, a.y / b)
        
    def __abs__(self):
        return math.sqrt(self.x.px() * self.x.px() + self.y.px() * self.y.px())
        

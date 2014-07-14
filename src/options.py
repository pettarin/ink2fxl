#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__     = 'MIT'
__author__      = 'Alberto Pettarin (alberto@albertopettarin.it)'
__copyright__   = '2014 Alberto Pettarin (alberto@albertopettarin.it)'
__version__     = 'v0.0.2'
__date__        = '2014-07-14'
__description__ = 'Command line options, shared by svg2htmlcss and ink2fxl'

### BEGIN changelog ###
#
# 0.0.2 2014-07-14 Read config from file, added JPEG output 
# 0.0.1 2014-07-10 Initial release
#
### END changelog ###

class Options():

    # NOTE change the following paths, depending on your OS, e.g. to 
    # __inkscape_path = "/usr/bin/inkscape"
    # __convert_path = "/usr/bin/convert"
    __inkscape_path = "inkscape"
    __convert_path = "convert"

    __options = [
        ### EXPORT OPTIONS ###
        {
            "short": "-f",
            "long": "--outputformat",
            "type": "string",
            "dest": "outputformat",
            "default": "vector",
            "help": "Output format [vector|mixed|raster]",
            "required": True,
            "allowedValues": ["vector", "mixed", "raster"]
        },
        {
            "short": "-d",
            "long": "--outputdirectory",
            "type": "string",
            "dest": "outputdirectory",
            "default": "/tmp/",
            "help": "Write output files in this directory"
        },
        {
            "short": "-e",
            "long": "--exporthiddenlayers",
            "type": "inkbool",
            "dest": "exporthiddenlayers",
            "default": "true",
            "help": "Export hidden layers"
        },
        {
            "short": "-r",
            "long": "--renameidattributes",
            "type": "inkbool",
            "dest": "renameidattributes",
            "default": "false",
            "help": "Rename id attributes"
        },
        {
            "short": "-l",
            "long": "--uselayerlabels",
            "type": "inkbool",
            "dest": "uselayerlabels",
            "default": "false",
            "help": "Use Inkscape layer label instead of id"
        },
        {
            # TODO currently ignored
            "short": None,
            "long": "--gheuristic",
            "type": "inkbool",
            "dest": "gheuristic",
            "default": "false",
            "help": "Detect layers using <svg>-><g> heuristic (IGNORED)"
        },
        ### RASTER OPTIONS ###
        {
            "short": None,
            "long": "--rasterformat",
            "type": "string",
            "dest": "rasterformat",
            "default": "png",
            "help": "Raster format [png|jpg|jpeg]",
            "allowedValues": ["png", "jpg", "jpeg"]
        },
        {
            "short": "-b",
            "long": "--rasterlayerboundingbox",
            "type": "inkbool",
            "dest": "rasterlayerboundingbox",
            "default": "true",
            "help": "Crop layer to bounding box"
        },
        {
            "short": None,
            "long": "--rasterimagesubdirectory",
            "type": "string",
            "dest": "rasterimagesubdirectory",
            "default": "",
            "help": "Output images in subdirectory"
        },
        ### VECTOR OPTIONS ###
        {
            "short": None,
            "long": "--outputxhtmlfile",
            "type": "string",
            "dest": "outputxhtmlfile",
            "default": "index.xhtml",
            "help": "Name of the XHTML output file"
        },
        {
            "short": "-o",
            "long": "--outputcss",
            "type": "inkbool",
            "dest": "outputcss",
            "default": "true",
            "help": "Output CSS in a separate file"
        },
        {
            "short": None,
            "long": "--outputcssfile",
            "type": "string",
            "dest": "outputcssfile",
            "default": "style.css",
            "help": "Name of the CSS output file"
        },
        {
            "short": None,
            "long": "--includefiles",
            "type": "string",
            "dest": "includefiles",
            "default": "",
            "help": "Include references to CSS/JS files"
        },
        {
            "short": None,
            "long": "--explicitzindex",
            "type": "inkbool",
            "dest": "explicitzindex",
            "default": "false",
            "help": "Explicit z-index"
        },
        {
            "short": None,
            "long": "--insertplaceholders",
            "type": "inkbool",
            "dest": "insertplaceholders",
            "default": "false",
            "help": "Insert placeholders in XHTML code"
        },
        ### PAGE OPTIONS ###
        {
            "short": None,
            "long": "--pagetitle",
            "type": "string",
            "dest": "pagetitle",
            "default": "ink2fxl",
            "help": "Use this string as <title> of the generated XHTML page"
        },
        {
            "short": None,
            "long": "--pageoffsetleft",
            "type": "int",
            "dest": "pageoffsetleft",
            "default": "0",
            "help": "Add this offset (in px) to the left property of generated XHTML elements"
        },
        {
            "short": None,
            "long": "--pageoffsettop",
            "type": "int",
            "dest": "pageoffsettop",
            "default": "0",
            "help": "Add this offset (in px) to the top property of generated XHTML elements"
        },
        {
            "short": None,
            "long": "--pagebackgroundcolor",
            "type": "inkbool",
            "dest": "pagebackgroundcolor",
            "default": "false",
            "help": "Draw the page"
        },
        {
            "short": None,
            "long": "--pagebackgroundcolorstyle",
            "type": "string",
            "dest": "pagebackgroundcolorstyle",
            "default": "",
            "help": "Use these CSS directives for the page background-color"
        },
        {
            "short": None,
            "long": "--pageborder",
            "type": "inkbool",
            "dest": "pageborder",
            "default": "false",
            "help": "Draw the page border"
        },
        {
            "short": None,
            "long": "--pageborderstyle",
            "type": "string",
            "dest": "pageborderstyle",
            "default": "",
            "help": "Use these CSS directives for the page border"
        },
        ### LOG OPTIONS
        {
            "short": None,
            "long": "--logfile",
            "type": "string",
            "dest": "logfile",
            "default": "",
            "help": "Write log to file"
        },
        {
            "short": None,
            "long": "--logdelete",
            "type": "inkbool",
            "dest": "logdelete",
            "default": "true",
            "help": "Delete log after success"
        },
        ### CONFIG OPTIONS
        {
            "short": "-c",
            "long": "--config",
            "type": "string",
            "dest": "config",
            "default": "",
            "help": "Load configuration from file"
        },
        # the next ones are dummy needed for the Inkscape plugin window
        {
            "short": None,
            "long": "--zzz1",
            "type": "string",
            "dest": "zzz1",
            "default": "DUMMY",
            "help": "" 
        },
        {
            "short": None,
            "long": "--zzz2",
            "type": "string",
            "dest": "zzz2",
            "default": "DUMMY",
            "help": "" 
        }
    ]

    @classmethod
    def getInkscapePath(cls):
        return cls.__inkscape_path

    @classmethod
    def getConvertPath(cls):
        return cls.__convert_path

    @classmethod
    def getOptions(cls):
        return cls.__options

    # read config from file
    # by reading lines formatted like
    # key=value
    # where key is the dest field of __options above
    # Other lines are ignored
    #
    # Example:
    # outputformat=raster
    # outputdirectory=/tmp/
    #
    @classmethod
    def readConfigFromFile(cls, config_file_path):
        opt = {}
        try:
            f = open(config_file_path, "r")
            config = f.read()
            f.close()
            for line in config.splitlines():
                parts = line.split("=")
                if (len(parts) == 2):
                    k = parts[0].strip()
                    v = parts[1].strip()
                    opt[k] = v
        except:
            pass
        return opt

    # convert options (from optparse) to a regular dict
    @classmethod
    def convertToDict(cls, options): 
        options = vars(options)
        
        # if -c or --config has been specified,
        # read parameters from it
        # and override
        if (("config" in options) and (len(options["config"]) > 0)):
            opt = cls.readConfigFromFile(options["config"])
            for k in opt.keys():
                options[k] = opt[k]

        for o in cls.getOptions():
            if (o["type"] == "inkbool"):
                k = o["dest"]
                if (k in options):
                    options[k] = cls.isTrue(options[k])
        return options

    # verify that the given options make sense
    # options is a regular dict
    @classmethod
    def verifyOptions(cls, options):
        for o in cls.getOptions():
            dest = o["dest"]
            longf = o["long"]
            if (("required" in o) and (o["required"]) and (dest not in options)):
                return [False, "Required parameter '%s' is missing" % (longf)]
            if (("allowedValues" in o) and (options[dest] not in o["allowedValues"])):
                return [False, "Unrecognized value '%s' for parameter '%s'" % (str(options[dest]), longf)]
        return [True, None]

    # return true if value == "True", "true", True, or a string containing an integer != 0
    @classmethod
    def isTrue(cls, value):
        if (value != None):
            if (isinstance(value, bool)):
                return value
            if (isinstance(value, str)):
                try:
                    return (int(value) != 0)
                except:
                    pass
                return (value.lower() == "true")
        return False

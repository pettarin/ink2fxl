# ink2fxl 

**ink2fxl** converts Inkscape SVG files to XHTML+(SVG)+CSS, XHTML+raster (layer-wise), or raster-only (layer-wise).

* Version: 0.0.3
* Date: 2015-01-31
* Developer: [Alberto Pettarin](http://www.albertopettarin.it/) ([contact](http://www.albertopettarin.it/contact.html))
* License: the MIT License (MIT), see LICENSE.md


## Screenshot

![Inkscape SVG => XHTML in Firefox](https://github.com/pettarin/ink2fxl/raw/master/screenshots/inkice.png "Inkscape SVG => XHTML in Firefox")


## Usage

**ink2fxl** is available as an [Inkscape](http://www.inkscape.org/en/) plugin,
or as a stand alone Python script.

First of all, you need to choose which output format you want:

* `vector`: export to XHTML+(SVG)+CSS
* `mixed`: export XHTML and each Inkscape layer as a raster (PNG) image
* `raster`: export each layer as a raster (PNG) image

In `vector` mode, `rect`, `text`, and `path` arc elements
will be output as `<div>` and `<span>` with suitable CSS styling.
All other elements, like `<path>` elements described by nodes,
will be output as inline SVG islands.
Each layer gets its own `<div>`.

In `mixed` mode, you will get an XHTML structure, with a `<div...><img.../></div>`
for each layer, where the image is raster (PNG).
The layer image can be cropped to its bounding box or have the page size.

In `raster` mode, only the raster (PNG) image of each layer is output.


### Inkscape plugin

1. Copy all the files from the `src/` directory into your `~/.config/inkscape/extensions/` directory
2. Open Inkscape
3. Open Extensions > Export > Export to FXL

Note: if you plan to use the `mixed` or `raster` output formats,
(and you want to export raster images to JPEG instead of PNG),
you might need to edit the `__inkscape_path` (and `__convert_path`)
lines in file `options.py`.
You might need to install `python-lxml` before running the plugin.


### Stand alone script

1. Copy all the files from the `src/` directory on your machine
2. Run the `svgexporter.py` script

Note: if you plan to use the `mixed` or `raster` output formats,
(and you want to export raster images to JPEG instead of PNG),
you might need to edit the `__inkscape_path` (and `__convert_path`)
lines in file `options.py`.
You might need to install `python-lxml` before running the plugin.

The usage of the script is as follows:

```
$ python svgexporter.py -h

Usage: svgexporter.py [options] file.svg

Options:
  -h, --help            show this help message and exit
  -f OUTPUTFORMAT, --outputformat=OUTPUTFORMAT
                        Output format [vector|mixed|raster]
  -d OUTPUTDIRECTORY, --outputdirectory=OUTPUTDIRECTORY
                        Write output files in this directory
  -e EXPORTHIDDENLAYERS, --exporthiddenlayers=EXPORTHIDDENLAYERS
                        Export hidden layers
  -r RENAMEIDATTRIBUTES, --renameidattributes=RENAMEIDATTRIBUTES
                        Rename id attributes
  -l USELAYERLABELS, --uselayerlabels=USELAYERLABELS
                        Use Inkscape layer label instead of id
  --gheuristic=GHEURISTIC
                        Detect layers using <svg>-><g> heuristic (IGNORED)
  --rasterformat=RASTERFORMAT
                        Raster format [png|jpg|jpeg]
  -b RASTERLAYERBOUNDINGBOX, --rasterlayerboundingbox=RASTERLAYERBOUNDINGBOX
                        Crop layer to bounding box
  --rasterimagesubdirectory=RASTERIMAGESUBDIRECTORY
                        Output images in subdirectory
  --outputxhtmlfile=OUTPUTXHTMLFILE
                        Name of the XHTML output file
  -o OUTPUTCSS, --outputcss=OUTPUTCSS
                        Output CSS in a separate file
  --outputcssfile=OUTPUTCSSFILE
                        Name of the CSS output file
  --includefiles=INCLUDEFILES
                        Include references to CSS/JS files
  --explicitzindex=EXPLICITZINDEX
                        Explicit z-index
  --insertplaceholders=INSERTPLACEHOLDERS
                        Insert placeholders in XHTML code
  --pagetitle=PAGETITLE
                        Use this string as <title> of the generated XHTML page
  --pageoffsetleft=PAGEOFFSETLEFT
                        Add this offset (in px) to the left property of
                        generated XHTML elements
  --pageoffsettop=PAGEOFFSETTOP
                        Add this offset (in px) to the top property of
                        generated XHTML elements
  --pagebackgroundcolor=PAGEBACKGROUNDCOLOR
                        Draw the page
  --pagebackgroundcolorstyle=PAGEBACKGROUNDCOLORSTYLE
                        Use these CSS directives for the page background-color
  --pageborder=PAGEBORDER
                        Draw the page border
  --pageborderstyle=PAGEBORDERSTYLE
                        Use these CSS directives for the page border
  --logfile=LOGFILE     Write log to file
  --logdelete=LOGDELETE
                        Delete log after success
  -c CONFIG, --config=CONFIG
                        Load configuration from file
```

Boolean parameter values can be given as `0`/`1`, `false`/`true`, or `False`/`True`.

You can modify the default values by editing the `options.py` file.

Given the large number of options,
you might want to write a configuration file,
and pass it to the script with the `-c` or `--config` switch.
See the file `misc/sample.conf` for an example.


### Examples

```
  1. Print this usage message
     $ python svgexporter.py -h

  2. Export to vector with default settings
     $ python svgexporter.py -f vector drawing.svg

  3. Export to mixed with default settings
     $ python svgexporter.py -f mixed drawing.svg

  4. Export to raster with default settings
     $ python svgexporter.py -f raster drawing.svg

  5. Export to vector, drawing the page border
     $ python svgexporter.py -f vector --pageborder=1 --pageborderstyle="black 5px solid" drawing.svg

  6. Export to mixed, setting the page title and exporting each layer without cropping
     $ python svgexporter.py -f mixed --pagetitle="Custom title" -b 0 drawing.svg

  7. Export to raster, reading the Inkscape labels for the layers
     $ python svgexporter.py -f raster -l 1 drawing.svg

  8. Export to vector, creating page.xhtml and pos.css in /tmp/foo/ instead of default index.xhtml and style.css in /tmp/
     $ python svgexporter.py -f vector --outputxhtmlfile="page.xhtml" --outputcssfile="pos.css" -d "/tmp/foo/" drawing.svg

  9. Export to vector, and log to /tmp/my.log
     $ python svgexporter.py -f vector --logfile="/tmp/my.log" drawing.svg

  10. Export to vector, embedding CSS directive into the XHTML file, referencing foo.js and bar.js, and outputting z-index
     $ python svgexporter.py -f vector -o 0 --includefiles="foo.js,bar.js" --explicitzindex=1 drawing.svg

  11. Export to mixed, creating an img/ subdirectory for the layer images
     $ python svgexporter.py -f mixed --rasterimagesubdirectory="img/" drawing.svg

  12. Load options from file
     $ python svgexporter.py -c my.conf drawing.svg

  13. Load options from both command line and configuration file (latter has higher priority)
     $ python svgexporter.py -c my.conf -f vector drawing.svg
```


## License

**ink2fxl** is released under the MIT License, see the included file.


## Technical Notes

**ink2fxl** requires Python 2.7 (or later Python 2.x), with  module `python-lxml`.

To export to `mixed` or `raster` format, you need Inkscape installed on your system.
Edit the `__inkscape_path = "inkscape"` line in file `options.py`,
according to the path where the inkscape executable is located on your system.
Similarily, if you want JPEG output instead of PNG,
you need `convert` (provided by Imagemagick) installed on your system,
and edit the `__convert_path = "convert"` line in file `options.py`.

The provided source files have been tested to work out-of-the-box
on Debian Linux and Mac OS X.
(Windows users: apologies but I do not have a Windows machine to test/debug.)


## Limitations and Missing Features 

* Extend SVG parser to deal with e.g. `filter` elements in `vector` mode
* Better XHTML+CSS output for text elements in `vector` mode
* Use direct Inkscape and Imagemagick python bindings (possible? how?) instead of relying on subprocess
* Implement <g> heuristic to process "layers" in SVG files not generated by Inkscape
* Better z-index management
* CSS output formatting


## Acknowledgments

* _Paolo Carnovalini_ for early testing
* The plugin concept has been inspired by [SAWS](https://code.google.com/p/saws/)
* The SVG parser has been extended/refactored from [svg2css](https://github.com/shogo82148/svg2css)
* _pedrosacramento_ for reporting issue #2

[![Analytics](https://ga-beacon.appspot.com/UA-52776738-1/ink2fxl)](http://www.albertopettarin.it)

#!/usr/bin/env python3

import re
import sys
import os
import argparse
import logging
try:
    import colorlog
except ImportError:
    colorlog = None


def setup_logger(name="Logger"):
    """ Sets up a logging.Logger with the name $name. If the colorlog module
    is available, the logger will use colors, otherwise it will be in b/w.
    The colorlog module is available at
    https://github.com/borntyping/python-colorlog
    but can also easily be installed with e.g. 'sudo pip3 colorlog' or similar
    commands.
    
    Arguments:
        name: name of the logger

    Returns:
        Logger
    """
    if colorlog:
        _logger = colorlog.getLogger(name)
    else:
        _logger = logging.getLogger(name)

    if _logger.handlers:
        # the logger already has handlers attached to it, even though
        # we didn't add it ==> logging.get_logger got us an existing
        # logger ==> we don't need to do anything
        return _logger

    _logger.setLevel(logging.DEBUG)
    if colorlog is not None:
        sh = colorlog.StreamHandler()
        log_colors = {'DEBUG':    'cyan',
                      'INFO':     'green',
                      'WARNING':  'yellow',
                      'ERROR':    'red',
                      'CRITICAL': 'red'}
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(name)s:%(levelname)s:%(message)s',
            log_colors=log_colors)
    else:
        # no colorlog available:
        sh = logging.StreamHandler()
        formatter = logging.Formatter('%(name)s:%(levelname)s:%(message)s')
    sh.setFormatter(formatter)
    sh.setLevel(logging.DEBUG)
    _logger.addHandler(sh)

    if colorlog is None:
        _logger.debug("Module colorlog not available. Log will be b/w.")

    return _logger

logger = setup_logger("TemplateTest")


parser = argparse.ArgumentParser(description="Test Anki templates, i.e. fill in field values and CSS to get a HTML file that can be displayed in the web browser.")
parser.add_argument("template", help="The HTML template", type=str)
parser.add_argument("fields", help="python file with dictionary containing field values", type=str)
parser.add_argument("-s", "--style", help="Include CSS style sheet")
parser.add_argument("-o", "--output", help="Output HTML file", type=str, default="")
args = parser.parse_args()

if not args.output:
    args.output = os.path.splitext(args.template)[0] + "_out.html"

html_out = "<html>"
html_out += "<head>"
html_out += '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
html_out += "<title>{}</title>".format(args.template)

if args.style:
    if os.path.exists(args.style):

        html_out += "<style>"
        with open(args.style, "r") as css_file:
            html_out += css_file.read()
        html_out += "</style>"
    else:
        print("CSS file could not be found at {}".format(
            os.path.abspath(args.style)))
        sys.exit(1)

html_out += "</head>"
html_out += "<body>"

if not os.path.exists(args.template):
    logger.critical("HTML file/template could not be found at {}".format(
            os.path.abspath(args.template)))
    sys.exit(1)

fields = None
if os.path.exists(args.fields):
    # todo: this is not nice
    exec(open(args.fields).read())
else:
    logger.critical("fields file could not be found at {}".format(
            os.path.abspath(args.fields)))
    sys.exit(1)

remove_following = False
remove_close_field = None
with open(args.template) as template_file:
    for line in template_file:
        #print(line)
        # fixme: only works if there is only one conditional statement per line
        match = re.search("\{\{#([a-zA-Z_ 0-9]*)\}\}", line)
        if match:
            fld = match.group(1)
            #print(fld, "cond")
            if fld in fields:
                #print("in")
                if not fields[fld].strip():
                    #print("remove!")
                    remove_following = True
                    remove_close_field = fld
            continue
        match = re.search("\{\{\^([a-zA-Z_ 0-9]*)\}\}", line)
        if match:
            fld = match.group(1)
            #print(fld, "neg cond")
            if fld in fields:
                #print("in")
                if fields[fld].strip():
                    remove_following = True
                    remove_close_field = fld
                    #print("remove!")
            continue
        match = re.search("\{\{\/([a-zA-Z_ 0-9]*)\}\}", line)
        if match:
            fld = match.group(1)
            #print(fld, "cond end")
            if fld == remove_close_field:
                #print("in")
                #print("stop remove!")
                remove_following = False
                remove_close_field = None
            continue
        if remove_following:
            continue
        # and try to replace the fields with the field values above
        for field_name in fields.keys():
            line = re.sub("\{\{" + field_name + "\}\}", fields[field_name], line)
        html_out += line

html_out += "</body>"
html_out += "</html>"


with open(args.output, "w") as output_file:
    output_file.write(html_out)

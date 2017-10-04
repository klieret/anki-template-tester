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




def get_cli_args():
    parser = argparse.ArgumentParser(description="Test Anki templates, i.e. fill in field values and CSS to get a HTML file that can be displayed in the web browser.")
    parser.add_argument("template", help="The HTML template", type=str)
    parser.add_argument("fields", help="python file with dictionary containing field values", type=str)
    parser.add_argument("-s", "--style", help="Include CSS style sheet")
    parser.add_argument("-o", "--output", help="Output HTML file", type=str, default="")
    return parser.parse_args()




class TemplateTester(object):
    def __init__(self, template: str, fields: dict, css: str):
        self.html = ""
        self.template = template
        self.fields = fields
        self.css = css

    def render(self) -> str:
        self.start_html_file()
        self.main_loop()
        self.end_html_file()
        return self.html

    def start_html_file(self):
        self.html = "<html>"
        self.html += "<head>"
        self.html += '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
        self.html += "<title>{}</title>".format(args.template)

        if self.css:
            self.html += "<style>"
            self.html += self.css
            self.html += "</style>"
        
        self.html += "</head>"
        self.html += "<body>"

    def end_html_file(self):
        self.html += "</body>"
        self.html += "</html>"

    def main_loop(self):
        remove_following = False
        remove_close_field = None
        lines = self.template.split("\n")
        for line in lines:
            #print(line)
            # fixme: only works if there is only one conditional statement per line
            # fixme: also fails with {{text:blah blah}} as needed in the urls
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
            self.html += line


if __name__ == "__main__":
    logger = setup_logger("TemplateTest")
    args = get_cli_args()

    if not args.output:
        args.output = os.path.splitext(args.template)[0] + "_out.html"
        logger.warning("Output file name was automatically "
                       "set to {}.".format(args.output))

    css = ""
    if args.style:
        try:
            with open(args.style) as css_file:
                css = css_file.read()
        except:
            logger.error("Could not load css file from {}. "
                         "Leaving it empty.").format(args.style)

    template = ""
    try:
        with open(args.template) as template_file:
            template = template_file.read()
    except:
        _ = "Could not load template file from {}. " \
            "Abort.".format(args.template)
        logger.critical(_)
        raise

    fields = {}
    if args.fields:
        try:
            with open(args.fields) as field_file:
                # todo: this is not nice
                exec(field_file.read())
        except:
            _ = "Could not load template file from {}. " \
                "Abort.".format(args.template)
            raise

    tt = TemplateTester(template, fields, css)
    html_out = tt.render()

    with open(args.output, "w") as output_file:
        output_file.write(html_out)

    logger.info("Output written to {}".format(args.output))

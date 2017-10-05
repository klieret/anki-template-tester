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
from typing import Dict, List


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



def get_cli_args():
    parser = argparse.ArgumentParser(description="Test Anki templates, i.e. fill in field values and CSS to get a HTML file that can be displayed in the web browser.")
    parser.add_argument("template", help="The HTML template", type=str)
    parser.add_argument("fields", help="python file with dictionary containing field values", type=str)
    parser.add_argument("-s", "--style", help="Include CSS style sheet")
    parser.add_argument("-o", "--output", help="Output HTML file", type=str, default="")
    return parser.parse_args()


def next_braces(string):
    match = re.search(r"\{\{([^\}]*)\}\}", string)
    if not match:
        before = string
        enclosed = ""
        after = ""
    else:
        enclosed = match.groups(0)[0]
        before = string[:match.span(0)[0]]
        after = string[match.span(0)[1]:]
    return before, enclosed, after


def is_pos_conditional(string: str) -> bool:
    return string.startswith("#")


def is_neg_conditional(string: str) -> bool:
    return string.startswith("^")


def is_close_conditional(string: str) -> bool:
    return string.startswith("/")


def is_field(string: str) -> bool:
    return string and not is_pos_conditional(string) and not is_neg_conditional(string) and not is_close_conditional(string)


def get_field_name(string: str) -> str:
    if is_pos_conditional(string):
        return string[1:]
    if is_neg_conditional(string):
        return string[1:]
    if is_close_conditional(string):
        return string[1:]
    if is_field(string):
        return string
    return ""


def evaluate_conditional(string: str, fields: Dict[str, str]) -> bool:
    field_name = get_field_name(string)
    if field_name not in fields:
        logger.warning("Field '{}' from conditional '{}' not defined! "
                       "Will evaluate conditional to "
                       "True!".format(field_name, string))
        return True
    if is_pos_conditional(string):
        return bool(fields[field_name].strip())
    if is_neg_conditional(string):
        return not bool(fields[field_name].strip())
    raise ValueError


def evaluate_conditional_chain(conditional_chain: List[str], fields: Dict[str, str]) -> bool:
    for conditional in conditional_chain:
        if not evaluate_conditional(conditional, fields):
            return False
    return True


def process_line(line: str, conditional_chain: List[str], fields: Dict[str, str]):
    after = line
    out = ""
    while after:
        before, enclosed, after = next_braces(after)
        # print(out, before, enclosed, after, conditional_chain, sep="|")
        if evaluate_conditional_chain(conditional_chain, fields):
            out += before
        if is_pos_conditional(enclosed) or is_neg_conditional(enclosed):
            conditional_chain.append(enclosed)
        elif is_close_conditional(enclosed):
            if not len(conditional_chain) >= 1:
                logger.error("Closing conditional '{}' found, but we didn't "
                             "encounter a conditional before.".format(enclosed))
            else:
                field_name = get_field_name(enclosed)
                if field_name not in conditional_chain[-1]:
                    logger.error("Closing conditional '{}' found, "
                                 "but the last opened conditional "
                                 "was {}. "
                                 "I will ignore this.".format(enclosed,
                                                              field_name))
                else:
                    conditional_chain.pop()
        elif is_field(enclosed):
            # print(enclosed)
            out += fields[get_field_name(enclosed).replace("text:", "")]
    return out, conditional_chain


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
        lines = self.template.split("\n")
        conditional_chain = []
        for line in lines:
            out, conditional_chain = process_line(line, conditional_chain, self.fields)
            self.html += out


if __name__ == "__main__":
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

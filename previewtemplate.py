#!/usr/bin/env python3

import re
import os
import argparse
import logging
try:
    import colorlog
except ImportError:
    colorlog = None
from typing import Dict, List
import csv

"""Small tool to preview templates for the spaced repetition flashcard program
 Anki.
 https://github.com/klieret/anki-template-tester
"""


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


def import_dict(filename: str) -> Dict[str, str]:
    """ Read a csv file and interpret each line as entries for a dictionary.
    Used to import the exemplary field values from a text file.
    """
    ret = {}
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=":", quotechar='"')
        i = 0
        for row in reader:
            i += 1
            if not len(row) == 2:
                logger.warning("Row {} of file {} does not seem to have "
                               "the proper format. Skip.".format(i, filename))
                continue
            ret[row[0]] = row[1]
    return ret


def get_cli_args():
    """ Get arguments from command line. """
    _ = "Test Anki templates, i.e. fill in field values and CSS to get a " \
        "HTML file that can be displayed in the web browser."
    parser = argparse.ArgumentParser(description=_)
    parser.add_argument("template", help="The HTML template", type=str)
    _ = "python file with dictionary containing field values"
    parser.add_argument("fields", help=_, type=str)
    parser.add_argument("-s", "--style", help="Include CSS style sheet")
    _ = "Output HTML file"
    parser.add_argument("-o", "--output", help=_, type=str, default="")
    return parser.parse_args()


def next_braces(string: str) -> (str, str, str):
    """Go through the string $string and find the next value contained in
    double braces, e.g. "before {{foo}} after" would return the triple
    ("before ", "foo", " after").

    Args:
        string: Input string.

    Returns: (before, enclosed, after)
        before: Everything before the double braces
        enclosed: String enclosed in the double braces
        after: Everything after the double braces.
    """
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


def is_pos_conditional(enclosed: str) -> bool:
    """ True if {{$enclosed}} corresponds to the beginning of an 'if empty'
    statement on the Anki card template.
    """
    return enclosed.startswith("#")


def is_neg_conditional(enclosed: str) -> bool:
    """ True if {{$enclosed}} corresponds to the beginning of an 'if not empty'
    statement on the Anki card template.
    """
    return enclosed.startswith("^")


def is_close_conditional(enclosed: str) -> bool:
    """ True if {{$enclosed}} corresponds to the end of an 'if' statement
    on the Anki card template.
    """
    return enclosed.startswith("/")


def is_field(enclosed: str) -> bool:
    """ True if {{$enclosed}} corresponds to a field value
    on the Anki card template.
    """
    return enclosed and not is_pos_conditional(enclosed) and not \
        is_neg_conditional(enclosed) and not is_close_conditional(enclosed)


def get_field_name(enclosed: str) -> str:
    """ Gets the name of the field which is used in the {{$enclosed}}
    statement on the Anki card template."""
    if is_pos_conditional(enclosed):
        return enclosed[1:]
    if is_neg_conditional(enclosed):
        return enclosed[1:]
    if is_close_conditional(enclosed):
        return enclosed[1:]
    if is_field(enclosed):
        enclosed = enclosed.replace("text:", "")
        return enclosed
    return ""


def evaluate_conditional(string: str, fields: Dict[str, str]) -> bool:
    """ Evaluates a conditional from $string on a Anki card template
    using the field values $fields. """
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


def evaluate_conditional_chain(conditional_chain: List[str],
                               fields: Dict[str, str]) -> bool:
    """ When we go through the template, we encounter conditionals, which
    can be enclosed in each other. This means that at any point of the
    template we can be inside a list of conditionals ($conditional_chain).
    Here we test if the whole $conditional_chain evaluates to true, i.e.
    if the code enclosed would be run.
    """
    for conditional in conditional_chain:
        if not evaluate_conditional(conditional, fields):
            return False
    return True


def process_line(line: str, conditional_chain: List[str],
                 fields: Dict[str, str]):
    """ Processes a line in the template, i.e. returns the output html code
    after evaluating all if statements and filling the fields. Since we
    oftentimes are in the middle of several if statements, we need to pass
    the current conditional_chain (i.e. the list of if statments the following
    line will be subject to) on (and also need to use it).

    Args:
        line: Line we are processing
        conditional_chain: In which conditionals are we currently enclosed?
        fields: field values

    Returns:
        (html output, conditional_chain)
    """
    after = line
    out = ""
    while after:
        before, enclosed, after = next_braces(after)
        if evaluate_conditional_chain(conditional_chain, fields):
            out += before
        if is_pos_conditional(enclosed) or is_neg_conditional(enclosed):
            conditional_chain.append(enclosed)
        elif is_close_conditional(enclosed):
            if not len(conditional_chain) >= 1:
                _ = "Closing conditional '{}' found, but we didn't encounter" \
                    " a conditional before.".format(enclosed)
                logger.error(_)
            else:
                field_name = get_field_name(enclosed)
                if field_name not in conditional_chain[-1]:
                    _ = "Closing conditional '{}' found, but the last opened" \
                        " conditional was {}. I will " \
                        "ignore this.".format(enclosed, field_name)
                    logger.error(_)
                else:
                    conditional_chain.pop()
        elif is_field(enclosed):
            field_name = get_field_name(enclosed)
            if field_name in fields:
                out += fields[field_name]
            else:
                _ = "Could not find value for field '{}'".format(field_name)
                logger.error(_)
    return out, conditional_chain


class TemplateTester(object):
    """ Main object that processes the template, the fields and the style
    sheet. """
    def __init__(self, template: str, fields: Dict[str, str], css: str):
        self.html = ""
        self.template = template
        self.fields = fields
        self.css = css

    def render(self) -> str:
        """ Parse the template and return the html string. """
        self._start_html_file()
        self._main_loop()
        self._end_html_file()
        return self.html

    def _start_html_file(self):
        """ Start html file. """
        self.html = "<html>"
        self.html += "<head>"
        self.html += '<meta http-equiv="Content-Type" content="text/html; ' \
                     'charset=utf-8" />'
        self.html += "<title>{}</title>".format("Rending")

        if self.css:
            self.html += "<style>"
            self.html += self.css
            self.html += "</style>"
        
        self.html += "</head>"
        self.html += "<body>"

    def _end_html_file(self):
        """ End html file. """
        self.html += "</body>"
        self.html += "</html>"

    def _main_loop(self):
        """ Process template line by line. """
        lines = self.template.split("\n")
        conditional_chain = []
        for line in lines:
            out, conditional_chain = process_line(line, conditional_chain,
                                                  self.fields)
            self.html += out


if __name__ == "__main__":
    args = get_cli_args()

    if not args.output:
        args.output = os.path.splitext(args.template)[0] + "_out.html"
        logger.warning("Output file name was automatically "
                       "set to {}.".format(args.output))

    css_ = ""
    if args.style:
        try:
            with open(args.style) as css_file:
                css_ = css_file.read()
        except:
            logger.error("Could not load css file from {}. "
                         "Leaving it empty.").format(args.style)

    template_ = ""
    try:
        with open(args.template) as template_file:
            template_ = template_file.read()
    except:
        _ = "Could not load template file from {}. " \
            "Abort.".format(args.template)
        logger.critical(_)
        raise

    fields_ = {}
    if args.fields:
        try:
                fields_ = import_dict(args.fields)
        except:
            _ = "Could not load template file from {}. " \
                "Abort.".format(args.template)
            raise

    tt = TemplateTester(template_, fields_, css_)
    html_out = tt.render()

    with open(args.output, "w") as output_file:
        output_file.write(html_out)

    logger.info("Output written to {}".format(args.output))

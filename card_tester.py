#!/usr/bin/env python3

import re
import sys
import os
import argparse

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
    print("HTML file/template could not be found at {}".format(
            os.path.abspath(args.template)))
    sys.exit(1)

fields = None
if os.path.exists(args.fields):
    # todo: this is not nice
    exec(open(args.fields).read())
else:
    print("fields file could not be found at {}".format(
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

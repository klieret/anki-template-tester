# Anki Template Tester

Small tool to preview templates for the spaced repetition flashcard program [Anki](https://apps.ankiweb.net/).
When writing templatex, the built in template editor of Anki can become quite cumbersome. On the other hand one cannot just preview the card templates in the webbrowser due to the Anki specific elements (filling of the field values, conditional statements).

This small script takes a template (and a CSS style sheet) together with a file which contains some exemplary field values and gives back a HTML file which can be properly viewed in the browser.

## Usage

```
$ python3 template-tester.py --help
usage: template-tester.py [-h] [-s STYLE] [-o OUTPUT] template fields

Test Anki templates, i.e. fill in field values and CSS to get a HTML file that
can be displayed in the web browser.

positional arguments:
  template              The HTML template
  fields                python file with dictionary containing field values

optional arguments:
  -h, --help            show this help message and exit
  -s STYLE, --style STYLE
                        Include CSS style sheet
  -o OUTPUT, --output OUTPUT
                        Output HTML file
```
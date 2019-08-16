# Anki Template Tester

**[Overview over my Anki add-ons](http://www.lieret.net/opensource/#anki)**

Small tool to preview templates for the spaced repetition flashcard program [Anki](https://apps.ankiweb.net/).
When writing templates, the built in template editor of Anki can become quite cumbersome. On the other hand one cannot just preview the card templates in the webbrowser due to the Anki specific elements (filling of the field values, conditional statements).

This small script takes a template (and a CSS style sheet) together with a file which contains some exemplary field values and gives back a HTML file which can be properly viewed in the browser.


| Branch | Description | Travis |
| -------| ----------- | ------ | 
| [master](https://github.com/klieret/anki-template-tester/tree/master) | (Hopefully) stable release | [![Build Status](https://travis-ci.org/klieret/anki-template-tester.svg?branch=master)](https://travis-ci.org/klieret/anki-template-tester) | 
| [development](https://github.com/klieret/anki-template-tester/tree/development)| Work on new features in progress. Might be completely broken from time to time. | [![Build Status](https://travis-ci.org/klieret/anki-template-tester.svg?branch=development)](https://travis-ci.org/klieret/anki-template-tester) | 


## Installation

All that is needed is the stand alone file ```previewtemplate.py``` and a python3 installation. If your python version is earlier than 3.4, please install the ```typing``` module, e.g. via ```sudo pip3 install typing```. 

## Usage

```
$ python3 previewtemplate.py --help
usage: previewtemplate.py [-h] [-s STYLE] [-o OUTPUT] template fields

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

## License

MIT license. See file ```license.txt``` enclosed in the repository.

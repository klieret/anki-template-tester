#!/usr/bin/env python3

import unittest

from templatetester import *


class TestParsing(unittest.TestCase):

    def test_next_braces(self):
        qa = {"foo {{bar}} foobar": ("foo ", "bar", " foobar"),
              "foo {bar}} foobar": ("foo {bar}} foobar", "", ""),
              "foo {{bar": ("foo {{bar", "", ""),
              "{{bar}} foobar": ("", "bar", " foobar"),
              "{{bar}}": ("", "bar", "")}
        for q, a in qa.items():
            with self.subTest(question=q):
                self.assertEqual(next_braces(q), a)

    def test_get_field_name(self):
        qa = {"asdf": "asdf",
              "": "",
              "^asf": "asf",
              "/asdf": "asdf",
              "#asdf": "asdf"}
        for q, a in qa.items():
            with self.subTest(question=q):
                self.assertEqual(get_field_name(q), a)

    def test_evaluate_conditional_chain(self):
        fields = {"t": "asf", "tt": "xyz", "ttt": "asdf",
                  "f": "", "ff": "  ", "fff": " "}
        qa = {("#t", "#tt", "#ttt"): True,
              ("#t",): True,
              ("^t",): False,
              (): True,
              ("#f",): False,
              ("#t", "#tt", "#f", "#ttt"): False,
              ("^t", "^ff"): False}
        for q, a in qa.items():
            with self.subTest(question=q):
                self.assertEqual(evaluate_conditional_chain(list(q), fields), a)

    def test_process_line(self):
        fields = {"t": "asf", "tt": "xyz", "ttt": "asdf",
                  "f": "", "ff": "  ", "fff": " "}
        qa = {"{{#t}} asdf {{/t}}": " asdf ",
              "{{#t}} asdf ": " asdf ",
              "{{#t}} yes {{#f}} xyt": " yes ",
              "before {{#t}} yes {{#f}} no {{/f}} blah {{/t}}": "before  yes  blah "}
        for q, a in qa.items():
            with self.subTest(question=q):
                self.assertEqual(process_line(q, [], fields), a)

if __name__ == '__main__':
    unittest.main()

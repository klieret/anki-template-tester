#!/usr/bin/env python3

from templatetester import *

before, enclosed, after = next_braces("foo {{bar}} foobar")
assert before == "foo "
assert enclosed == "bar"
assert after == " foobar"

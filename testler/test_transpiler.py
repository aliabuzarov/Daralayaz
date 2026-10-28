"""Transpilerə aid avtomatik testlər.

İşlətmə: python -m unittest testler.test_transpiler
"""

import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from transpiler import transpile_source


def run_transpiled(source):
    py_code = transpile_source(source)
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        env = {}
        exec(py_code, env)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return output


class TranspilerTest(unittest.TestCase):
    def test_transpile_print_and_math(self):
        out = run_transpiled("x = 10\ny = 20\nyaz x + y")
        self.assertEqual(out.strip(), "30")

    def test_transpile_conditions(self):
        out = run_transpiled('x = 5\nəgər x > 0:\n    yaz "müsbət"\nəks halda:\n    yaz "mənfi"')
        self.assertEqual(out.strip(), "müsbət")

    def test_transpile_loops(self):
        source = (
            "cəm = 0\n"
            "hər i içində aralıq(1, 5):\n"
            "    cəm = cəm + i\n"
            "yaz cəm"
        )
        out = run_transpiled(source)
        self.assertEqual(out.strip(), "10")

    def test_transpile_function(self):
        source = (
            "funksiya kvadrat(x):\n"
            "    qaytar x * x\n"
            "yaz kvadrat(7)"
        )
        out = run_transpiled(source)
        self.assertEqual(out.strip(), "49")

    def test_transpile_class(self):
        source = (
            "sinif Adam:\n"
            "    funksiya yarat(özü, ad):\n"
            "        özü.ad = ad\n"
            "    funksiya salamla(özü):\n"
            '        yaz "Salam, " + özü.ad\n'
            'a = Adam("Nigar")\n'
            "a.salamla()"
        )
        out = run_transpiled(source)
        self.assertEqual(out.strip(), "Salam, Nigar")


if __name__ == "__main__":
    unittest.main()

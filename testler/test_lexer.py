"""Lexerə aid avtomatik testlər (Marhala 1).

İşlətmə: python -m unittest testler.test_lexer
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from lexer import Lexer, LexerError, Token


def tokens_of(source):
    return Lexer(source).tokenize()


def token_types(source):
    return [t.type for t in tokens_of(source)]


class LexerTest(unittest.TestCase):
    def test_yaz_oxu(self):
        toks = tokens_of('yaz "Salam"\nad = oxu("Ad: ")')
        types = [t.type for t in toks]
        self.assertIn("ACAR_SÖZ", types)
        self.assertIn("IDENTİFİKATOR", types)
        self.assertIn("MƏTN", types)
        self.assertIn("OPERATOR", types)

    def test_reqemler(self):
        toks = tokens_of("x = 10\ny = 3.14")
        nums = [t.value for t in toks if t.type == "RƏQƏM"]
        self.assertIn("10", nums)
        self.assertIn("3.14", nums)

    def test_operatörler(self):
        toks = tokens_of("a == b\nc != d\ne <= f\ng >= h\ni ** j")
        ops = [t.value for t in toks if t.type == "OPERATOR"]
        self.assertIn("==", ops)
        self.assertIn("!=", ops)
        self.assertIn("<=", ops)
        self.assertIn(">=", ops)
        self.assertIn("**", ops)

    def test_azerbaycan_herfleri(self):
        toks = tokens_of("səbəp = 5\nsalam_dunya = 1")
        idents = [t.value for t in toks if t.type == "IDENTİFİKATOR"]
        self.assertIn("səbəp", idents)
        self.assertIn("salam_dunya", idents)

    def test_acar_sözlər(self):
        toks = tokens_of("əgər x > 0:\n    yaz x")
        kws = [t.value for t in toks if t.type == "ACAR_SÖZ"]
        self.assertIn("əgər", kws)
        self.assertIn("yaz", kws)

    def test_shehri_atilir(self):
        toks = tokens_of("x = 1 # bu bir şehridir\nyaz x")
        values = [t.value for t in toks]
        self.assertNotIn("bu bir şehridir", values)

    def test_indent_dedent(self):
        source = "əgər x > 0:\n    yaz 1\n    yaz 2\nyaz 3"
        types = token_types(source)
        self.assertIn("GIRIŞ", types)
        self.assertIn("ÇIXIŞ", types)

    def test_acilmamis_meten(self):
        with self.assertRaises(LexerError) as ctx:
            tokens_of('x = "salams')
        self.assertIn("Açılmamış", str(ctx.exception))
        self.assertIn("sətir 1", str(ctx.exception))

    def test_tanimlanmayan_simvol(self):
        with self.assertRaises(LexerError) as ctx:
            tokens_of("x = @")
        self.assertIn("Tanınmayan", str(ctx.exception))

    def test_sotron(self):
        toks = tokens_of("x = 1")
        self.assertEqual(toks[-1].type, "SON")

    def test_pi_sabiti(self):
        toks = tokens_of("r = PI * 2")
        idents = [t.value for t in toks if t.type == "IDENTİFİKATOR"]
        self.assertIn("PI", idents)

    def test_meten_cixar(self):
        toks = tokens_of('yaz "salam, dünya!"')
        metnler = [t.value for t in toks if t.type == "MƏTN"]
        self.assertEqual(metnler, ["salam, dünya!"])

    def test_setir_sutun(self):
        toks = tokens_of("ab = 1")
        ident = toks[0]
        self.assertEqual(ident.line, 1)
        self.assertEqual(ident.column, 1)


if __name__ == "__main__":
    unittest.main()

"""Interpreterə aid avtomatik testlər (Marhala 3).

İşlətmə: python -m unittest testler.test_interpreter
"""

import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from interpreter import Interpreter, RuntimeError


def run(source):
    from lexer import Lexer
    from parser import Parser

    interpreter = Interpreter()
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        tokens = Lexer(source).tokenize()
        statements = Parser(tokens).parse()
        interpreter.run(statements)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    return output


class InterpreterTest(unittest.TestCase):
    def test_yaz_reqem(self):
        out = run("yaz 42")
        self.assertEqual(out.strip(), "42")

    def test_yaz_meten(self):
        out = run('yaz "Salam, Dünya!"')
        self.assertEqual(out.strip(), "Salam, Dünya!")

    def test_yaz_bool(self):
        out = run("yaz doğru")
        self.assertEqual(out.strip(), "doğru")

        out = run("yaz yalan")
        self.assertEqual(out.strip(), "yalan")

    def test_yaz_bos(self):
        out = run("yaz boş")
        self.assertEqual(out.strip(), "boş")

    def test_deyisen_teyin_ve_yaz(self):
        out = run("x = 10\nyaz x")
        self.assertEqual(out.strip(), "10")

    def test_deyisen_emeliyyatlar(self):
        out = run("x = 5\ny = 3\nyaz x + y\nyaz x - y\nyaz x * y\nyaz x / y")
        self.assertEqual(out.strip(), "8\n2\n15\n1.6666666666666667")

    def test_sabit(self):
        out = run("sabit PI = 3.14\nyaz PI")
        self.assertEqual(out.strip(), "3.14")

    def test_sabit_yeniden_teyin_olmur(self):
        with self.assertRaises(RuntimeError) as ctx:
            run("sabit PI = 3.14\nPI = 3")
        self.assertIn("sabitidir", str(ctx.exception))

    def test_topla_farkli_tip(self):
        with self.assertRaises(RuntimeError) as ctx:
            run("yaz 5 + [1, 2]")
        self.assertIn("toplana bilməz", str(ctx.exception))

    def test_topla_metn_eded(self):
        out = run('yaz 5 + " alma"')
        self.assertEqual(out.strip(), "5 alma")

    def test_bolu_sifira(self):
        with self.assertRaises(RuntimeError) as ctx:
            run("yaz 10 / 0")
        self.assertIn("sıfıra bölünmə", str(ctx.exception))

    def test_deyisen_tapilmazsa(self):
        with self.assertRaises(RuntimeError) as ctx:
            run("yaz x")
        self.assertIn("tapılmadı", str(ctx.exception))

    def test_ustunluluk_hesabla(self):
        out = run("yaz 2 + 3 * 4")
        self.assertEqual(out.strip(), "14")

    def test_brassek(self):
        out = run("yaz (2 + 3) * 4")
        self.assertEqual(out.strip(), "20")

    def test_darbox(self):
        out = run("yaz 2 ** 3")
        self.assertEqual(out.strip(), "8")

    def test_unar_minus(self):
        out = run("yaz -5")
        self.assertEqual(out.strip(), "-5")

    def test_muqayise(self):
        out = run("yaz 5 > 3\nyaz 2 == 2\nyaz 1 != 1")
        self.assertEqual(out.strip(), "doğru\ndoğru\nyalan")

    def test_ve_operator(self):
        out = run("yaz doğru və yalan\nyaz doğru və doğru")
        self.assertEqual(out.strip(), "yalan\ndoğru")

    def test_ve_ya_operator(self):
        out = run("yaz yalan və ya doğru\nyaz yalan və ya yalan")
        self.assertEqual(out.strip(), "doğru\nyalan")

    def test_yox_operator(self):
        out = run("yaz yox doğru")
        self.assertEqual(out.strip(), "yalan")

    def test_azerbaycan_herfli_deyisen(self):
        out = run("səba = 7\nyaz səba")
        self.assertEqual(out.strip(), "7")

    def test_coplu_setir(self):
        out = run("a = 1\nb = 2\nc = a + b\nyaz c")
        self.assertEqual(out.strip(), "3")

    def test_if_stmt(self):
        out = run('x = 5\nəgər x > 0:\n    yaz "positive"')
        self.assertEqual(out.strip(), "positive")

    def test_if_else(self):
        out = run('x = -5\nəgər x > 0:\n    yaz "pos"\nəks halda:\n    yaz "neg"')
        self.assertEqual(out.strip(), "neg")

    def test_if_elif_else(self):
        out = run('x = 0\nəgər x > 0:\n    yaz "pos"\nyoxsa əgər x < 0:\n    yaz "neg"\nəks halda:\n    yaz "zero"')
        self.assertEqual(out.strip(), "zero")

    def test_short_circuit_ve(self):
        out = run("yaz yalan və (10 / 0 == 0)")
        self.assertEqual(out.strip(), "yalan")

    def test_short_circuit_ve_ya(self):
        out = run("yaz doğru və ya (10 / 0 == 0)")
        self.assertEqual(out.strip(), "doğru")

    def test_error_line_number_variable(self):
        with self.assertRaises(RuntimeError) as ctx:
            run("a = 1\nyaz tapilmayan")
        self.assertIn("sətir 2", str(ctx.exception))

    def test_error_line_number_constant(self):
        with self.assertRaises(RuntimeError) as ctx:
            run("sabit PI = 3.14\nPI = 3")
        self.assertIn("sətir 2", str(ctx.exception))

    def test_error_line_number_zero_division(self):
        with self.assertRaises(RuntimeError) as ctx:
            run("a = 5\nb = 0\nyaz a / b")
        self.assertIn("sətir 3", str(ctx.exception))

    def test_while_loop(self):
        source = (
            "i = 1\n"
            "cəm = 0\n"
            "nə qədər ki i <= 3:\n"
            "    cəm = cəm + i\n"
            "    i = i + 1\n"
            "yaz cəm"
        )
        out = run(source)
        self.assertEqual(out.strip(), "6")

    def test_for_loop_and_araliq(self):
        source = (
            "cəm = 0\n"
            "hər x içində aralıq(1, 4):\n"
            "    cəm = cəm + x\n"
            "yaz cəm"
        )
        out = run(source)
        self.assertEqual(out.strip(), "6")

    def test_loop_break_and_continue(self):
        source = (
            "nəticə = 0\n"
            "hər x içində aralıq(1, 10):\n"
            "    əgər x == 2:\n"
            "        davam\n"
            "    əgər x == 5:\n"
            "        dayan\n"
            "    nəticə = nəticə + x\n"
            "yaz nəticə"
        )
        # x = 1 (1), 2 (skip), 3 (1+3=4), 4 (4+4=8), 5 (break) -> 8
        out = run(source)
        self.assertEqual(out.strip(), "8")

    def test_function_and_recursion(self):
        source = (
            "funksiya faktorial(n):\n"
            "    əgər n <= 1:\n"
            "        qaytar 1\n"
            "    əks halda:\n"
            "        qaytar n * faktorial(n - 1)\n"
            "yaz faktorial(5)"
        )
        out = run(source)
        self.assertEqual(out.strip(), "120")

    def test_closure(self):
        source = (
            "funksiya yaradici(x):\n"
            "    funksiya artir(y):\n"
            "        qaytar x + y\n"
            "    qaytar artir\n"
            "f = yaradici(10)\n"
            "yaz f(5)"
        )
        out = run(source)
        self.assertEqual(out.strip(), "15")

    def test_lists_and_dicts(self):
        source = (
            "s = [10, 20, 30]\n"
            "əlavə(s, 40)\n"
            "yaz uzunluq(s)\n"
            "yaz s[0]\n"
            "s[1] = 99\n"
            "yaz s[1]\n"
            'l = {"ad": "Ali", "yas": 25}\n'
            'yaz l["ad"]'
        )
        out = run(source)
        self.assertEqual(out.strip(), "4\n10\n99\nAli")

    def test_class_constructor_and_inheritance(self):
        source = (
            "sinif Heyvan:\n"
            "    funksiya yarat(özü, ad):\n"
            "        özü.ad = ad\n"
            "    funksiya danış(özü):\n"
            '        yaz özü.ad + " seslenir"\n'
            "sinif It miras Heyvan:\n"
            "    funksiya danış(özü):\n"
            '        yaz özü.ad + " hüpür"\n'
            'h = Heyvan("Qara")\n'
            "h.danış()\n"
            'i = It("Toplan")\n'
            "i.danış()"
        )
        out = run(source)
        self.assertEqual(out.strip(), "Qara seslenir\nToplan hüpür")

    def test_try_catch_and_throw(self):
        source = (
            "yoxla:\n"
            '    at "Xüsusi xəta baş verdi"\n'
            "tut e:\n"
            '    yaz "Tutuldu: " + e'
        )
        out = run(source)
        self.assertIn("Tutuldu:", out)
        self.assertIn("Xüsusi xəta", out)

    def test_import_math(self):
        source = (
            'idxal "riyaziyyat"\n'
            "yaz riyaziyyat.kök(16)"
        )
        out = run(source)
        self.assertEqual(out.strip(), "4")


if __name__ == "__main__":
    unittest.main()

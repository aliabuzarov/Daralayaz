"""Parserə aid avtomatik testlər (Marhala 2).

İşlətmə: python -m unittest testler.test_parser
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from lexer import Lexer
from parser import (
    Parser,
    ParseError,
    Number,
    String,
    Boolean,
    NoneNode,
    Identifier,
    BinaryOp,
    UnaryOp,
    PrintStmt,
    IfStmt,
    AssignStmt,
    ExpressionStmt,
)


def parse(source):
    toks = Lexer(source).tokenize()
    return Parser(toks).parse()


class ParserTest(unittest.TestCase):
    def test_yaz(self):
        stmts = parse('yaz "Salam"')
        self.assertIsInstance(stmts[0], PrintStmt)
        self.assertIsInstance(stmts[0].expr, String)
        self.assertEqual(stmts[0].expr.value, "Salam")

    def test_reqem(self):
        stmts = parse("yaz 42")
        self.assertIsInstance(stmts[0], PrintStmt)
        self.assertIsInstance(stmts[0].expr, Number)
        self.assertEqual(stmts[0].expr.value, 42)

    def test_reqem_kesr(self):
        stmts = parse("yaz 3.14")
        self.assertEqual(stmts[0].expr.value, 3.14)

    def test_bool(self):
        stmts = parse("yaz doğru")
        self.assertIsInstance(stmts[0].expr, Boolean)
        self.assertTrue(stmts[0].expr.value)

        stmts = parse("yaz yalan")
        self.assertFalse(stmts[0].expr.value)

    def test_bos(self):
        stmts = parse("yaz boş")
        self.assertIsInstance(stmts[0].expr, NoneNode)

    def test_ident(self):
        stmts = parse("yaz x")
        self.assertIsInstance(stmts[0].expr, Identifier)
        self.assertEqual(stmts[0].expr.name, "x")

    def test_assign(self):
        stmts = parse("x = 10")
        self.assertIsInstance(stmts[0], AssignStmt)
        self.assertEqual(stmts[0].name, "x")
        self.assertEqual(stmts[0].value.value, 10)

    def test_toplama(self):
        stmts = parse("yaz 1 + 2")
        binop = stmts[0].expr
        self.assertIsInstance(binop, BinaryOp)
        self.assertEqual(binop.op, "+")
        self.assertEqual(binop.left.value, 1)
        self.assertEqual(binop.right.value, 2)

    def test_ustunluluk(self):
        # 1 + 2 * 3  =>  1 + (2 * 3)
        stmts = parse("yaz 1 + 2 * 3")
        binop = stmts[0].expr
        self.assertEqual(binop.op, "+")
        self.assertIsInstance(binop.right, BinaryOp)
        self.assertEqual(binop.right.op, "*")

    def test_bracket(self):
        # (1 + 2) * 3
        stmts = parse("yaz (1 + 2) * 3")
        binop = stmts[0].expr
        self.assertEqual(binop.op, "*")
        self.assertIsInstance(binop.left, BinaryOp)
        self.assertEqual(binop.left.op, "+")

    def test_darbox(self):
        # 2 ** 3 ** 2  =>  2 ** (3 ** 2)
        stmts = parse("yaz 2 ** 3 ** 2")
        binop = stmts[0].expr
        self.assertEqual(binop.op, "**")
        self.assertIsInstance(binop.right, BinaryOp)
        self.assertEqual(binop.right.op, "**")

    def test_unar_minus(self):
        stmts = parse("yaz -5")
        unary = stmts[0].expr
        self.assertIsInstance(unary, UnaryOp)
        self.assertEqual(unary.op, "-")
        self.assertEqual(unary.operand.value, 5)

    def test_unar_yox(self):
        stmts = parse("yaz yox doğru")
        unary = stmts[0].expr
        self.assertEqual(unary.op, "yox")
        self.assertIsInstance(unary.operand, Boolean)
        self.assertTrue(unary.operand.value)

    def test_car(self):
        stmts = parse("yaz 1 == 2")
        binop = stmts[0].expr
        self.assertEqual(binop.op, "==")
        self.assertEqual(binop.left.value, 1)
        self.assertEqual(binop.right.value, 2)

    def test_ve(self):
        stmts = parse("yaz doğru və yalan")
        binop = stmts[0].expr
        self.assertEqual(binop.op, "və")
        self.assertTrue(binop.left.value)
        self.assertFalse(binop.right.value)

    def test_ve_ya(self):
        stmts = parse("yaz doğru və ya yalan")
        binop = stmts[0].expr
        self.assertEqual(binop.op, "və ya")
        self.assertTrue(binop.left.value)

    def test_multiple_statements(self):
        stmts = parse("x = 1\nyaz x")
        self.assertEqual(len(stmts), 2)
        self.assertIsInstance(stmts[0], AssignStmt)
        self.assertIsInstance(stmts[1], PrintStmt)

    def test_syntax_error(self):
        with self.assertRaises(ParseError) as ctx:
            parse("yaz")
        self.assertIn("Xəta (sətir 1)", str(ctx.exception))

    def test_shehri_atiq_da_yaz(self):
        stmts = parse('yaz "salam" # bu şehridir')
        self.assertEqual(len(stmts), 1)
        self.assertEqual(stmts[0].expr.value, "salam")

    def test_if_stmt(self):
        stmts = parse('əgər x > 0:\n    yaz "positive"')
        self.assertIsInstance(stmts[0], IfStmt)
        self.assertEqual(len(stmts[0].then_branch), 1)
        self.assertIsInstance(stmts[0].then_branch[0], PrintStmt)
        self.assertEqual(stmts[0].else_branch, None)
        self.assertEqual(len(stmts[0].elif_branches), 0)

    def test_if_elif_else(self):
        source = ('əgər x > 0:\n'
                  '    yaz "pos"\n'
                  'yoxsa əgər x < 0:\n'
                  '    yaz "neg"\n'
                  'əks halda:\n'
                  '    yaz "zero"')
        stmts = parse(source)
        if_stmt = stmts[0]
        self.assertIsInstance(if_stmt, IfStmt)
        self.assertEqual(len(if_stmt.elif_branches), 1)
        self.assertIsInstance(if_stmt.else_branch, list)
        self.assertEqual(len(if_stmt.else_branch), 1)

    def test_if_missing_colon(self):
        with self.assertRaises(ParseError) as ctx:
            parse("əgər x > 0\n    yaz x")
        self.assertIn("Xəta (sətir 1)", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

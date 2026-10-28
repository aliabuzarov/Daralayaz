"""Dərələyəz interpreterin giriş nöqtəsi (main).

İstifadə:
    python main.py                     (İnteraktiv REPL rejimi)
    python main.py fayl.dz             (Faylı icra etmək)
    python main.py --python fayl.dz    (Python koduna tərcümə rejimi)
"""

import sys
import os
from lexer import Lexer, LexerError
from parser import Parser, ParseError, ExpressionStmt
from interpreter import Interpreter, RuntimeError
from transpiler import PythonTranspiler


def run_file(filename):
    """Verilmiş .dz faylını oxuyur və icra edir."""
    if not os.path.exists(filename):
        print(f"Xəta: '{filename}' faylı tapılmadı.", file=sys.stderr)
        return 1

    try:
        with open(filename, "r", encoding="utf-8") as f:
            source = f.read()

        tokens = Lexer(source).tokenize()
        statements = Parser(tokens).parse()
        interpreter = Interpreter()
        interpreter.run(statements)
        return 0
    except (LexerError, ParseError, RuntimeError) as e:
        print(e, file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Gözlənilməz xəta: {e}", file=sys.stderr)
        return 1


def transpile_file(filename):
    """Verilmiş .dz faylını Python koduna tərcümə edib ekrana çıxarır."""
    if not os.path.exists(filename):
        print(f"Xəta: '{filename}' faylı tapılmadı.", file=sys.stderr)
        return 1

    try:
        with open(filename, "r", encoding="utf-8") as f:
            source = f.read()

        tokens = Lexer(source).tokenize()
        statements = Parser(tokens).parse()
        py_code = PythonTranspiler().transpile(statements)
        print(py_code)
        return 0
    except (LexerError, ParseError) as e:
        print(e, file=sys.stderr)
        return 1


def repl():
    """İnteraktiv terminal rejimi (REPL)."""
    print("Dərələyəz 1.0 (İnteraktiv Rejim / REPL)")
    print("Kodu daxil edin (çıxmaq üçün 'çıx', 'exit' və ya Ctrl+D):")
    interpreter = Interpreter()

    while True:
        try:
            line = input(">>> ")
            if line.strip() in ("çıx", "exit", "quit"):
                print("Sağ olun!")
                break
            if not line.strip():
                continue

            tokens = Lexer(line).tokenize()
            statements = Parser(tokens).parse()
            for stmt in statements:
                if isinstance(stmt, ExpressionStmt):
                    val = interpreter.evaluate(stmt.expr)
                    if val is not None:
                        print(interpreter._format(val))
                else:
                    interpreter.execute(stmt)
        except (LexerError, ParseError, RuntimeError) as e:
            print(e, file=sys.stderr)
        except (KeyboardInterrupt, EOFError):
            print("\nSağ olun!")
            break
        except Exception as e:
            print(f"Gözlənilməz xəta: {e}", file=sys.stderr)


def main():
    if len(sys.argv) == 1:
        repl()
        return 0

    if sys.argv[1] in ("--python", "-p", "--tərcümə"):
        if len(sys.argv) < 3:
            print("İstifadə: python main.py --python fayl.dz", file=sys.stderr)
            return 1
        return transpile_file(sys.argv[2])

    return run_file(sys.argv[1])


if __name__ == "__main__":
    sys.exit(main())

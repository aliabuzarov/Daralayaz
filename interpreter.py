"""Interpreter modulu (Marhala 3–10).

AST düyünlərini yürüdür, mühit (environment/scope) idarə edir,
dəyişənlər, dövrlər, funksiyalar, siniflər və modulları dəstəkləyir.
"""

import math
import random
import os
import sys

from parser import (
    Number,
    String,
    Boolean,
    NoneNode,
    Identifier,
    BinaryOp,
    UnaryOp,
    PrintStmt,
    AssignStmt,
    ExpressionStmt,
    IfStmt,
    WhileStmt,
    ForStmt,
    BreakStmt,
    ContinueStmt,
    CallExpr,
    IndexExpr,
    GetAttrExpr,
    SetAttrStmt,
    SetItemStmt,
    ListLiteral,
    DictLiteral,
    FunctionDef,
    ReturnStmt,
    ClassDef,
    TryStmt,
    ThrowStmt,
    ImportStmt,
)


class BreakSignal(Exception):
    """'dayan' əmri üçün siqnal."""
    pass


class ContinueSignal(Exception):
    """'davam' əmri üçün siqnal."""
    pass


class ReturnSignal(Exception):
    """'qaytar' əmri üçün siqnal."""
    def __init__(self, value):
        self.value = value


class RuntimeError(Exception):
    """İcra zamanında baş verən xətalar üçün."""
    pass


class Environment:
    """Dəyişən ad-dəyər cütlərini saxlayan scoped mühit."""

    def __init__(self, parent=None):
        self.variables = {}
        self.constants = set()
        self.parent = parent

    def define(self, name, value, is_constant=False, line=None):
        """Mühitdə yeni dəyişən və ya sabit yaradır."""
        if name in self.constants:
            line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
            raise RuntimeError(
                f"Xəta ({line_str}): '{name}' sabitidir, yenidən təyin edilə bilməz"
            )
        self.variables[name] = value
        if is_constant:
            self.constants.add(name)

    def get(self, name, line=None):
        """Dəyişənin dəyərini döndürür; tapılmasa xəta verir."""
        if name in self.variables:
            return self.variables[name]
        if self.parent is not None:
            return self.parent.get(name, line=line)
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        raise RuntimeError(f"Xəta ({line_str}): '{name}' dəyişəni tapılmadı")

    def set(self, name, value, line=None):
        """Mövcud dəyişənin dəyərini yeniləyir (mühit ağacında yuxarıya doğru axtarır)."""
        if name in self.variables:
            if name in self.constants:
                line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
                raise RuntimeError(
                    f"Xəta ({line_str}): '{name}' sabitidir, yenidən təyin edilə bilməz"
                )
            self.variables[name] = value
            return
        if self.parent is not None:
            self.parent.set(name, value, line=line)
            return
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        raise RuntimeError(f"Xəta ({line_str}): '{name}' dəyişəni tapılmadı")

    def set_or_define(self, name, value, line=None):
        """Dəyişən mövcuddursa yeniləyir, yoxdursa cari mühitdə təyin edir."""
        if name in self.variables:
            if name in self.constants:
                line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
                raise RuntimeError(
                    f"Xəta ({line_str}): '{name}' sabitidir, yenidən təyin edilə bilməz"
                )
            self.variables[name] = value
            return
        if self.parent is not None and self.parent.has(name):
            self.parent.set(name, value, line=line)
            return
        self.variables[name] = value

    def has(self, name):
        if name in self.variables:
            return True
        if self.parent is not None:
            return self.parent.has(name)
        return False


class DZFunction:
    """İstifadəçi tərəfindən təyin edilən funksiya (closure dəstəyi ilə)."""

    def __init__(self, name, params, body, closure_env):
        self.name = name
        self.params = params
        self.body = body
        self.closure_env = closure_env

    def __call__(self, *args):
        call_env = Environment(parent=self.closure_env)
        for i, param in enumerate(self.params):
            val = args[i] if i < len(args) else None
            call_env.define(param, val)
        interpreter = Interpreter(env=call_env)
        try:
            for stmt in self.body:
                interpreter.execute(stmt)
        except ReturnSignal as ret:
            return ret.value
        return None

    def bind(self, instance):
        return DZMethod(self, instance)

    def __repr__(self):
        return f"<funksiya {self.name}>"


class DZMethod:
    """Obyektə bağlanmış metod."""

    def __init__(self, function, instance):
        self.function = function
        self.instance = instance

    def __call__(self, *args):
        return self.function(self.instance, *args)

    def __repr__(self):
        return f"<metod {self.function.name}>"


class DZClass:
    """İstifadəçi tərəfindən təyin edilmiş sinif."""

    def __init__(self, name, superclass, methods):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def find_method(self, name):
        if name in self.methods:
            return self.methods[name]
        if self.superclass is not None and isinstance(self.superclass, DZClass):
            return self.superclass.find_method(name)
        return None

    def __call__(self, *args):
        instance = DZInstance(self)
        initializer = self.find_method("yarat")
        if initializer is not None:
            bound = initializer.bind(instance)
            bound(*args)
        return instance

    def __repr__(self):
        return f"<sinif {self.name}>"


class DZInstance:
    """Sinifdən yaradılmış obyekt nümunəsi."""

    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    def get(self, name, line=None):
        if name in self.fields:
            return self.fields[name]
        method = self.klass.find_method(name)
        if method is not None:
            return method.bind(self)
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        raise RuntimeError(
            f"Xəta ({line_str}): '{self.klass.name}' obyektində '{name}' sahəsi və ya metodu tapılmadı"
        )

    def set(self, name, value):
        self.fields[name] = value

    def __repr__(self):
        return f"<{self.klass.name} obyekti>"


class DZModule:
    """İdxal olunmuş modul."""

    def __init__(self, name, exports):
        self.name = name
        self.exports = exports

    def get(self, name, line=None):
        if name in self.exports:
            return self.exports[name]
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        raise RuntimeError(f"Xəta ({line_str}): '{self.name}' modulunda '{name}' tapılmadı")

    def __repr__(self):
        return f"<modul '{self.name}'>"


def create_global_environment():
    """Standart daxili funksiyalar olan qlobal mühiti yaradır."""
    env = Environment()

    def dz_araliq(*args):
        if len(args) == 1:
            return list(range(int(args[0])))
        if len(args) == 2:
            return list(range(int(args[0]), int(args[1])))
        if len(args) == 3:
            return list(range(int(args[0]), int(args[1]), int(args[2])))
        raise RuntimeError("Xəta: aralıq() funksiyası 1, 2 və ya 3 ədəd arqument tələb edir")

    def dz_uzunluq(obj):
        if hasattr(obj, "__len__"):
            return len(obj)
        raise RuntimeError(f"Xəta: '{type(obj).__name__}' tipinin uzunluğu yoxdur")

    def dz_elave(lst, item):
        if isinstance(lst, list):
            lst.append(item)
            return lst
        raise RuntimeError("Xəta: əlavə() funksiyası yalnız siyahılara tətbiq olunur")

    def dz_tip(val):
        if val is None:
            return "boş"
        if isinstance(val, bool):
            return "məntiq"
        if isinstance(val, (int, float)):
            return "ədəd"
        if isinstance(val, str):
            return "mətn"
        if isinstance(val, list):
            return "siyahı"
        if isinstance(val, dict):
            return "lüğət"
        if isinstance(val, DZInstance):
            return val.klass.name
        if isinstance(val, DZClass):
            return "sinif"
        if isinstance(val, (DZFunction, DZMethod)):
            return "funksiya"
        return type(val).__name__

    def dz_oxu(prompt=""):
        try:
            return input(str(prompt))
        except EOFError:
            return ""

    env.define("aralıq", dz_araliq)
    env.define("uzunluq", dz_uzunluq)
    env.define("əlavə", dz_elave)
    env.define("tip", dz_tip)
    env.define("oxu", dz_oxu)

    return env


class Interpreter:
    """AST-ni icra edən interpreter."""

    def __init__(self, env=None):
        if env is None:
            self.globals = create_global_environment()
            self.locals = self.globals
        else:
            self.globals = env
            self.locals = env

    def run(self, statements):
        """Statement siyahısını sırasıyla icra edir."""
        for stmt in statements:
            self.execute(stmt)

    def execute(self, node):
        method_name = "execute_" + type(node).__name__
        method = getattr(self, method_name, None)
        if method is None:
            line_str = f"sətir {node.line}" if getattr(node, "line", None) is not None else "sətir bilinməz"
            raise RuntimeError(f"Xəta ({line_str}): '{type(node).__name__}' icra edilə bilməz")
        return method(node)

    def evaluate(self, node):
        method_name = "evaluate_" + type(node).__name__
        method = getattr(self, method_name, None)
        if method is None:
            line_str = f"sətir {node.line}" if getattr(node, "line", None) is not None else "sətir bilinməz"
            raise RuntimeError(f"Xəta ({line_str}): '{type(node).__name__}' qiymətləndirilə bilməz")
        return method(node)

    # ----- statements -----

    def execute_PrintStmt(self, node):
        value = self.evaluate(node.expr)
        print(self._format(value))

    def execute_AssignStmt(self, node):
        value = self.evaluate(node.value)
        if getattr(node, "is_constant", False):
            self.locals.define(node.name, value, is_constant=True, line=node.line)
        else:
            self.locals.set_or_define(node.name, value, line=node.line)

    def execute_SetAttrStmt(self, node):
        target = self.evaluate(node.target)
        value = self.evaluate(node.value)
        if hasattr(target, "set"):
            target.set(node.attr, value)
            return
        line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
        raise RuntimeError(f"Xəta ({line_str}): '{type(target).__name__}' obyektinə atribut mənimsədilə bilməz")

    def execute_SetItemStmt(self, node):
        target = self.evaluate(node.target)
        index = self.evaluate(node.index)
        value = self.evaluate(node.value)
        line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
        if isinstance(target, list):
            if not isinstance(index, int):
                raise RuntimeError(f"Xəta ({line_str}): siyahı indeksi tam ədəd olmalıdır")
            if index < 0 or index >= len(target):
                raise RuntimeError(f"Xəta ({line_str}): siyahı indeksi sərhəddən kənardır")
            target[index] = value
            return
        if isinstance(target, dict):
            target[index] = value
            return
        raise RuntimeError(f"Xəta ({line_str}): '{type(target).__name__}' indekslə mənimsətməni dəstəkləmir")

    def execute_ExpressionStmt(self, node):
        self.evaluate(node.expr)

    def execute_IfStmt(self, node):
        if self._is_truthy(self.evaluate(node.condition)):
            for stmt in node.then_branch:
                self.execute(stmt)
            return
        for cond, branch in node.elif_branches:
            if self._is_truthy(self.evaluate(cond)):
                for stmt in branch:
                    self.execute(stmt)
                return
        if node.else_branch is not None:
            for stmt in node.else_branch:
                self.execute(stmt)

    def execute_WhileStmt(self, node):
        while self._is_truthy(self.evaluate(node.condition)):
            try:
                for stmt in node.body:
                    self.execute(stmt)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def execute_ForStmt(self, node):
        iterable = self.evaluate(node.iterable)
        if not hasattr(iterable, "__iter__"):
            line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
            raise RuntimeError(f"Xəta ({line_str}): '{type(iterable).__name__}' üzərində dövr edilə bilməz")
        for item in iterable:
            self.locals.set_or_define(node.var, item, line=node.line)
            try:
                for stmt in node.body:
                    self.execute(stmt)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def execute_BreakStmt(self, node):
        raise BreakSignal()

    def execute_ContinueStmt(self, node):
        raise ContinueSignal()

    def execute_FunctionDef(self, node):
        func = DZFunction(node.name, node.params, node.body, self.locals)
        self.locals.set_or_define(node.name, func, line=node.line)

    def execute_ReturnStmt(self, node):
        value = self.evaluate(node.value) if node.value is not None else None
        raise ReturnSignal(value)

    def execute_ClassDef(self, node):
        superclass = None
        if node.superclass is not None:
            superclass = self.locals.get(node.superclass, line=node.line)
            if not isinstance(superclass, DZClass):
                line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
                raise RuntimeError(f"Xəta ({line_str}): miras alınan '{node.superclass}' sinif deyil")

        methods = {}
        for stmt in node.body:
            if isinstance(stmt, FunctionDef):
                method_func = DZFunction(stmt.name, stmt.params, stmt.body, self.locals)
                methods[stmt.name] = method_func

        klass = DZClass(node.name, superclass, methods)
        self.locals.set_or_define(node.name, klass, line=node.line)

    def execute_TryStmt(self, node):
        try:
            for stmt in node.try_body:
                self.execute(stmt)
        except RuntimeError as e:
            if node.error_var is not None:
                self.locals.set_or_define(node.error_var, str(e))
            for stmt in node.catch_body:
                self.execute(stmt)

    def execute_ThrowStmt(self, node):
        msg = self.evaluate(node.expr)
        line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
        raise RuntimeError(f"Xəta ({line_str}): {msg}")

    def execute_ImportStmt(self, node):
        mod_name = node.module_name
        line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"

        # Standart kitabxana: riyaziyyat
        if mod_name == "riyaziyyat":
            exports = {
                "pi": math.pi,
                "e": math.e,
                "kök": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "mütləq": abs,
                "yuvarlaq": round,
                "döşəmə": math.floor,
                "tavan": math.ceil,
            }
            self.locals.set_or_define("riyaziyyat", DZModule("riyaziyyat", exports), line=node.line)
            return

        # Standart kitabxana: təsadüfi
        if mod_name == "təsadüfi":
            exports = {
                "ədəd": random.randint,
                "seç": random.choice,
                "qarışdır": random.shuffle,
            }
            self.locals.set_or_define("təsadüfi", DZModule("təsadüfi", exports), line=node.line)
            return

        # Standart kitabxana: fayl
        if mod_name == "fayl":
            def oxu_fayl(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

            def yaz_fayl(path, content):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(str(content))

            exports = {
                "oxu": oxu_fayl,
                "yaz": yaz_fayl,
            }
            self.locals.set_or_define("fayl", DZModule("fayl", exports), line=node.line)
            return

        # Cari qovluqda .dz faylı axtarışı
        target_path = mod_name if mod_name.endswith(".dz") else mod_name + ".dz"
        if os.path.exists(target_path):
            from lexer import Lexer
            from parser import Parser

            with open(target_path, "r", encoding="utf-8") as f:
                src = f.read()
            tokens = Lexer(src).tokenize()
            stmts = Parser(tokens).parse()
            module_interp = Interpreter()
            module_interp.run(stmts)
            self.locals.set_or_define(
                os.path.splitext(os.path.basename(target_path))[0],
                DZModule(mod_name, module_interp.locals.variables),
                line=node.line,
            )
            return

        raise RuntimeError(f"Xəta ({line_str}): '{mod_name}' modulu tapılmadı")

    # ----- expressions -----

    def evaluate_Number(self, node):
        return node.value

    def evaluate_String(self, node):
        return node.value

    def evaluate_Boolean(self, node):
        return node.value

    def evaluate_NoneNode(self, node):
        return None

    def evaluate_Identifier(self, node):
        return self.locals.get(node.name, line=node.line)

    def evaluate_ListLiteral(self, node):
        return [self.evaluate(elem) for elem in node.elements]

    def evaluate_DictLiteral(self, node):
        d = {}
        for k_expr, v_expr in node.pairs:
            k = self.evaluate(k_expr)
            v = self.evaluate(v_expr)
            d[k] = v
        return d

    def evaluate_CallExpr(self, node):
        callee = self.evaluate(node.callee)
        args = [self.evaluate(arg) for arg in node.args]
        if callable(callee):
            try:
                return callee(*args)
            except RuntimeError:
                raise
            except Exception as e:
                line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
                raise RuntimeError(f"Xəta ({line_str}): {e}")
        line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
        raise RuntimeError(f"Xəta ({line_str}): '{self._format(callee)}' çağırıla bilən funksiya və ya sinif deyil")

    def evaluate_IndexExpr(self, node):
        target = self.evaluate(node.target)
        index = self.evaluate(node.index)
        line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
        if isinstance(target, (list, str)):
            if not isinstance(index, int):
                raise RuntimeError(f"Xəta ({line_str}): indeks tam ədəd olmalıdır")
            if index < 0 or index >= len(target):
                raise RuntimeError(f"Xəta ({line_str}): indeks sərhəddən kənardır")
            return target[index]
        if isinstance(target, dict):
            if index not in target:
                raise RuntimeError(f"Xəta ({line_str}): '{index}' açarı tapılmadı")
            return target[index]
        raise RuntimeError(f"Xəta ({line_str}): '{type(target).__name__}' tipli veriləndə indeksləmə dəstəklənmir")

    def evaluate_GetAttrExpr(self, node):
        target = self.evaluate(node.target)
        if hasattr(target, "get"):
            return target.get(node.attr, line=node.line)
        line_str = f"sətir {node.line}" if node.line is not None else "sətir bilinməz"
        raise RuntimeError(f"Xəta ({line_str}): '{type(target).__name__}' obyekti atribut müraciətini dəstəkləmir")

    def evaluate_BinaryOp(self, node):
        op = node.op
        line = node.line
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"

        # Short-circuit (qısa qapanma) məntiqi operatorlar
        if op == "və":
            left = self.evaluate(node.left)
            if not self._is_truthy(left):
                return left
            return self.evaluate(node.right)

        if op in ("və ya", "ya"):
            left = self.evaluate(node.left)
            if self._is_truthy(left):
                return left
            return self.evaluate(node.right)

        left = self.evaluate(node.left)
        right = self.evaluate(node.right)

        if op == "+":
            return self._add(left, right, line)
        if op == "-":
            return self._sub(left, right, line)
        if op == "*":
            return self._mul(left, right, line)
        if op == "/":
            return self._div(left, right, line)
        if op == "%":
            return self._mod(left, right, line)
        if op == "**":
            return self._pow(left, right, line)
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right

        raise RuntimeError(f"Xəta ({line_str}): '{op}' operatoru dəstəklənmir")

    def evaluate_UnaryOp(self, node):
        operand = self.evaluate(node.operand)
        op = node.op
        line = node.line
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        if op == "-":
            if isinstance(operand, (int, float)):
                return -operand
            raise RuntimeError(f"Xəta ({line_str}): '-' unar operatoru yalnız ədədlərə tətbiq oluna bilər")
        if op == "yox":
            return not self._is_truthy(operand)
        raise RuntimeError(f"Xəta ({line_str}): '{op}' unar operatoru dəstəklənmir")

    # ----- helpers -----

    @staticmethod
    def _is_truthy(value):
        """Dərələyəz həqiqilik qaydası: boş, yalan, 0 və boş mətn yalandır."""
        if value is None or value is False:
            return False
        if value == 0 or value == "":
            return False
        return True

    def _add(self, a, b, line=None):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a + b
        if isinstance(a, str) or isinstance(b, str):
            return self._format(a) + self._format(b)
        if isinstance(a, list) and isinstance(b, list):
            return a + b
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        raise RuntimeError(
            f"Xəta ({line_str}): '{type(a).__name__}' və '{type(b).__name__}' toplana bilməz"
        )

    def _sub(self, a, b, line=None):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a - b
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        raise RuntimeError(
            f"Xəta ({line_str}): '{type(a).__name__}' dan '{type(b).__name__}' çıxıla bilməz"
        )

    def _mul(self, a, b, line=None):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a * b
        if isinstance(a, str) and isinstance(b, int):
            return a * b
        if isinstance(a, list) and isinstance(b, int):
            return a * b
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        raise RuntimeError(
            f"Xəta ({line_str}): '{type(a).__name__}' və '{type(b).__name__}' vurula bilməz"
        )

    def _div(self, a, b, line=None):
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if b == 0:
                raise RuntimeError(f"Xəta ({line_str}): sıfıra bölünmə icazəli deyil")
            return a / b
        raise RuntimeError(
            f"Xəta ({line_str}): '{type(a).__name__}' '{type(b).__name__}'ə bölünə bilməz"
        )

    def _mod(self, a, b, line=None):
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if b == 0:
                raise RuntimeError(f"Xəta ({line_str}): sıfıra bölünmə icazəli deyil")
            return a % b
        raise RuntimeError(
            f"Xəta ({line_str}): '{type(a).__name__}' '{type(b).__name__}'ə görə modulo ala bilməz"
        )

    def _pow(self, a, b, line=None):
        line_str = f"sətir {line}" if line is not None else "sətir bilinməz"
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a ** b
        raise RuntimeError(
            f"Xəta ({line_str}): '{type(a).__name__}' '{type(b).__name__}' qüvvətə yüksəldilə bilməz"
        )

    @staticmethod
    def _format(value):
        if value is None:
            return "boş"
        if isinstance(value, bool):
            return "doğru" if value else "yalan"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        if isinstance(value, list):
            items = ", ".join(Interpreter._format(x) for x in value)
            return f"[{items}]"
        if isinstance(value, dict):
            items = ", ".join(f"{Interpreter._format(k)}: {Interpreter._format(v)}" for k, v in value.items())
            return f"{{{items}}}"
        return str(value)


def execute_source(source):
    """Mənbə kodunu lexer-parser-interpreter zənciri ilə yürür."""
    from lexer import Lexer
    from parser import Parser

    tokens = Lexer(source).tokenize()
    statements = Parser(tokens).parse()
    interpreter = Interpreter()
    interpreter.run(statements)

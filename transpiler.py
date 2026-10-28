"""Dərələyəz AST-dən Python koduna transpilasiya (çevirici) modulu.

Dərələyəz (.dz) kodunu təmiz, icra oluna bilən Python koduna çevirir.
"""

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


class PythonTranspiler:
    def __init__(self):
        self.indent_level = 0

    def _indent(self):
        return "    " * self.indent_level

    def transpile(self, statements):
        """Bütün statement siyahısını Python koduna çevirir."""
        lines = [
            "# Dərələyəz transpilasiya edilmiş Python kodu",
            "import math, random",
            "",
            "# Daxili funksiyaların Python qarşılığı",
            "aralıq = lambda *a: range(*a)",
            "uzunluq = len",
            "əlavə = lambda lst, x: (lst.append(x), lst)[1]",
            "tip = type",
            "oxu = input",
            "",
        ]
        for stmt in statements:
            lines.append(self.visit_stmt(stmt))
        return "\n".join(lines)

    def visit_stmt(self, node):
        method_name = "visit_" + type(node).__name__
        method = getattr(self, method_name)
        return method(node)

    def visit_expr(self, node):
        method_name = "visit_" + type(node).__name__
        method = getattr(self, method_name)
        return method(node)

    # Statements
    def visit_PrintStmt(self, node):
        return f"{self._indent()}print({self.visit_expr(node.expr)})"

    def visit_AssignStmt(self, node):
        return f"{self._indent()}{node.name} = {self.visit_expr(node.value)}"

    def visit_SetAttrStmt(self, node):
        target = self.visit_expr(node.target)
        val = self.visit_expr(node.value)
        return f"{self._indent()}{target}.{node.attr} = {val}"

    def visit_SetItemStmt(self, node):
        target = self.visit_expr(node.target)
        index = self.visit_expr(node.index)
        val = self.visit_expr(node.value)
        return f"{self._indent()}{target}[{index}] = {val}"

    def visit_ExpressionStmt(self, node):
        return f"{self._indent()}{self.visit_expr(node.expr)}"

    def visit_IfStmt(self, node):
        cond = self.visit_expr(node.condition)
        lines = [f"{self._indent()}if {cond}:"]
        self.indent_level += 1
        for s in node.then_branch:
            lines.append(self.visit_stmt(s))
        self.indent_level -= 1

        for elif_cond, elif_branch in node.elif_branches:
            c = self.visit_expr(elif_cond)
            lines.append(f"{self._indent()}elif {c}:")
            self.indent_level += 1
            for s in elif_branch:
                lines.append(self.visit_stmt(s))
            self.indent_level -= 1

        if node.else_branch is not None:
            lines.append(f"{self._indent()}else:")
            self.indent_level += 1
            for s in node.else_branch:
                lines.append(self.visit_stmt(s))
            self.indent_level -= 1

        return "\n".join(lines)

    def visit_WhileStmt(self, node):
        cond = self.visit_expr(node.condition)
        lines = [f"{self._indent()}while {cond}:"]
        self.indent_level += 1
        for s in node.body:
            lines.append(self.visit_stmt(s))
        self.indent_level -= 1
        return "\n".join(lines)

    def visit_ForStmt(self, node):
        iterable = self.visit_expr(node.iterable)
        lines = [f"{self._indent()}for {node.var} in {iterable}:"]
        self.indent_level += 1
        for s in node.body:
            lines.append(self.visit_stmt(s))
        self.indent_level -= 1
        return "\n".join(lines)

    def visit_BreakStmt(self, node):
        return f"{self._indent()}break"

    def visit_ContinueStmt(self, node):
        return f"{self._indent()}continue"

    def visit_FunctionDef(self, node):
        # 'özü' parametrini 'self' kimi saxlamaq olar və ya 'özü' kimi saxlamaq olar (Python Unicode dəstəkləyir!)
        params = ", ".join(node.params)
        lines = [f"{self._indent()}def {node.name}({params}):"]
        self.indent_level += 1
        if not node.body:
            lines.append(f"{self._indent()}pass")
        else:
            for s in node.body:
                lines.append(self.visit_stmt(s))
        self.indent_level -= 1
        return "\n".join(lines)

    def visit_ReturnStmt(self, node):
        if node.value is None:
            return f"{self._indent()}return"
        return f"{self._indent()}return {self.visit_expr(node.value)}"

    def visit_ClassDef(self, node):
        super_str = f"({node.superclass})" if node.superclass else ""
        lines = [f"{self._indent()}class {node.name}{super_str}:"]
        self.indent_level += 1
        has_methods = False
        for s in node.body:
            if isinstance(s, FunctionDef):
                has_methods = True
                # 'yarat' metodunu '__init__' kimi çeviririk
                method_name = "__init__" if s.name == "yarat" else s.name
                params = ", ".join(s.params)
                lines.append(f"{self._indent()}def {method_name}({params}):")
                self.indent_level += 1
                for bs in s.body:
                    lines.append(self.visit_stmt(bs))
                self.indent_level -= 1
        if not has_methods:
            lines.append(f"{self._indent()}pass")
        self.indent_level -= 1
        return "\n".join(lines)

    def visit_TryStmt(self, node):
        lines = [f"{self._indent()}try:"]
        self.indent_level += 1
        for s in node.try_body:
            lines.append(self.visit_stmt(s))
        self.indent_level -= 1
        err = f" as {node.error_var}" if node.error_var else ""
        lines.append(f"{self._indent()}except Exception{err}:")
        self.indent_level += 1
        for s in node.catch_body:
            lines.append(self.visit_stmt(s))
        self.indent_level -= 1
        return "\n".join(lines)

    def visit_ThrowStmt(self, node):
        return f"{self._indent()}raise Exception({self.visit_expr(node.expr)})"

    def visit_ImportStmt(self, node):
        return f"{self._indent()}import {node.module_name}"

    # Expressions
    def visit_Number(self, node):
        return str(node.value)

    def visit_String(self, node):
        return repr(node.value)

    def visit_Boolean(self, node):
        return "True" if node.value else "False"

    def visit_NoneNode(self, node):
        return "None"

    def visit_Identifier(self, node):
        return node.name

    def visit_ListLiteral(self, node):
        elems = ", ".join(self.visit_expr(e) for e in node.elements)
        return f"[{elems}]"

    def visit_DictLiteral(self, node):
        pairs = ", ".join(f"{self.visit_expr(k)}: {self.visit_expr(v)}" for k, v in node.pairs)
        return f"{{{pairs}}}"

    def visit_IndexExpr(self, node):
        target = self.visit_expr(node.target)
        index = self.visit_expr(node.index)
        return f"{target}[{index}]"

    def visit_GetAttrExpr(self, node):
        target = self.visit_expr(node.target)
        return f"{target}.{node.attr}"

    def visit_CallExpr(self, node):
        callee = self.visit_expr(node.callee)
        args = ", ".join(self.visit_expr(a) for a in node.args)
        return f"{callee}({args})"

    def visit_UnaryOp(self, node):
        op = "not " if node.op == "yox" else node.op
        operand = self.visit_expr(node.operand)
        return f"({op}{operand})"

    def visit_BinaryOp(self, node):
        op = node.op
        if op == "və":
            op = "and"
        elif op in ("və ya", "ya"):
            op = "or"
        left = self.visit_expr(node.left)
        right = self.visit_expr(node.right)
        return f"({left} {op} {right})"


def transpile_source(source):
    from lexer import Lexer
    from parser import Parser

    tokens = Lexer(source).tokenize()
    statements = Parser(tokens).parse()
    return PythonTranspiler().transpile(statements)

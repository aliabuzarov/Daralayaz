"""Parser modulu (Marhala 2).

Lexerden gelen token akışından recursion yöntemi ilə AST qurur.
"""

from lexer import (
    Token,
    TT_NUMBER,
    TT_STRING,
    TT_IDENT,
    TT_KEYWORD,
    TT_OPERATOR,
    TT_PUNCTUATION,
    TT_NEWLINE,
    TT_INDENT,
    TT_DEDENT,
    TT_EOF,
)


# ---------- AST düğümləri ----------

class ASTNode:
    """Əməliyyat ağacının əsas düyünü."""
    def __init__(self, line=None):
        self.line = line


class Number(ASTNode):
    def __init__(self, value, line=None):
        super().__init__(line)
        self.value = value


class String(ASTNode):
    def __init__(self, value, line=None):
        super().__init__(line)
        self.value = value


class Boolean(ASTNode):
    def __init__(self, value, line=None):
        super().__init__(line)
        self.value = value


class NoneNode(ASTNode):
    def __init__(self, line=None):
        super().__init__(line)


class Identifier(ASTNode):
    def __init__(self, name, line=None):
        super().__init__(line)
        self.name = name


class BinaryOp(ASTNode):
    def __init__(self, left, op, right, line=None):
        super().__init__(line)
        self.left = left
        self.op = op
        self.right = right


class UnaryOp(ASTNode):
    def __init__(self, op, operand, line=None):
        super().__init__(line)
        self.op = op
        self.operand = operand


class PrintStmt(ASTNode):
    def __init__(self, expr, line=None):
        super().__init__(line)
        self.expr = expr


class IfStmt(ASTNode):
    def __init__(self, condition, then_branch, elif_branches, else_branch, line=None):
        super().__init__(line)
        self.condition = condition
        self.then_branch = then_branch       # statement list
        self.elif_branches = elif_branches   # list of (condition, statement list)
        self.else_branch = else_branch       # statement list or None


class WhileStmt(ASTNode):
    def __init__(self, condition, body, line=None):
        super().__init__(line)
        self.condition = condition
        self.body = body                     # statement list


class ForStmt(ASTNode):
    def __init__(self, var, iterable, body, line=None):
        super().__init__(line)
        self.var = var                       # identifier name
        self.iterable = iterable             # expression (list or aralıq call)
        self.body = body                     # statement list


class BreakStmt(ASTNode):
    def __init__(self, line=None):
        super().__init__(line)


class ContinueStmt(ASTNode):
    def __init__(self, line=None):
        super().__init__(line)


class CallExpr(ASTNode):
    def __init__(self, callee, args, line=None):
        super().__init__(line)
        self.callee = callee
        self.args = args

    @property
    def name(self):
        if isinstance(self.callee, Identifier):
            return self.callee.name
        return str(self.callee)


class IndexExpr(ASTNode):
    def __init__(self, target, index, line=None):
        super().__init__(line)
        self.target = target
        self.index = index


class GetAttrExpr(ASTNode):
    def __init__(self, target, attr, line=None):
        super().__init__(line)
        self.target = target
        self.attr = attr


class SetAttrStmt(ASTNode):
    def __init__(self, target, attr, value, line=None):
        super().__init__(line)
        self.target = target
        self.attr = attr
        self.value = value


class SetItemStmt(ASTNode):
    def __init__(self, target, index, value, line=None):
        super().__init__(line)
        self.target = target
        self.index = index
        self.value = value


class ListLiteral(ASTNode):
    def __init__(self, elements, line=None):
        super().__init__(line)
        self.elements = elements


class DictLiteral(ASTNode):
    def __init__(self, pairs, line=None):
        super().__init__(line)
        self.pairs = pairs


class AssignStmt(ASTNode):
    def __init__(self, name, value, is_constant=False, line=None):
        super().__init__(line)
        self.name = name
        self.value = value
        self.is_constant = is_constant


class ExpressionStmt(ASTNode):
    def __init__(self, expr, line=None):
        super().__init__(line)
        self.expr = expr


class FunctionDef(ASTNode):
    def __init__(self, name, params, body, line=None):
        super().__init__(line)
        self.name = name
        self.params = params
        self.body = body


class ReturnStmt(ASTNode):
    def __init__(self, value, line=None):
        super().__init__(line)
        self.value = value


class ClassDef(ASTNode):
    def __init__(self, name, superclass, body, line=None):
        super().__init__(line)
        self.name = name
        self.superclass = superclass
        self.body = body


class TryStmt(ASTNode):
    def __init__(self, try_body, error_var, catch_body, line=None):
        super().__init__(line)
        self.try_body = try_body
        self.error_var = error_var
        self.catch_body = catch_body


class ThrowStmt(ASTNode):
    def __init__(self, expr, line=None):
        super().__init__(line)
        self.expr = expr


class ImportStmt(ASTNode):
    def __init__(self, module_name, line=None):
        super().__init__(line)
        self.module_name = module_name


# ---------- Xəta ----------

class ParseError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Xəta (sətir {line}): {message}")


# ---------- Parser ----------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, types, values=None):
        """Verilmiş tipi ( və istənilmişdir də dəyəri ) olan tokeni tələb edir və keçir."""
        tok = self.peek()
        if tok.type not in types:
            raise ParseError(
                f"'{types}' gözlənirdi, '{tok.type}' tapıldı",
                tok.line,
                tok.column,
            )
        if values is not None and tok.value not in values:
            raise ParseError(
                f"{values} içində '{tok.value}' gözlənirdi",
                tok.line,
                tok.column,
            )
        self.advance()
        return tok

    def match(self, types, values=None):
        """Əgər cari token uyğunlaşarsa onu keçir və qaytarır, əks halda None."""
        tok = self.peek()
        if tok.type in types and (values is None or tok.value in values):
            self.advance()
            return tok
        return None

    # ----- giriş -----

    def parse(self):
        """Bütün proqramı ayır: statement siyahısı qaytarır."""
        statements = []
        while self.pos < len(self.tokens) and self.peek().type != TT_EOF:
            stmt = self.parse_statement()
            statements.append(stmt)
            if not isinstance(stmt, (IfStmt, WhileStmt, ForStmt, FunctionDef, ClassDef, TryStmt)):
                self.expect({TT_NEWLINE, TT_EOF})
            while self.pos < len(self.tokens) and self.peek().type == TT_NEWLINE:
                self.advance()
        return statements

    def parse_statement(self):
        """Bir statement-ı ayır: yaz əmri, təyin, dövr, funksiya, sinif və ya expression."""
        tok = self.peek()

        # yaz <ifadə>
        if tok.type == TT_KEYWORD and tok.value == "yaz":
            yaz_tok = self.advance()
            expr = self.parse_expression()
            return PrintStmt(expr, line=yaz_tok.line)

        # sabit <ad> = <ifadə> (dəyişən təyini, sabit)
        if tok.type == TT_KEYWORD and tok.value == "sabit":
            sabit_tok = self.advance()
            name_tok = self.expect({TT_IDENT})
            self.expect({TT_OPERATOR}, {"="})
            value = self.parse_expression()
            return AssignStmt(name_tok.value, value, is_constant=True, line=sabit_tok.line)

        # əgər <ifadə>: ... (yoxsa əgər ...)* (əks halda: ...)?
        if tok.type == TT_KEYWORD and tok.value == "əgər":
            return self.parse_if()

        # nə qədər ki <ifadə>:
        if tok.type == TT_KEYWORD and tok.value == "nə":
            return self.parse_while()

        # hər <ad> içində <ifadə>:
        if tok.type == TT_KEYWORD and tok.value == "hər":
            return self.parse_for()

        # dayan
        if tok.type == TT_KEYWORD and tok.value == "dayan":
            self.advance()
            return BreakStmt(line=tok.line)

        # davam
        if tok.type == TT_KEYWORD and tok.value == "davam":
            self.advance()
            return ContinueStmt(line=tok.line)

        # funksiya <ad>(<params>):
        if tok.type == TT_KEYWORD and tok.value == "funksiya":
            return self.parse_function_def()

        # qaytar <ifadə>?
        if tok.type == TT_KEYWORD and tok.value == "qaytar":
            return self.parse_return()

        # sinif <ad> (miras <baza>)?:
        if tok.type == TT_KEYWORD and tok.value == "sinif":
            return self.parse_class_def()

        # yoxla: ... tut <xəta>?: ...
        if tok.type == TT_KEYWORD and tok.value == "yoxla":
            return self.parse_try()

        # at <ifadə>
        if tok.type == TT_KEYWORD and tok.value == "at":
            return self.parse_throw()

        # idxal <modul>
        if tok.type == TT_KEYWORD and tok.value == "idxal":
            return self.parse_import()

        # İfadə və ya mənimsətmə: target = value
        expr = self.parse_expression()
        if self.match({TT_OPERATOR}, {"="}):
            value = self.parse_expression()
            if isinstance(expr, Identifier):
                return AssignStmt(expr.name, value, line=expr.line)
            if isinstance(expr, GetAttrExpr):
                return SetAttrStmt(expr.target, expr.attr, value, line=expr.line)
            if isinstance(expr, IndexExpr):
                return SetItemStmt(expr.target, expr.index, value, line=expr.line)
            raise ParseError("Yalnız dəyişən, atribut və ya indeksə mənimsətmə edilə bilər", tok.line, tok.column)

        return ExpressionStmt(expr, line=expr.line)

    def parse_while(self):
        """nə qədər ki <şərt>: blokunu ayırır."""
        ne_tok = self.expect({TT_KEYWORD}, {"nə"})
        self.expect({TT_KEYWORD}, {"qədər"})
        self.expect({TT_KEYWORD}, {"ki"})
        condition = self.parse_expression()
        self.expect({TT_PUNCTUATION}, {":"})
        self.expect({TT_NEWLINE})
        body = self.parse_block()
        return WhileStmt(condition, body, line=ne_tok.line)

    def parse_for(self):
        """hər <ad> içində <ifadə>: blokunu ayırır."""
        her_tok = self.expect({TT_KEYWORD}, {"hər"})
        var_tok = self.expect({TT_IDENT})
        self.expect({TT_KEYWORD}, {"içində"})
        iterable = self.parse_expression()
        self.expect({TT_PUNCTUATION}, {":"})
        self.expect({TT_NEWLINE})
        body = self.parse_block()
        return ForStmt(var_tok.value, iterable, body, line=her_tok.line)

    def parse_function_def(self):
        """funksiya <ad>(param1, param2): blokunu ayırır."""
        fn_tok = self.expect({TT_KEYWORD}, {"funksiya"})
        name_tok = self.advance()
        if name_tok.type not in (TT_IDENT, TT_KEYWORD):
            raise ParseError("Funksiya adı gözlənirdi", name_tok.line, name_tok.column)
        self.expect({TT_PUNCTUATION}, {"("})
        params = []
        if not (self.peek().type == TT_PUNCTUATION and self.peek().value == ")"):
            p_tok = self.advance()
            params.append(p_tok.value)
            while self.peek().type == TT_PUNCTUATION and self.peek().value == ",":
                self.advance()
                if self.peek().type == TT_PUNCTUATION and self.peek().value == ")":
                    break
                p_tok = self.advance()
                params.append(p_tok.value)
        self.expect({TT_PUNCTUATION}, {")"})
        self.expect({TT_PUNCTUATION}, {":"})
        self.expect({TT_NEWLINE})
        body = self.parse_block()
        return FunctionDef(name_tok.value, params, body, line=fn_tok.line)

    def parse_return(self):
        """qaytar <ifadə>? əmrini ayırır."""
        ret_tok = self.expect({TT_KEYWORD}, {"qaytar"})
        if self.peek().type in (TT_NEWLINE, TT_DEDENT, TT_EOF):
            return ReturnStmt(None, line=ret_tok.line)
        value = self.parse_expression()
        return ReturnStmt(value, line=ret_tok.line)

    def parse_class_def(self):
        """sinif <ad> (miras <baza>)?: blokunu ayırır."""
        sinif_tok = self.expect({TT_KEYWORD}, {"sinif"})
        name_tok = self.expect({TT_IDENT})
        superclass = None
        if self.peek().type == TT_KEYWORD and self.peek().value == "miras":
            self.advance()
            super_tok = self.expect({TT_IDENT})
            superclass = super_tok.value
        self.expect({TT_PUNCTUATION}, {":"})
        self.expect({TT_NEWLINE})
        body = self.parse_block()
        return ClassDef(name_tok.value, superclass, body, line=sinif_tok.line)

    def parse_try(self):
        """yoxla: ... tut <xəta>?: ... blokunu ayırır."""
        yoxla_tok = self.expect({TT_KEYWORD}, {"yoxla"})
        self.expect({TT_PUNCTUATION}, {":"})
        self.expect({TT_NEWLINE})
        try_body = self.parse_block()
        self.expect({TT_KEYWORD}, {"tut"})
        error_var = None
        if self.peek().type in (TT_IDENT, TT_KEYWORD) and self.peek().value != ":":
            error_var = self.advance().value
        self.expect({TT_PUNCTUATION}, {":"})
        self.expect({TT_NEWLINE})
        catch_body = self.parse_block()
        return TryStmt(try_body, error_var, catch_body, line=yoxla_tok.line)

    def parse_throw(self):
        """at <ifadə> əmrini ayırır."""
        at_tok = self.expect({TT_KEYWORD}, {"at"})
        expr = self.parse_expression()
        return ThrowStmt(expr, line=at_tok.line)

    def parse_import(self):
        """idxal <modul_adı> əmrini ayırır."""
        idxal_tok = self.expect({TT_KEYWORD}, {"idxal"})
        mod_tok = self.expect({TT_STRING})
        return ImportStmt(mod_tok.value, line=idxal_tok.line)

    def parse_if(self):
        """əgər / yoxsa əgər / əks halda blokunu ayırır."""
        eger_tok = self.expect({TT_KEYWORD}, {"əgər"})
        condition = self.parse_expression()
        self.expect({TT_PUNCTUATION}, {":"})
        self.expect({TT_NEWLINE})
        then_branch = self.parse_block()

        elif_branches = []
        while self.peek().type == TT_KEYWORD and self.peek().value == "yoxsa":
            self.advance()
            # "yoxsa" sonra "əgər" ola bilər və ya birbaşa "yoxsa" (qısaldılmış elif)
            if self.peek().type == TT_KEYWORD and self.peek().value == "əgər":
                self.advance()
            elif_condition = self.parse_expression()
            self.expect({TT_PUNCTUATION}, {":"})
            self.expect({TT_NEWLINE})
            elif_branch = self.parse_block()
            elif_branches.append((elif_condition, elif_branch))

        else_branch = None
        if self.peek().type == TT_KEYWORD and self.peek().value == "əks":
            self.advance()  # "əks"
            self.expect({TT_KEYWORD}, {"halda"})
            self.expect({TT_PUNCTUATION}, {":"})
            self.expect({TT_NEWLINE})
            else_branch = self.parse_block()

        return IfStmt(condition, then_branch, elif_branches, else_branch, line=eger_tok.line)

    def parse_block(self):
        """INDENT ... DEDENT arasında statement-ləri ayırır."""
        self.expect({TT_INDENT})
        statements = []
        while self.peek().type != TT_DEDENT:
            stmt = self.parse_statement()
            statements.append(stmt)
            if not isinstance(stmt, (IfStmt, WhileStmt, ForStmt, FunctionDef, ClassDef, TryStmt)):
                self.expect({TT_NEWLINE, TT_EOF})
            while self.pos < len(self.tokens) and self.peek().type == TT_NEWLINE:
                self.advance()
        self.advance()  # DEDENT
        return statements

    # ----- ifadələr (üstünlülük səviyyələri) -----

    def parse_expression(self):
        """Ən aşağı üstünlülük: məntiqi 'və ya' / 'ya'."""
        return self.parse_or()

    def parse_or(self):
        node = self.parse_and()
        while True:
            tok = self.peek()
            # "və ya" — iki simvoldan ibarət OR operatoru
            if (tok.type == TT_KEYWORD and tok.value == "və"
                    and self.pos + 1 < len(self.tokens)
                    and self.tokens[self.pos + 1].type == TT_KEYWORD
                    and self.tokens[self.pos + 1].value == "ya"):
                op_tok = self.advance()  # "və"
                self.advance()  # "ya"
                right = self.parse_and()
                node = BinaryOp(node, "və ya", right, line=op_tok.line)
            elif tok.type == TT_KEYWORD and tok.value == "ya":
                op_tok = self.advance()
                right = self.parse_and()
                node = BinaryOp(node, "ya", right, line=op_tok.line)
            else:
                break
        return node

    def parse_and(self):
        node = self.parse_comparison()
        while True:
            tok = self.peek()
            # Ətərafda "ya" olmayan "və" — AND operatoru ("və ya" OR-ə aid)
            if (tok.type == TT_KEYWORD and tok.value == "və"
                    and not (self.pos + 1 < len(self.tokens)
                             and self.tokens[self.pos + 1].type == TT_KEYWORD
                             and self.tokens[self.pos + 1].value == "ya")):
                op_tok = self.advance()
                right = self.parse_comparison()
                node = BinaryOp(node, "və", right, line=op_tok.line)
            else:
                break
        return node

    def parse_comparison(self):
        node = self.parse_additive()
        while self.match(
            {TT_OPERATOR}, {"==", "!=", "<", ">", "<=", ">="}
        ):
            op_tok = self.tokens[self.pos - 1]
            op = op_tok.value
            right = self.parse_additive()
            node = BinaryOp(node, op, right, line=op_tok.line)
        return node

    def parse_additive(self):
        node = self.parse_multiplicative()
        while self.match({TT_OPERATOR}, {"+", "-"}):
            op_tok = self.tokens[self.pos - 1]
            op = op_tok.value
            right = self.parse_multiplicative()
            node = BinaryOp(node, op, right, line=op_tok.line)
        return node

    def parse_multiplicative(self):
        node = self.parse_power()
        while self.match({TT_OPERATOR}, {"*", "/", "%"}):
            op_tok = self.tokens[self.pos - 1]
            op = op_tok.value
            right = self.parse_power()
            node = BinaryOp(node, op, right, line=op_tok.line)
        return node

    def parse_power(self):
        """'**' sağdan sola işlənir (sağ-assosiatif)."""
        base = self.parse_unary()
        if self.match({TT_OPERATOR}, {"**"}):
            op_tok = self.tokens[self.pos - 1]
            exponent = self.parse_power()
            return BinaryOp(base, "**", exponent, line=op_tok.line)
        return base

    def parse_unary(self):
        """'yox' və '-' unar operatorları."""
        tok = self.peek()
        if tok.type == TT_KEYWORD and tok.value == "yox":
            op_tok = self.advance()
            operand = self.parse_unary()
            return UnaryOp("yox", operand, line=op_tok.line)
        if tok.type == TT_OPERATOR and tok.value == "-":
            op_tok = self.advance()
            operand = self.parse_unary()
            return UnaryOp("-", operand, line=op_tok.line)
        return self.parse_postfix()

    def parse_postfix(self):
        """Funksiya çağırışı (), indeks [] və atribut . əməliyyatları."""
        node = self.parse_primary()
        while True:
            tok = self.peek()
            # Funksiya çağırışı: callee(...)
            if tok.type == TT_PUNCTUATION and tok.value == "(":
                lparen = self.advance()
                args = []
                if not (self.peek().type == TT_PUNCTUATION and self.peek().value == ")"):
                    args.append(self.parse_expression())
                    while self.peek().type == TT_PUNCTUATION and self.peek().value == ",":
                        self.advance()
                        if self.peek().type == TT_PUNCTUATION and self.peek().value == ")":
                            break
                        args.append(self.parse_expression())
                self.expect({TT_PUNCTUATION}, {")"})
                node = CallExpr(node, args, line=lparen.line)

            # İndekslə müraciət: target[...]
            elif tok.type == TT_PUNCTUATION and tok.value == "[":
                lbrack = self.advance()
                index = self.parse_expression()
                self.expect({TT_PUNCTUATION}, {"]"})
                node = IndexExpr(node, index, line=lbrack.line)

            # Atribut / metod müraciəti: target.attr
            elif tok.type == TT_PUNCTUATION and tok.value == ".":
                dot = self.advance()
                attr_tok = self.expect({TT_IDENT})
                node = GetAttrExpr(node, attr_tok.value, line=dot.line)

            else:
                break
        return node

    def parse_primary(self):
        """Əsas ifadə: rəqəm, mətn, bool, identifikator, siyahı, lüğət və ya '( ... )'."""
        tok = self.peek()

        if tok.type == TT_NUMBER:
            num_tok = self.advance()
            return Number(self._to_number(num_tok.value), line=num_tok.line)

        if tok.type == TT_STRING:
            str_tok = self.advance()
            return String(str_tok.value, line=str_tok.line)

        if tok.type == TT_KEYWORD:
            if tok.value == "doğru":
                kw_tok = self.advance()
                return Boolean(True, line=kw_tok.line)
            if tok.value == "yalan":
                kw_tok = self.advance()
                return Boolean(False, line=kw_tok.line)
            if tok.value == "boş":
                kw_tok = self.advance()
                return NoneNode(line=kw_tok.line)
            # Daxili funksiyalar və 'özü' ifadədə identifikator kimi işlənə bilər
            if tok.value in ("aralıq", "uzunluq", "əlavə", "tip", "oxu", "özü"):
                kw_tok = self.advance()
                return Identifier(kw_tok.value, line=kw_tok.line)

        if tok.type == TT_IDENT:
            id_tok = self.advance()
            return Identifier(id_tok.value, line=id_tok.line)

        # Mötərizəli ifadə: ( ... )
        if tok.type == TT_PUNCTUATION and tok.value == "(":
            self.advance()
            expr = self.parse_expression()
            self.expect({TT_PUNCTUATION}, {")"})
            return expr

        # Siyahı literalı: [1, 2, 3]
        if tok.type == TT_PUNCTUATION and tok.value == "[":
            lbrack = self.advance()
            elements = []
            if not (self.peek().type == TT_PUNCTUATION and self.peek().value == "]"):
                elements.append(self.parse_expression())
                while self.peek().type == TT_PUNCTUATION and self.peek().value == ",":
                    self.advance()
                    if self.peek().type == TT_PUNCTUATION and self.peek().value == "]":
                        break
                    elements.append(self.parse_expression())
            self.expect({TT_PUNCTUATION}, {"]"})
            return ListLiteral(elements, line=lbrack.line)

        # Lüğət literalı: {"ad": "Aytən"}
        if tok.type == TT_PUNCTUATION and tok.value == "{":
            lbrace = self.advance()
            pairs = []
            if not (self.peek().type == TT_PUNCTUATION and self.peek().value == "}"):
                k = self.parse_expression()
                self.expect({TT_PUNCTUATION}, {":"})
                v = self.parse_expression()
                pairs.append((k, v))
                while self.peek().type == TT_PUNCTUATION and self.peek().value == ",":
                    self.advance()
                    if self.peek().type == TT_PUNCTUATION and self.peek().value == "}":
                        break
                    k = self.parse_expression()
                    self.expect({TT_PUNCTUATION}, {":"})
                    v = self.parse_expression()
                    pairs.append((k, v))
            self.expect({TT_PUNCTUATION}, {"}"})
            return DictLiteral(pairs, line=lbrace.line)

        raise ParseError(
            f"Təxminən ifadə gözlənirdi, '{tok.type}' tapıldı",
            tok.line,
            tok.column,
        )

    @staticmethod
    def _to_number(text):
        if "." in text:
            return float(text)
        return int(text)

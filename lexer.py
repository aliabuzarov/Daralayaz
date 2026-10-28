"""Lexer modulu (Marhala 1).

Dərələyəz mənbə kodunu tokenlərə ayirir.
Unicode identifier-ləri, INDENT/DEDENT blokunu və sətir nömrəsini saxlayır.
"""

from collections import namedtuple

# Token tipleri
TT_NUMBER = "RƏQƏM"
TT_STRING = "MƏTN"
TT_IDENT = "IDENTİFİKATOR"
TT_KEYWORD = "ACAR_SÖZ"
TT_OPERATOR = "OPERATOR"
TT_PUNCTUATION = "NOKTALAMA"
TT_NEWLINE = "YENİ_SƏTR"
TT_INDENT = "GIRIŞ"
TT_DEDENT = "ÇIXIŞ"
TT_EOF = "SON"

Token = namedtuple("Token", ["type", "value", "line", "column"])

# Dilin açar sözləri, tipləri və daxili funksiya adları
KEYWORDS = frozenset({
    # Çıxış / giriş
    "yaz", "oxu",
    # Tiplər
    "ədəd", "mətn", "məntiq", "boş", "siyahı", "lüğət",
    # Şərti bloklar
    "əgər", "yoxsa", "əks", "halda",
    # Sabitlər
    "sabit",
    # Dövrlər
    "nə", "qədər", "ki", "hər", "içində",
    "dayan", "davam",
    # Funksiyalar
    "funksiya", "qaytar",
    # Siniflər
    "sinif", "miras", "özü", "yarat",
    # Xəta idarəsi
    "yoxla", "tut", "xəbərdarlık", "at",
    # Modullar
    "idxal",
    # Məntiqi / sabitlər
    "doğru", "yalan", "boş",
    "və", "ya", "yox",
    # Daxili funksiyalar
    "uzunluq", "əlavə", "aralıq", "tip",
})

# Sabitlər
CONSTANTS = frozenset({"PI"})

# Çox-simvollu operatorlar (öncə onlara baxılır)
MULTI_CHAR_OPERATORS = frozenset({"**", "==", "!=", "<=", ">="})
# Tek-simvollu operatorlar
SINGLE_CHAR_OPERATORS = frozenset({"+", "-", "*", "/", "%", "<", ">", "="})

# Noktalama işarələri
PUNCTUATION = frozenset({":", "(", ")", "[", "]", "{", "}", ",", "."})


class LexerError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Xəta (sətir {line}): {message}")


def _is_id_start(ch):
    return ch.isalpha() or ch == "_"


def _is_id_char(ch):
    return ch.isalnum() or ch == "_"


class Lexer:
    def __init__(self, source):
        self.source = source
        self.tokens = []

    def tokenize(self):
        """Mənbə kodundan token siyahısı qaytarır."""
        lines = self.source.split("\n")

        # Hər sətiri ayır: (indent_sehvi, [(type, value, line, col)], sətir_nömrə)
        line_tokens = []
        for i, raw_line in enumerate(lines):
            line_no = i + 1
            expanded = raw_line.expandtabs(4)
            stripped = expanded.lstrip(" ")
            indent = len(expanded) - len(stripped)

            # Boş və yalnız-şərh sətirlərini atırıq
            if stripped == "" or stripped.lstrip().startswith("#"):
                continue

            code = self._strip_comment(stripped)
            toks = self._tokenize_line(code, line_no)
            line_tokens.append((indent, toks, line_no))

        # INDENT/DEDENT və YENİ_SƏTR daxil edərək nəticəni qurur
        result = []
        indent_stack = [0]

        for indent, toks, line_no in line_tokens:
            while indent < indent_stack[-1]:
                indent_stack.pop()
                result.append(Token(TT_DEDENT, None, line_no, 1))
            if indent > indent_stack[-1]:
                indent_stack.append(indent)
                result.append(Token(TT_INDENT, None, line_no, 1))
            result.extend(toks)
            result.append(Token(TT_NEWLINE, None, line_no, 1))

        # Qalıqlı giriş bloklarını bağlar
        last_line = line_tokens[-1][2] if line_tokens else 1
        while len(indent_stack) > 1:
            indent_stack.pop()
            result.append(Token(TT_DEDENT, None, last_line, 1))

        result.append(Token(TT_EOF, None, last_line, 1))
        self.tokens = result
        return result

    def _strip_comment(self, line):
        """Sətirdən # ilə başlayan şərhünü çıxarır (mətin literali içindəki # istisna)."""
        in_str = False
        str_char = ""
        out = []
        i = 0
        while i < len(line):
            ch = line[i]
            if in_str:
                out.append(ch)
                if ch == "\\" and i + 1 < len(line):
                    out.append(line[i + 1])
                    i += 2
                    continue
                if ch == str_char:
                    in_str = False
                i += 1
                continue
            if ch == '"' or ch == "'":
                in_str = True
                str_char = ch
                out.append(ch)
                i += 1
                continue
            if ch == "#":
                break
            out.append(ch)
            i += 1
        return "".join(out)

    def _tokenize_line(self, code, line_no):
        """Bir sətirik kodu tokenlərə çevirir."""
        toks = []
        i = 0
        n = len(code)
        col = 1
        while i < n:
            ch = code[i]

            if ch in " \t":
                col += 1
                i += 1
                continue

            # Rəqəm (tam və onluq kəsr)
            if ch.isdigit():
                start_col = col
                num = ""
                while i < n and (code[i].isdigit() or code[i] == "."):
                    num += code[i]
                    col += 1
                    i += 1
                toks.append(Token(TT_NUMBER, num, line_no, start_col))
                continue

            # Mətin literalı ("...' və '...')
            if ch == '"' or ch == "'":
                start_col = col
                quote = ch
                i += 1
                col += 1
                s = ""
                while i < n and code[i] != quote:
                    if code[i] == "\\" and i + 1 < n:
                        nxt = code[i + 1]
                        if nxt == "n":
                            s += "\n"
                        elif nxt == "t":
                            s += "\t"
                        elif nxt in ('"', "'", "\\"):
                            s += nxt
                        else:
                            s += nxt
                        i += 2
                        col += 2
                        continue
                    s += code[i]
                    col += 1
                    i += 1
                if i >= n:
                    raise LexerError("Açılmamış mətn literali", line_no, start_col)
                i += 1  # bağlanış tırnaq
                col += 1
                toks.append(Token(TT_STRING, s, line_no, start_col))
                continue

            # İki simvollu operator
            if i + 1 < n and code[i:i + 2] in MULTI_CHAR_OPERATORS:
                toks.append(Token(TT_OPERATOR, code[i:i + 2], line_no, col))
                col += 2
                i += 2
                continue

            # Tek simvollu operator
            if ch in SINGLE_CHAR_OPERATORS:
                toks.append(Token(TT_OPERATOR, ch, line_no, col))
                col += 1
                i += 1
                continue

            # Noktalama
            if ch in PUNCTUATION:
                toks.append(Token(TT_PUNCTUATION, ch, line_no, col))
                col += 1
                i += 1
                continue

            # Identifikator / açar söz
            if _is_id_start(ch):
                start_col = col
                word = ""
                while i < n and _is_id_char(code[i]):
                    word += code[i]
                    col += 1
                    i += 1
                if word in KEYWORDS:
                    toks.append(Token(TT_KEYWORD, word, line_no, start_col))
                else:
                    toks.append(Token(TT_IDENT, word, line_no, start_col))
                continue

            raise LexerError(f"Tanınmayan simvol: '{ch}'", line_no, col)

        return toks

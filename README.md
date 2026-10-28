# Dərələyəz (.dz)

Azərbaycan dilində açar sözləri olan, öyrənmək və əylənmək məqsədilə Python 3 standart kitabxanası ilə hazırlanmış dinamik interpretator proqramlaşdırma dili.

---

## 🌟 Əsas Xüsusiyyətlər

- **Yalnız Standart Kitabxana:** Heç bir kənar asılılıq yoxdur (`pip` tələb olunmur).
- **Klassik Mühəndislik:** Lexer → Recursive Descent Parser → AST → Tree-walk Interpreter.
- **Azərbaycan Əlifbası Dəstəyi:** İdentifikatorlarda `ə`, `ı`, `ö`, `ü`, `ş`, `ç`, `ğ` tam dəstəklənir.
- **Dəqiq Azərbaycan Dilində Xətalar:** Xəta baş verdikdə sətir nömrəsi ilə ana dilimizdə izahat verilir (məsələn, `Xəta (sətir 3): 'say' dəyişəni tapılmadı`).
- **Python İndentation:** 4 boşluq girinti və `:` bloku.
- **Zəngin İmkanlar:** Dəyişənlər və sabitlər, şərtlər, dövrlər, closures, rekursiya, siniflər və miras, xəta idarəsi (`yoxla/tut/at`), modullar (`idxal`).
- **Bonuslar:** 
  - İnteraktiv REPL rejimi (`./dərələyəz`).
  - Python koduna tərcümə (Transpiler rejimi: `python main.py --python fayl.dz`).
  - Müasir Brauzer Playground (`playground.html`).

---

## 📂 Qovluq Quruluşu

- `lexer.py` — Mərhələ 1: Tokenlər, Unicode hərflər, INDENT/DEDENT, sətir nömrələri.
- `parser.py` — Mərhələ 2: Rekursiv eniş parseri, operator üstünlüyü, AST düyünləri.
- `interpreter.py` — Mərhələ 3–10: Mühit (Environment), icra, dövrlər, funksiyalar, siniflər, daxili kitabxana.
- `transpiler.py` — Bonus: Dərələyəz kodunu birbaşa Python koduna çevirən transpilator.
- `main.py` — CLI giriş nöqtəsi və REPL.
- `dərələyəz` — Birbaşa icra olunan skript (`./dərələyəz fayl.dz`).
- `playground.html` — Pyodide (WebAssembly) ilə işləyən onlayn brauzer meydançası.
- `nümunələr/` — 7 ədəd nümayiş proqramı (`.dz`).
- `testler/` — 79 ədəd avtomatik vahid test (`unittest`).

---

## 🚀 İstifadə Qaydası

### 1. Fayl İcra Etmək
```bash
./dərələyəz nümunələr/heyvan.dz
# və ya
python3 main.py nümunələr/faktorial.dz
```

### 2. İnteraktiv REPL
```bash
./dərələyəz
```
```
Dərələyəz 1.0 (İnteraktiv Rejim / REPL)
Kodu daxil edin (çıxmaq üçün 'çıx', 'exit' və ya Ctrl+D):
>>> ad = "Dünya"
>>> yaz "Salam, " + ad
Salam, Dünya
```

### 3. Python Koduna Çevirmək (Transpiler)
```bash
python3 main.py --python nümunələr/heyvan.dz
```

### 4. Testləri İcra Etmək
```bash
python3 -m unittest discover -s testler
```

---

## 📖 Dilin Spesifikasiyası və Nümunə

```python
sinif Heyvan:
    funksiya yarat(özü, ad):
        özü.ad = ad

    funksiya danış(özü):
        yaz özü.ad + " səs çıxarır"

sinif Pişik miras Heyvan:
    funksiya danış(özü):
        yaz özü.ad + " miyoldayır"

p = Pişik("Mırmır")
p.danış()

hər i içində aralıq(1, 4):
    əgər i % 2 == 0:
        yaz i + " cütdür"
    əks halda:
        yaz i + " təkdir"
```

### Açar Sözlər
- **Giriş / Çıxış:** `yaz`, `oxu`
- **Dəyişənlər və Sabitlər:** `ad = dəyər`, `sabit PI = 3.14`
- **Tiplər:** `ədəd`, `mətn`, `məntiq` (`doğru` / `yalan`), `boş`, `siyahı` (`[1, 2]`), `lüğət` (`{"a": 1}`)
- **Operatorlar:** `+`, `-`, `*`, `/`, `%`, `**`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `və`, `və ya`, `yox`
- **Şərtlər:** `əgər`, `yoxsa əgər`, `yoxsa`, `əks halda`
- **Dövrlər:** `nə qədər ki`, `hər ... içində`, `dayan`, `davam`
- **Funksiyalar:** `funksiya ad(param): ... qaytar dəyər`
- **Siniflər:** `sinif`, `yarat`, `özü`, `miras`
- **Xəta İdarəsi:** `yoxla: ... tut e: ...`, `at "xəta"`
- **Modullar:** `idxal "riyaziyyat"`, `idxal "təsadüfi"`, `idxal "fayl"`
- **Daxili Funksiyalar:** `aralıq(a, b)`, `uzunluq(x)`, `əlavə(s, x)`, `tip(x)`, `oxu("...")`

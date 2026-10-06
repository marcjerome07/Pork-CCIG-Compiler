# Pork CCig Compiler

A browser-based compiler for **Pork CCig**, a cooking-themed, C-like programming language inspired by Filipino sisig.
![Uploading image.png…]()


- **Frontend:** React + Vite
- **Compiler logic:** Python

---

## Quick Start

### 1. Install the requirements

| Tool | Version | Download |
|---|---|---|
| Node.js | 18 or later | https://nodejs.org |
| Python | 3.10 or later | https://www.python.org |

Python uses only the standard library, so there is nothing to `pip install`.

### 2. Get the project

```bash
git clone https://github.com/marcjerome07/Pork-CCIG-Compiler.git
cd Pork-CCIG-Compiler
npm install
```

### 3. Run it (two terminals)

**Terminal 1: start the Python lexer server**

```bash
npm run lexer
```

On macOS or Linux, use `python3 backend/server.py` instead.

**Terminal 2: start the web app**

```bash
npm run dev
```

### 4. Open the app

Go to **http://localhost:5173**, paste some Pork CCig code into the editor, and click **Run**.

Keep both terminals open while you use the app. Press `Ctrl + C` in each terminal to stop.

---

## Try It

Paste this into the editor and click **Run**:

```c
// Global Declaration
meat total = 0;

// Sub-Program
meat add (meat a, meat b) {
    serveback a + b;
}

// Main Program
empty pork() {
    total = add (5, 10);
    serve("Total: &d", total);
}
```

The **Tokens** table lists every token with its type, lexeme, line, and column. The **Console** shows a summary and any lexical errors.

To see an error, try:

```c
meat price = 5 $ 2;
```

---

## Features

- Code editor with line numbers
- Zoom like VS Code: `+` / `-` / Reset buttons, `Ctrl + mouse wheel`, or `Ctrl + +` / `Ctrl + -` / `Ctrl + 0`
- Light and dark mode, remembered between visits
- Token table: **Token Type | Lexeme | Line | Col**
- Console with error line and column numbers
- Collapsible **Keywords** panel with all 24 reserved words

## Project Status

| Phase | Status |
|---|---|
| Lexical analysis | Done |
| Syntax analysis (parser) | Not started |
| Semantic analysis | Not started |

---

## What the Lexer Recognizes

| Category | Token type | Examples |
|---|---|---|
| Reserved words | the word itself | `meat`, `if`, `pork`, `serve` |
| Identifiers | `id` | `age`, `student_name`, `_count` |
| Whole numbers | `meat_lit` | `21`, `-15` (max 15 digits) |
| Decimals | `sauce_lit` | `150.50` (max 12 whole, 7 decimal digits) |
| Characters | `chop_lit` | `'A'`, `'\n'` |
| Strings | `recipe_lit` | `"Sisig"` |
| Symbols | the symbol itself | `=`, `==`, `+=`, `&&`, `;`, `{` |
| Comments | `Single-Line Comment`, `Multi-Line Comment` | `// note`, `/* note */` |
| Whitespace | `space`, `newline`, `tab` | |

### Reserved words (24)

| Group | Words |
|---|---|
| Data types | `meat` `sauce` `chop` `recipe` `cooked` `empty` `menu` |
| Conditional | `if` `else` `switch` `case` `default` |
| Iterative | `for` `while` `do` |
| Jump | `stop` `again` `serveback` |
| Others | `pork` `serve` `taste` `yummy` `yuck` `fixed` |

### Lexical errors detected

- Invalid characters, such as `$`, `@`, `#` or a single `|`
- A token followed by a character its delimiter set does not allow
- Numbers that are too long or malformed, such as `1.2.3` or `12.`
- Identifiers longer than 20 characters or starting with a digit
- Empty or space-only `chop` literals, and invalid escapes like `\o`
- Unterminated strings, characters, or `/* */` comments

---

## Running the Tests

```bash
npm run test:lexer
```

---

## Project Structure

```
Pork-CCIG-Compiler/
├── backend/
│   ├── pork_lexer.py     # Lexer: keywords, delimiters, literal rules
│   ├── server.py         # Local server for the web app
│   └── test_lexer.py     # Lexer unit tests
├── src/
│   ├── App.jsx           # Page layout and Run button logic
│   ├── lexerApi.js       # Connects the web app to the Python server
│   ├── components/       # Editor, token table, console, keywords panel
│   └── styles.css        # Light and dark themes
├── index.html
├── package.json
└── vite.config.js
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Console says "Cannot reach the Python lexer server" | Start it with `npm run lexer` in another terminal |
| `'py' is not recognized` | Use `python backend/server.py` (or `python3` on macOS/Linux) |
| Port 5173 is already in use | Vite picks the next free port; use the URL shown in the terminal |

---

## Notes on the Specification

The lexer follows the group's Pork CCig documentation. Where a transition diagram and a written rule disagree, the **written rule** wins. Delimiters are applied **exactly as drawn**, so some code that looks normal is a lexical error:

| Code | Why it is an error | Works instead |
|---|---|---|
| `yummy;` | Only whitespace may follow `yummy` / `yuck` | `yummy ;` |
| `add(a, b)` | An identifier cannot be followed directly by `(` | `add (a, b)` |
| `i++;` | `++` cannot be followed directly by `;` | `i++ ;` |
| `x*2` | `*` cannot be followed directly by a digit | `x * 2` |

These are open items for consultation with the subject adviser.

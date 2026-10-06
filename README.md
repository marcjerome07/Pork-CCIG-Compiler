# Pork CCig Compiler

A browser-based compiler for **Pork CCig**, a cooking-themed, C-like programming language inspired by Filipino sisig.


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

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Console says "Cannot reach the Python lexer server" | Start it with `npm run lexer` in another terminal |
| `'py' is not recognized` | Use `python backend/server.py` (or `python3` on macOS/Linux) |
| Port 5173 is already in use | Vite picks the next free port; use the URL shown in the terminal |

---

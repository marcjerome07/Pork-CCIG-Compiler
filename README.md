# Pork CCig Compiler

## Quick Start

**Prerequisites**

- [Node.js](https://nodejs.org) 20.19 or later
- [Python](https://www.python.org) 3.8 or later (no `pip` packages needed)

**Install dependencies**

```bash
git clone https://github.com/marcjerome07/Pork-CCIG-Compiler.git
cd Pork-CCIG-Compiler
npm install
```

## Run the Project

Open two terminals in the project folder.

**Terminal 1: Python lexer server** (runs at `http://127.0.0.1:8000`)

```bash
npm run lexer
```

On macOS or Linux, use `python3 backend/server.py` instead.

**Terminal 2: web app**

```bash
npm run dev
```

Then open **http://localhost:5173** in your browser.

## Current Scope

Only lexical analysis is implemented.

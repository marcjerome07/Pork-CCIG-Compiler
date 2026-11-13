// Live syntax colors for the editor, built from the Python lexer's own output
// (the same POST /api/lex the Run button uses), so the colors always match the
// Lexer Table. This file only maps token types to color groups; the colors
// themselves are the --syn-* CSS variables in styles.css.

import { errorRanges } from './errorRanges.js';

const WHITESPACE_TYPES = new Set(['space', 'newline', 'tab']);
const COMMENT_TYPES = new Set(['Single-Line Comment', 'Multi-Line Comment']);
const NUMBER_TYPES = new Set(['meat_lit', 'sauce_lit']);
const STRING_TYPES = new Set(['chop_lit', 'recipe_lit']);
// Symbols built only from the lexer's OPERATORS characters (backend/lexer/dfa_lexer.py);
// every other symbol ({ } ( ) [ ] . , : ;) is a delimiter.
const OPERATOR_SYMBOL = /^[+\-*/%<>=!&|]+$/;

// Color group for a lexer token type, or null for whitespace (left uncolored).
// dataTypes: the keywords in the lexer's "Data Types" group (from /api/keywords).
export function tokenGroup(type, dataTypes) {
  if (WHITESPACE_TYPES.has(type)) return null;
  if (COMMENT_TYPES.has(type)) return 'comment';
  if (NUMBER_TYPES.has(type)) return 'number';
  if (STRING_TYPES.has(type)) return 'string';
  if (/^id\d*$/.test(type)) return 'identifier';
  if (/^[a-z]+$/.test(type)) return dataTypes.has(type) ? 'datatype' : 'keyword';
  if (OPERATOR_SYMBOL.test(type)) return 'operator';
  return 'delimiter';
}

function lineStarts(text) {
  const starts = [0];
  for (let i = 0; i < text.length; i++) if (text.charCodeAt(i) === 10) starts.push(i + 1);
  return starts;
}

// Colored character ranges { start, end, group } for `text`, sorted by start.
// Lexer errors become "invalid" ranges. Like errorRanges, (line, col) maps
// straight to an offset, and anything whose lexeme no longer matches is dropped.
export function lexSpans(text, tokens, errors, dataTypes) {
  const starts = lineStarts(text);
  const spans = [];
  for (const token of tokens) {
    const group = tokenGroup(token.type, dataTypes);
    const lineStart = starts[token.line - 1];
    if (!group || lineStart === undefined) continue;
    const start = lineStart + token.col - 1;
    const end = start + token.lexeme.length;
    if (text.slice(start, end) === token.lexeme) spans.push({ start, end, group });
  }
  for (const range of errorRanges(text, errors)) {
    spans.push({ start: range.start, end: range.end, group: 'invalid' });
  }
  return spans.sort((a, b) => a.start - b.start);
}

// Carries spans found for `oldText` over to `newText` while the next lex is
// pending: spans before the edit stay, spans after it shift by the length change,
// and spans touching the edited stretch are dropped (shown plain until the lexer answers).
export function shiftSpans(oldText, spans, newText) {
  if (oldText === newText) return spans;
  const max = Math.min(oldText.length, newText.length);
  let prefix = 0;
  while (prefix < max && oldText.charCodeAt(prefix) === newText.charCodeAt(prefix)) prefix++;
  let suffix = 0;
  while (
    suffix < max - prefix &&
    oldText.charCodeAt(oldText.length - 1 - suffix) === newText.charCodeAt(newText.length - 1 - suffix)
  ) {
    suffix++;
  }
  const oldTail = oldText.length - suffix;
  const delta = newText.length - oldText.length;
  const shifted = [];
  for (const span of spans) {
    if (span.end <= prefix) shifted.push(span);
    else if (span.start >= oldTail) shifted.push({ ...span, start: span.start + delta, end: span.end + delta });
  }
  return shifted;
}

// Splits the text into lines of pieces { text, group } for the syntax layer.
// Every character appears exactly once, so the layer lines up with the textarea.
export function highlightLines(text, spans) {
  const lines = [[]];
  const add = (from, to, group) => {
    const piece = text.slice(from, to);
    if (!piece.includes('\n')) {
      if (piece) lines[lines.length - 1].push({ text: piece, group });
      return;
    }
    piece.split('\n').forEach((part, i) => {
      if (i > 0) lines.push([]);
      if (part) lines[lines.length - 1].push({ text: part, group });
    });
  };
  let pos = 0;
  for (const span of spans) {
    if (span.start < pos) continue;
    if (span.start > pos) add(pos, span.start, null);
    add(span.start, span.end, span.group);
    pos = span.end;
  }
  add(pos, text.length, null);
  return lines;
}

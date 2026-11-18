// Auto-closing pairs for the source editor, like VS Code. Each function returns an
// edit in the same form as indentation.js: replace text[start, end) with `text`,
// then select [selStart, selEnd). Returns null to let the key type normally.

const BRACKETS = { '(': ')', '[': ']', '{': '}' };
const QUOTES = new Set(['"', "'"]);
const CLOSERS = new Set([...Object.values(BRACKETS), ...QUOTES]);

// A pair is only auto-closed when the caret is followed by one of these (or by
// nothing), so typing in front of existing code does not add stray closers.
const CLOSE_BEFORE = new Set([' ', '\t', '\n', '', ';', ':', '.', ',', '=', ')', ']', '}', '>']);

const isWordChar = (ch) => /[A-Za-z0-9_]/.test(ch);

// Whether the caret, after `before` (the line up to the caret), is inside a
// string, a character literal or a // comment.
function inLiteralOrComment(before) {
  let quote = null;
  for (let i = 0; i < before.length; i++) {
    const ch = before[i];
    if (quote) {
      if (ch === '\\') i++;
      else if (ch === quote) quote = null;
    } else if (QUOTES.has(ch)) {
      quote = ch;
    } else if (ch === '/' && before[i + 1] === '/') {
      return true;
    }
  }
  return quote !== null;
}

const caretAt = (pos) => ({ selStart: pos, selEnd: pos });

// Typing an opening bracket or a quote.
export function openEdit(text, selStart, selEnd, ch) {
  const close = BRACKETS[ch] ?? (QUOTES.has(ch) ? ch : null);
  if (!close) return null;

  // With text selected, wrap it in the pair and keep it selected.
  if (selStart !== selEnd) {
    const selected = text.slice(selStart, selEnd);
    return { start: selStart, end: selEnd, text: ch + selected + close, selStart: selStart + 1, selEnd: selEnd + 1 };
  }

  const before = text.slice(text.lastIndexOf('\n', selStart - 1) + 1, selStart);
  const next = text.charAt(selStart);
  const prev = before.slice(-1);

  if (QUOTES.has(ch)) {
    // Typing the quote that is already next just steps over it (closing a pair).
    if (next === ch && inLiteralOrComment(before)) return { start: selStart, end: selStart, text: '', ...caretAt(selStart + 1) };
    // No pair inside a literal or comment, or right after a word or a backslash.
    if (inLiteralOrComment(before) || isWordChar(prev) || prev === '\\') return null;
  } else if (inLiteralOrComment(before)) {
    return null;
  }

  if (!CLOSE_BEFORE.has(next)) return null;
  return { start: selStart, end: selStart, text: ch + close, ...caretAt(selStart + 1) };
}

// Typing ) ] } when that same character is already next: step over it.
// (Quotes are handled by openEdit, since a quote both opens and closes.)
export function overtypeEdit(text, selStart, selEnd, ch) {
  if (selStart !== selEnd || QUOTES.has(ch) || !CLOSERS.has(ch)) return null;
  if (text.charAt(selStart) !== ch) return null;
  return { start: selStart, end: selStart, text: '', ...caretAt(selStart + 1) };
}

// Backspace between an empty pair, as in (|) or "|", deletes both characters.
export function deletePairEdit(text, selStart, selEnd) {
  if (selStart !== selEnd || selStart === 0) return null;
  const prev = text.charAt(selStart - 1);
  const next = text.charAt(selStart);
  const close = BRACKETS[prev] ?? (QUOTES.has(prev) ? prev : null);
  if (!close || next !== close) return null;
  return { start: selStart - 1, end: selStart + 1, text: '', ...caretAt(selStart - 1) };
}

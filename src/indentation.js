// Auto-indentation rules for the source editor. Each function returns an edit:
// replace text[start, end) with `text`, then select [selStart, selEnd).
// Returns null when there is nothing to change.

// Indent size, in spaces. Change it here to change it everywhere.
export const INDENT_SIZE = 4;
export const INDENT = ' '.repeat(INDENT_SIZE);

const PAIRS = { '{': '}', '(': ')', '[': ']' };
export const CLOSERS = new Set(Object.values(PAIRS));

function lineStartAt(text, pos) {
  return text.lastIndexOf('\n', pos - 1) + 1;
}

function leadingWhitespace(line) {
  return line.match(/^[ \t]*/)[0];
}

// Leading whitespace with one indent level removed (back to the previous indent stop).
function outdentWhitespace(ws) {
  if (ws.endsWith('\t')) return ws.slice(0, -1);
  const spaces = ws.match(/ *$/)[0].length;
  const remove = spaces === 0 ? 0 : Math.min(spaces, ((ws.length - 1) % INDENT_SIZE) + 1);
  return ws.slice(0, ws.length - remove);
}

// Enter: keep the current line's indentation, one level deeper after { ( [,
// and between a pair like {|} put the closer on its own line below.
export function newlineEdit(text, selStart, selEnd) {
  const lineStart = lineStartAt(text, selStart);
  const before = text.slice(lineStart, selStart);
  const indent = leadingWhitespace(before);
  const closer = PAIRS[before.trimEnd().slice(-1)];
  if (!closer) {
    const insert = '\n' + indent;
    const caret = selStart + insert.length;
    return { start: selStart, end: selEnd, text: insert, selStart: caret, selEnd: caret };
  }
  const inner = '\n' + indent + INDENT;
  const caret = selStart + inner.length;
  const [gap, next] = text.slice(selEnd).match(/^([ \t]*)(.?)/).slice(1);
  if (next === closer) {
    const insert = inner + '\n' + indent;
    return { start: selStart, end: selEnd + gap.length, text: insert, selStart: caret, selEnd: caret };
  }
  return { start: selStart, end: selEnd, text: inner, selStart: caret, selEnd: caret };
}

// Typing } ) or ] as the first thing on a line removes one indent level.
export function closerEdit(text, selStart, selEnd, closer) {
  if (selStart !== selEnd) return null;
  const lineStart = lineStartAt(text, selStart);
  const before = text.slice(lineStart, selStart);
  if (before === '' || before.trim() !== '') return null;
  const indent = outdentWhitespace(before);
  const caret = lineStart + indent.length + 1;
  return { start: lineStart, end: selStart, text: indent + closer, selStart: caret, selEnd: caret };
}

// Tab / Shift+Tab on every line the selection touches.
export function indentLinesEdit(text, selStart, selEnd, outdent) {
  const blockStart = lineStartAt(text, selStart);
  // A selection that ends at the very start of a line does not include that line.
  const lastPos = selEnd > selStart && text[selEnd - 1] === '\n' ? selEnd - 1 : selEnd;
  const nextBreak = text.indexOf('\n', lastPos);
  const blockEnd = nextBreak === -1 ? text.length : nextBreak;
  const lines = text.slice(blockStart, blockEnd).split('\n');

  // Per line: characters added at, or removed from, the start of the line.
  const edits = lines.map((line) => {
    if (outdent) {
      const ws = leadingWhitespace(line);
      return { added: '', removed: ws.length - outdentWhitespace(ws).length };
    }
    const skip = lines.length > 1 && line.trim() === '';
    return { added: skip ? '' : INDENT, removed: 0 };
  });
  if (edits.every((e) => !e.added && !e.removed)) return null;

  const replacement = lines.map((line, i) => edits[i].added + line.slice(edits[i].removed)).join('\n');

  // Shift an offset in the original text to the matching offset after the edit.
  // A selection starting at column 0 stays there, so whole selected lines stay selected.
  const mapPos = (pos, keepAtLineStart) => {
    let lineStart = blockStart;
    let shift = 0;
    for (let i = 0; i < lines.length; i++) {
      const { added, removed } = edits[i];
      const lineEnd = lineStart + lines[i].length;
      if (pos <= lineEnd) {
        const col = pos - lineStart;
        const newCol = col === 0 && keepAtLineStart ? 0 : Math.max(0, col - removed) + added.length;
        return lineStart + shift + newCol;
      }
      shift += added.length - removed;
      lineStart = lineEnd + 1;
    }
    return pos + shift;
  };

  const hasSelection = selEnd > selStart;
  return {
    start: blockStart,
    end: blockEnd,
    text: replacement,
    selStart: mapPos(selStart, hasSelection),
    selEnd: mapPos(selEnd, false),
  };
}

// Turns lexer errors (1-based line/col + lexeme) into character ranges in the
// editor text. The lexer counts a tab as one column and resets the column after
// every newline, so (line, col) maps straight to an offset; the lexeme's length
// gives the end. The editor text only ever contains "\n" line breaks.

function lineStarts(text) {
  const starts = [0];
  for (let i = 0; i < text.length; i++) if (text.charCodeAt(i) === 10) starts.push(i + 1);
  return starts;
}

// Returns ranges sorted by start: { start, end, startLine, endLine, error }.
// Errors whose lexeme no longer matches the text at that position are dropped.
export function errorRanges(text, errors) {
  const starts = lineStarts(text);
  const ranges = [];
  for (const error of errors) {
    const lineStart = starts[error.line - 1];
    if (lineStart === undefined || !error.lexeme) continue;
    const start = lineStart + error.col - 1;
    const end = start + error.lexeme.length;
    if (text.slice(start, end) !== error.lexeme) continue;
    let endLine = error.line;
    for (let i = start; i < end - 1; i++) if (text.charCodeAt(i) === 10) endLine++;
    ranges.push({ start, end, startLine: error.line, endLine, error });
  }
  return ranges.sort((a, b) => a.start - b.start);
}

// Line number -> errors that touch that line (for the gutter).
export function errorsByLine(ranges) {
  const map = new Map();
  for (const range of ranges) {
    for (let line = range.startLine; line <= range.endLine; line++) {
      if (!map.has(line)) map.set(line, []);
      map.get(line).push(range.error);
    }
  }
  return map;
}

// Splits the text into plain and error pieces for the highlight layer.
// An error piece that covers an empty line gets a one-space marker so that line
// still shows red (e.g. inside an unterminated multi-line comment).
export function highlightSegments(text, ranges) {
  const segments = [];
  let pos = 0;
  ranges.forEach((range, index) => {
    if (range.start > pos) segments.push({ text: text.slice(pos, range.start) });
    const parts = text.slice(range.start, range.end).split('\n');
    parts.forEach((part, i) => {
      const last = i === parts.length - 1;
      if (part) {
        segments.push({ text: part, error: range.error, index });
      } else if (!last) {
        // The error covers an empty stretch that ends in a line break: mark it
        // with one space (adding a space before "\n" moves nothing on screen).
        segments.push({ text: ' ', error: range.error, index });
      }
      if (!last) segments.push({ text: '\n' });
    });
    pos = range.end;
  });
  if (pos < text.length) segments.push({ text: text.slice(pos) });
  return segments;
}

// The range containing a character offset, if any.
export function rangeAt(ranges, offset) {
  return ranges.find((r) => offset >= r.start && offset < r.end) || null;
}

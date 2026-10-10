import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { errorRanges, errorsByLine, highlightSegments, rangeAt } from '../errorRanges.js';
import { readStorage, writeStorage } from '../storage.js';

const FONT_KEY = 'pork-editor-font-size';
const DEFAULT_FONT = 14;
const MIN_FONT = 8;
const MAX_FONT = 32;
const STEP = 2;
const TAB = '    ';

function clampFont(size) {
  return Math.min(MAX_FONT, Math.max(MIN_FONT, size));
}

function loadFontSize() {
  const saved = Number.parseInt(readStorage(FONT_KEY, ''), 10);
  return Number.isFinite(saved) ? clampFont(saved) : DEFAULT_FONT;
}

// Toggles "// " on every line touched by the selection, like VS Code's Ctrl+/.
// Returns the replacement for text[blockStart, blockEnd) and the new selection.
function toggleLineComments(text, selStart, selEnd) {
  const blockStart = selStart === 0 ? 0 : text.lastIndexOf('\n', selStart - 1) + 1;
  // A selection that ends at the very start of a line does not include that line.
  const lastPos = selEnd > selStart && text[selEnd - 1] === '\n' ? selEnd - 1 : selEnd;
  const nextBreak = text.indexOf('\n', lastPos);
  const blockEnd = nextBreak === -1 ? text.length : nextBreak;
  const lines = text.slice(blockStart, blockEnd).split('\n');

  const indentOf = (line) => line.length - line.trimStart().length;
  const filled = lines.filter((line) => line.trim() !== '');
  const uncomment = filled.length > 0 && filled.every((line) => line.trimStart().startsWith('//'));
  const commentCol = filled.length ? Math.min(...filled.map(indentOf)) : 0;

  // Per line: where the edit happens, how many characters are removed and the text inserted.
  const edits = lines.map((line) => {
    if (uncomment) {
      if (line.trim() === '') return { col: 0, removed: 0, added: '' };
      const col = indentOf(line);
      return { col, removed: line.startsWith('// ', col) ? 3 : 2, added: '' };
    }
    if (line.trim() === '' && filled.length) return { col: 0, removed: 0, added: '' };
    return { col: commentCol, removed: 0, added: '// ' };
  });

  const replacement = lines
    .map((line, i) => {
      const { col, removed, added } = edits[i];
      return line.slice(0, col) + added + line.slice(col + removed);
    })
    .join('\n');

  // Shift an offset in the original text to the matching offset after the edit.
  // A selection start sitting exactly where "// " goes stays put, so the comment is selected too.
  const mapPos = (pos, keepAtInsert) => {
    let lineStart = blockStart;
    let shift = 0;
    for (let i = 0; i < lines.length; i++) {
      const { col, removed, added } = edits[i];
      const lineEnd = lineStart + lines[i].length;
      if (pos <= lineEnd) {
        const c = pos - lineStart;
        let newC = c;
        if (c === col && added && keepAtInsert) newC = c;
        else if (c >= col + removed) newC = c - removed + added.length;
        else if (c > col) newC = col;
        return lineStart + shift + newC;
      }
      shift += added.length - removed;
      lineStart = lineEnd + 1;
    }
    return pos + shift;
  };

  const hasSelection = selEnd > selStart;
  return {
    blockStart,
    blockEnd,
    replacement,
    selStart: mapPos(selStart, hasSelection),
    selEnd: mapPos(selEnd, false),
  };
}

// Width a character takes on screen, in columns (tabs stop every 4 columns, like the CSS tab-size).
function visualWidth(ch, column) {
  return ch === '\t' ? TAB.length - (column % TAB.length) : 1;
}

const CodeEditor = forwardRef(function CodeEditor(
  { value, onChange, onRun, running, errors = [] },
  ref
) {
  const [fontSize, setFontSize] = useState(loadFontSize);
  const [caretLine, setCaretLine] = useState(1);
  const [focused, setFocused] = useState(false);
  const [hover, setHover] = useState(null); // { x, y, range } for the error tooltip
  const surfaceRef = useRef(null);
  const textareaRef = useRef(null);
  const gutterRef = useRef(null);
  const highlightRef = useRef(null);
  const errorLayerRef = useRef(null);
  const measureRef = useRef(null);
  const charWidthRef = useRef(8);
  const escapedRef = useRef(false);

  // Whole-pixel line height keeps gutter rows and text rows on the same grid at every zoom level.
  const lineHeight = Math.round(fontSize * 1.5);
  const lineCount = value.split('\n').length;

  // Error highlights: character ranges, the lines they touch, and the highlight-layer pieces.
  const ranges = useMemo(() => errorRanges(value, errors), [value, errors]);
  const lineErrors = useMemo(() => errorsByLine(ranges), [ranges]);
  const segments = useMemo(() => highlightSegments(value, ranges), [value, ranges]);

  const zoomBy = useCallback((delta) => setFontSize((s) => clampFont(s + delta)), []);
  const resetZoom = useCallback(() => setFontSize(DEFAULT_FONT), []);

  useEffect(() => writeStorage(FONT_KEY, fontSize), [fontSize]);

  // The editor font is monospace, so one measured width serves every character.
  useLayoutEffect(() => {
    const el = measureRef.current;
    if (el) charWidthRef.current = el.getBoundingClientRect().width / el.textContent.length;
  }, [fontSize]);

  const syncScroll = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    if (gutterRef.current) gutterRef.current.scrollTop = ta.scrollTop;
    if (highlightRef.current) {
      highlightRef.current.style.transform = `translateY(${-ta.scrollTop}px)`;
    }
    if (errorLayerRef.current) {
      errorLayerRef.current.style.transform = `translate(${-ta.scrollLeft}px, ${-ta.scrollTop}px)`;
    }
  }, []);

  // Re-align after zoom or content changes (the textarea's scroll range changes with them).
  useLayoutEffect(syncScroll, [fontSize, value, focused, caretLine, segments, syncScroll]);

  // Character offset under a mouse position, or null outside the text.
  const offsetAtPoint = useCallback(
    (clientX, clientY) => {
      const ta = textareaRef.current;
      const style = getComputedStyle(ta);
      const rect = ta.getBoundingClientRect();
      const x = clientX - rect.left + ta.scrollLeft - parseFloat(style.paddingLeft);
      const y = clientY - rect.top + ta.scrollTop - parseFloat(style.paddingTop);
      if (x < 0 || y < 0) return null;
      const lines = value.split('\n');
      const lineIndex = Math.floor(y / lineHeight);
      if (lineIndex >= lines.length) return null;
      let offset = 0;
      for (let i = 0; i < lineIndex; i++) offset += lines[i].length + 1;
      const columnAtX = x / charWidthRef.current;
      let column = 0;
      for (const ch of lines[lineIndex]) {
        column += visualWidth(ch, column);
        if (columnAtX < column) return offset;
        offset += 1;
      }
      // Just past the end of the line: the line break, which an error may cover.
      return columnAtX < column + 1 && lineIndex < lines.length - 1 ? offset : null;
    },
    [value, lineHeight]
  );

  const handleMouseMove = (e) => {
    if (!ranges.length) return;
    const offset = offsetAtPoint(e.clientX, e.clientY);
    const range = offset === null ? null : rangeAt(ranges, offset);
    if (!range) {
      if (hover) setHover(null);
      return;
    }
    const box = surfaceRef.current.getBoundingClientRect();
    setHover({ x: e.clientX - box.left, y: e.clientY - box.top, range });
  };

  // Clear a stale tooltip when the highlights change (new run or an edit).
  useEffect(() => setHover(null), [ranges]);

  const updateCaretLine = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    const before = ta.value.slice(0, ta.selectionStart);
    let line = 1;
    for (let i = 0; i < before.length; i++) if (before.charCodeAt(i) === 10) line++;
    setCaretLine(line);
  }, []);

  // Lets the console select an error's characters and scroll them into view.
  useImperativeHandle(
    ref,
    () => ({
      revealError(error) {
        const ta = textareaRef.current;
        const [range] = errorRanges(value, [error]);
        if (!ta || !range) return;
        ta.focus();
        ta.setSelectionRange(range.start, range.end);
        const lineText = value.slice(value.lastIndexOf('\n', range.start - 1) + 1, range.start);
        let column = 0;
        for (const ch of lineText) column += visualWidth(ch, column);
        const top = (range.startLine - 1) * lineHeight;
        ta.scrollTop = Math.max(0, top - (ta.clientHeight - lineHeight) / 2);
        const left = column * charWidthRef.current;
        if (left < ta.scrollLeft || left > ta.scrollLeft + ta.clientWidth - 40) {
          ta.scrollLeft = Math.max(0, left - ta.clientWidth / 3);
        }
        updateCaretLine();
        syncScroll();
      },
    }),
    [value, lineHeight, updateCaretLine, syncScroll]
  );

  // Ctrl/Cmd + wheel over the editor zooms the editor only. Needs a non-passive
  // listener so preventDefault can stop the browser's page zoom.
  useEffect(() => {
    const el = surfaceRef.current;
    if (!el) return undefined;
    const onWheel = (e) => {
      if (!(e.ctrlKey || e.metaKey) || e.deltaY === 0) return;
      e.preventDefault();
      zoomBy(e.deltaY < 0 ? STEP : -STEP);
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  }, [zoomBy]);

  const insertText = (text) => {
    const ta = textareaRef.current;
    // execCommand keeps the native undo stack intact; fall back if unsupported.
    // insertText with an empty string is unreliable, so deletions use "delete".
    const done = text
      ? document.execCommand?.('insertText', false, text)
      : ta.selectionStart === ta.selectionEnd || document.execCommand?.('delete');
    if (!done) {
      ta.setRangeText(text, ta.selectionStart, ta.selectionEnd, 'end');
      onChange(ta.value);
    }
  };

  const handleKeyDown = (e) => {
    const mod = e.ctrlKey || e.metaKey;
    if (mod && (e.key === '=' || e.key === '+')) {
      e.preventDefault();
      zoomBy(STEP);
      return;
    }
    if (mod && e.key === '-') {
      e.preventDefault();
      zoomBy(-STEP);
      return;
    }
    if (mod && e.key === '0') {
      e.preventDefault();
      resetZoom();
      return;
    }
    if (mod && (e.key === '/' || e.code === 'Slash')) {
      e.preventDefault();
      const ta = textareaRef.current;
      const edit = toggleLineComments(ta.value, ta.selectionStart, ta.selectionEnd);
      ta.setSelectionRange(edit.blockStart, edit.blockEnd);
      insertText(edit.replacement);
      ta.setSelectionRange(edit.selStart, edit.selEnd);
      updateCaretLine();
      return;
    }
    if (e.key === 'Escape') {
      // Escape, then Tab, moves focus out of the editor instead of indenting.
      escapedRef.current = true;
      return;
    }
    if (e.key === 'Tab' && !e.shiftKey && !mod && !e.altKey && !escapedRef.current) {
      e.preventDefault();
      insertText(TAB);
    }
    escapedRef.current = false;
  };

  // Keep focus in the textarea when clicking toolbar buttons so the caret and selection survive.
  const keepFocus = (e) => e.preventDefault();

  const lineNumbers = [];
  for (let i = 1; i <= lineCount; i++) {
    const errorsHere = lineErrors.get(i);
    let className = i === caretLine && focused ? 'gutter-line active' : 'gutter-line';
    if (errorsHere) className += ' has-error';
    lineNumbers.push(
      <div
        key={i}
        className={className}
        title={errorsHere?.map((e) => e.message).join('\n')}
      >
        {i}
      </div>
    );
  }

  const editorStyle = {
    fontSize: `${fontSize}px`,
    lineHeight: `${lineHeight}px`,
    '--gutter-chars': Math.max(2, String(lineCount).length),
  };

  return (
    <section className="panel editor-panel" aria-labelledby="editor-title">
      <div className="panel-header">
        <h2 id="editor-title" className="panel-title">Source Code</h2>
        <div className="toolbar">
          <div className="zoom-controls" role="group" aria-label="Editor zoom">
            <button
              type="button"
              className="btn btn-icon"
              onMouseDown={keepFocus}
              onClick={() => zoomBy(-STEP)}
              disabled={fontSize <= MIN_FONT}
              title="Zoom Out (Ctrl/Cmd + −)"
              aria-label="Zoom out"
            >
              −
            </button>
            <button
              type="button"
              className="btn btn-icon zoom-value"
              onMouseDown={keepFocus}
              onClick={resetZoom}
              title="Reset Zoom (Ctrl/Cmd + 0)"
              aria-label={`Reset zoom, current font size ${fontSize} pixels`}
            >
              {fontSize}px
            </button>
            <button
              type="button"
              className="btn btn-icon"
              onMouseDown={keepFocus}
              onClick={() => zoomBy(STEP)}
              disabled={fontSize >= MAX_FONT}
              title="Zoom In (Ctrl/Cmd + +)"
              aria-label="Zoom in"
            >
              +
            </button>
            <button
              type="button"
              className="btn btn-text"
              onMouseDown={keepFocus}
              onClick={resetZoom}
              disabled={fontSize === DEFAULT_FONT}
              title="Reset Zoom (Ctrl/Cmd + 0)"
            >
              Reset
            </button>
          </div>
          <button type="button" className="btn btn-primary" onClick={onRun} disabled={running}>
            <span aria-hidden="true">▶</span> {running ? 'Running…' : 'Run'}
          </button>
        </div>
      </div>

      <div className="editor-surface" ref={surfaceRef} style={editorStyle}>
        <div className="gutter" ref={gutterRef} aria-hidden="true">
          <div className="gutter-inner">{lineNumbers}</div>
        </div>
        <div className="code-area">
          <span ref={measureRef} className="char-measure" aria-hidden="true">
            0000000000
          </span>
          {focused && (
            <div
              ref={highlightRef}
              className="current-line"
              style={{ top: `calc(var(--editor-pad) + ${(caretLine - 1) * lineHeight}px)`, height: lineHeight }}
              aria-hidden="true"
            />
          )}
          {ranges.length > 0 && (
            // A copy of the text behind the (transparent) textarea; only the error
            // pieces are drawn. React escapes the text, so < > & show as-is.
            <div ref={errorLayerRef} className="error-layer" aria-hidden="true">
              {segments.map((segment, i) =>
                segment.error ? (
                  <span
                    key={i}
                    className={hover?.range.error === segment.error ? 'error-mark hovered' : 'error-mark'}
                  >
                    {segment.text}
                  </span>
                ) : (
                  <span key={i}>{segment.text}</span>
                )
              )}
            </div>
          )}
          <textarea
            ref={textareaRef}
            className="code-input"
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              updateCaretLine();
            }}
            onScroll={() => {
              syncScroll();
              if (hover) setHover(null);
            }}
            onMouseMove={handleMouseMove}
            onMouseLeave={() => setHover(null)}
            onSelect={updateCaretLine}
            onKeyUp={updateCaretLine}
            onMouseUp={updateCaretLine}
            onKeyDown={handleKeyDown}
            onFocus={() => {
              setFocused(true);
              updateCaretLine();
            }}
            onBlur={() => setFocused(false)}
            wrap="off"
            spellCheck={false}
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            aria-label="Source code"
            aria-multiline="true"
          />
        </div>
        {hover && (
          <div className="error-tooltip" role="tooltip" style={{ left: hover.x + 12, top: hover.y + 18 }}>
            <span>{hover.range.error.message}</span>
          </div>
        )}
      </div>
    </section>
  );
});

export default CodeEditor;

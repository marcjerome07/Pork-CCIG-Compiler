import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
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

export default function CodeEditor({ value, onChange, onRun, running }) {
  const [fontSize, setFontSize] = useState(loadFontSize);
  const [caretLine, setCaretLine] = useState(1);
  const [focused, setFocused] = useState(false);
  const surfaceRef = useRef(null);
  const textareaRef = useRef(null);
  const gutterRef = useRef(null);
  const highlightRef = useRef(null);
  const escapedRef = useRef(false);

  // Whole-pixel line height keeps gutter rows and text rows on the same grid at every zoom level.
  const lineHeight = Math.round(fontSize * 1.5);
  const lineCount = value.split('\n').length;

  const zoomBy = useCallback((delta) => setFontSize((s) => clampFont(s + delta)), []);
  const resetZoom = useCallback(() => setFontSize(DEFAULT_FONT), []);

  useEffect(() => writeStorage(FONT_KEY, fontSize), [fontSize]);

  const syncScroll = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    if (gutterRef.current) gutterRef.current.scrollTop = ta.scrollTop;
    if (highlightRef.current) {
      highlightRef.current.style.transform = `translateY(${-ta.scrollTop}px)`;
    }
  }, []);

  // Re-align after zoom or content changes (the textarea's scroll range changes with them).
  useLayoutEffect(syncScroll, [fontSize, value, focused, caretLine, syncScroll]);

  const updateCaretLine = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    const before = ta.value.slice(0, ta.selectionStart);
    let line = 1;
    for (let i = 0; i < before.length; i++) if (before.charCodeAt(i) === 10) line++;
    setCaretLine(line);
  }, []);

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
    if (!document.execCommand?.('insertText', false, text)) {
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
    lineNumbers.push(
      <div key={i} className={i === caretLine && focused ? 'gutter-line active' : 'gutter-line'}>
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
          {focused && (
            <div
              ref={highlightRef}
              className="current-line"
              style={{ top: `calc(var(--editor-pad) + ${(caretLine - 1) * lineHeight}px)`, height: lineHeight }}
              aria-hidden="true"
            />
          )}
          <textarea
            ref={textareaRef}
            className="code-input"
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              updateCaretLine();
            }}
            onScroll={syncScroll}
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
      </div>
    </section>
  );
}

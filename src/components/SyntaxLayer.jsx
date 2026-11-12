import { forwardRef, memo, useEffect, useState } from 'react';

function samePieces(a, b) {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i].text !== b[i].text || a[i].group !== b[i].group) return false;
  }
  return true;
}

// One line of colored text, in its own block so the browser only re-lays out the
// lines that change. Memoized so typing only re-renders the lines that changed.
// An empty line holds a zero-width space so it keeps its height.
const SyntaxLine = memo(
  function SyntaxLine({ pieces }) {
    return (
      <div className="syntax-line">
        {pieces.length === 0
          ? '​'
          : pieces.map((piece, i) =>
              piece.group ? (
                <span key={i} className={`syn-${piece.group}`}>
                  {piece.text}
                </span>
              ) : (
                piece.text
              )
            )}
      </div>
    );
  },
  (prev, next) => samePieces(prev.pieces, next.pieces)
);

// Lines are rendered in whole chunks around the visible ones, so long code stays
// fast to type in and scrolling only re-renders when it crosses a chunk boundary.
const CHUNK = 50;

// Colored copy of the editor text, drawn behind the (transparent-text) textarea.
// Same box, font and padding as the textarea, so every character lines up. Only
// the lines near the textarea's scroll position are rendered; a spacer stands in
// for the lines above them (every line is exactly lineHeight tall).
const SyntaxLayer = forwardRef(function SyntaxLayer({ lines, lineHeight, textareaRef }, ref) {
  const [range, setRange] = useState({ first: 0, last: CHUNK * 2 });

  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return undefined;
    const update = () => {
      const top = Math.floor(ta.scrollTop / lineHeight);
      const bottom = Math.ceil((ta.scrollTop + ta.clientHeight) / lineHeight);
      const first = Math.max(0, (Math.floor(top / CHUNK) - 1) * CHUNK);
      const last = (Math.ceil(bottom / CHUNK) + 1) * CHUNK;
      setRange((r) => (r.first === first && r.last === last ? r : { first, last }));
    };
    update();
    ta.addEventListener('scroll', update, { passive: true });
    const observer = new ResizeObserver(update);
    observer.observe(ta);
    return () => {
      ta.removeEventListener('scroll', update);
      observer.disconnect();
    };
  }, [textareaRef, lineHeight]);

  return (
    <div ref={ref} className="syntax-layer" aria-hidden="true">
      <div style={{ height: range.first * lineHeight }} />
      {lines.slice(range.first, range.last).map((pieces, i) => (
        <SyntaxLine key={range.first + i} pieces={pieces} />
      ))}
    </div>
  );
});

export default SyntaxLayer;

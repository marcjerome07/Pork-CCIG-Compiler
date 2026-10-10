export default function ConsolePanel({ lines, onSelectError }) {
  return (
    <section className="panel console-panel" aria-labelledby="console-title">
      <div className="panel-header">
        <h2 id="console-title" className="panel-title">Console Output</h2>
      </div>
      <div className="console-body" role="log" aria-live="polite">
        {lines.length === 0 ? (
          <span className="placeholder">Console output will appear here.</span>
        ) : (
          lines.map((line, i) =>
            line.error && onSelectError ? (
              // Clicking an error selects its characters in the source code.
              <div
                key={i}
                className={`console-line console-${line.kind} console-link`}
                role="button"
                tabIndex={0}
                title="Show in source code"
                onClick={() => onSelectError(line.error)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectError(line.error);
                  }
                }}
              >
                {line.text}
              </div>
            ) : (
              <div key={i} className={`console-line console-${line.kind}`}>
                {line.text}
              </div>
            )
          )
        )}
      </div>
    </section>
  );
}

export default function ConsolePanel({ lines }) {
  return (
    <section className="panel console-panel" aria-labelledby="console-title">
      <div className="panel-header">
        <h2 id="console-title" className="panel-title">Console Output</h2>
      </div>
      <div className="console-body" role="log" aria-live="polite">
        {lines.length === 0 ? (
          <span className="placeholder">Console output will appear here.</span>
        ) : (
          lines.map((line, i) => (
            <div key={i} className={`console-line console-${line.kind}`}>
              {line.text}
            </div>
          ))
        )}
      </div>
    </section>
  );
}

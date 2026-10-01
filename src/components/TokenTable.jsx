// Whitespace lexemes are kept as-is in the data; only their display is made visible.
const WHITESPACE_DISPLAY = { ' ': '·', '\n': '\\n', '\t': '\\t' };
const WHITESPACE_NAMES = { ' ': 'space', '\n': 'newline', '\t': 'tab' };

function Lexeme({ value }) {
  if (value in WHITESPACE_DISPLAY) {
    return (
      <span className="lexeme-whitespace" title={WHITESPACE_NAMES[value]}>
        {WHITESPACE_DISPLAY[value]}
      </span>
    );
  }
  return value;
}

export default function TokenTable({ tokens }) {
  return (
    <section className="panel token-panel" aria-labelledby="tokens-title">
      <div className="panel-header">
        <h2 id="tokens-title" className="panel-title">Tokens</h2>
        {tokens.length > 0 && <span className="panel-count">{tokens.length}</span>}
      </div>
      <div className="token-scroll">
        <table className="token-table">
          <thead>
            <tr>
              <th scope="col">Token Type</th>
              <th scope="col">Lexeme</th>
              <th scope="col">Line</th>
              <th scope="col">Col</th>
            </tr>
          </thead>
          <tbody>
            {tokens.length === 0 ? (
              <tr>
                <td colSpan={4} className="empty-row">No tokens to display.</td>
              </tr>
            ) : (
              tokens.map((t, i) => (
                <tr key={i}>
                  <td>{t.type}</td>
                  <td className="mono lexeme-cell"><Lexeme value={t.lexeme} /></td>
                  <td>{t.line}</td>
                  <td>{t.col}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

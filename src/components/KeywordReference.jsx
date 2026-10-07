import { useEffect, useState } from 'react';
import { fetchKeywords } from '../lexerApi.js';
import { readStorage, writeStorage } from '../storage.js';

const OPEN_KEY = 'pork-keywords-open';

// The list comes from the Python lexer's own keyword table, so the UI and the lexer cannot drift apart.
export default function KeywordReference() {
  const [open, setOpen] = useState(() => readStorage(OPEN_KEY, 'false') === 'true');
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  const load = () => {
    setError('');
    fetchKeywords()
      .then(setData)
      .catch((err) => setError(err.message));
  };

  useEffect(load, []);

  const toggle = (e) => {
    setOpen(e.currentTarget.open);
    writeStorage(OPEN_KEY, e.currentTarget.open);
  };

  return (
    <details className="panel keyword-panel" open={open} onToggle={toggle}>
      <summary className="panel-header keyword-summary">
        <h2 className="panel-title">Keywords</h2>
        {data && <span className="panel-count">{data.keywords.length}</span>}
      </summary>
      <div className="keyword-body">
        {error && (
          <p className="keyword-message">
            {error}{' '}
            <button type="button" className="btn btn-text" onClick={load}>Retry</button>
          </p>
        )}
        {!error && !data && <p className="keyword-message">Loading keywords…</p>}
        {data &&
          data.groups.map((group) => (
            <div key={group} className="keyword-group">
              <h3 className="keyword-group-title">{group}</h3>
              <ul className="keyword-list">
                {data.keywords
                  .filter((k) => k.group === group)
                  .map((k) => (
                    <li key={k.word} title={k.description}>
                      <code className="keyword-word">{k.word}</code>
                      <span className="keyword-c">{k.cCounterpart}</span>
                    </li>
                  ))}
              </ul>
            </div>
          ))}
      </div>
    </details>
  );
  // Uncomment the above to show the keywords panel
}

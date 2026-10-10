import { useEffect, useMemo, useRef, useState } from 'react';
import CodeEditor from './components/CodeEditor.jsx';
import ConsolePanel from './components/ConsolePanel.jsx';
import KeywordReference from './components/KeywordReference.jsx';
import TokenTable from './components/TokenTable.jsx';
import ThemeToggle from './components/ThemeToggle.jsx';
import { lexSource } from './lexerApi.js';
import { readStorage, writeStorage } from './storage.js';

const THEME_KEY = 'pork-theme';

const plural = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`;

// Summary line, then each error message exactly as the lexer wrote it.
function summarize(tokens, errors) {
  const tokenText = plural(tokens.length, 'token');
  if (errors.length === 0) {
    return [{ kind: 'ok', text: `Lexical analysis complete: ${tokenText}, 0 errors.` }];
  }
  return [
    {
      kind: 'warn',
      text:
        `Lexical analysis complete with errors: ${tokenText}, ${plural(errors.length, 'error')} ` +
        `(${errors.filter((e) => e.status === 'Invalid').length} invalid, ` +
        `${errors.filter((e) => e.status === 'Unavailable').length} unavailable).`,
    },
    ...errors.map((e) => ({ kind: 'error', text: e.message, error: e })),
  ];
}

export default function App() {
  const [theme, setTheme] = useState(() =>
    readStorage(THEME_KEY, 'light') === 'dark' ? 'dark' : 'light'
  );
  const [source, setSource] = useState('');
  const [tokens, setTokens] = useState([]);
  const [consoleLines, setConsoleLines] = useState([]);
  const [running, setRunning] = useState(false);
  // Errors from the last run, with the exact source they were found in.
  const [lexed, setLexed] = useState({ source: null, errors: [] });
  const editorRef = useRef(null);

  // Highlights only apply to the text that was analyzed; editing hides them
  // until the next run (undoing back to that text shows them again).
  const noErrors = useMemo(() => [], []);
  const editorErrors = lexed.source === source ? lexed.errors : noErrors;

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    writeStorage(THEME_KEY, theme);
  }, [theme]);

  const handleRun = async () => {
    if (running) return;
    setRunning(true);
    try {
      if (source.length === 0) {
        setTokens([]);
        setLexed({ source: null, errors: [] });
        setConsoleLines([{ kind: 'info', text: 'No source code to analyze.' }]);
        return;
      }
      const result = await lexSource(source);
      setTokens(result.tokens);
      setLexed({ source, errors: result.errors });
      setConsoleLines(summarize(result.tokens, result.errors));
    } catch (err) {
      setTokens([]);
      setLexed({ source: null, errors: [] });
      setConsoleLines([{ kind: 'error', text: err.message }]);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">
          <img className="app-logo" src="/logo.png" alt="PORK CCIG Compiler" />
        </h1>
        <ThemeToggle
          theme={theme}
          onToggle={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}
        />
      </header>

      <main className="workspace">
        <CodeEditor
          ref={editorRef}
          value={source}
          onChange={setSource}
          onRun={handleRun}
          running={running}
          errors={editorErrors}
        />
        <div className="side-column">
          <KeywordReference />
          <TokenTable tokens={tokens} />
        </div>
        <ConsolePanel
          lines={consoleLines}
          onSelectError={(error) => editorRef.current?.revealError(error)}
        />
      </main>
    </div>
  );
}

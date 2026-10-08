import { useEffect, useState } from 'react';
import CodeEditor from './components/CodeEditor.jsx';
import ConsolePanel from './components/ConsolePanel.jsx';
import KeywordReference from './components/KeywordReference.jsx';
import TokenTable from './components/TokenTable.jsx';
import ThemeToggle from './components/ThemeToggle.jsx';
import { lexSource } from './lexerApi.js';
import { readStorage, writeStorage } from './storage.js';

const THEME_KEY = 'pork-theme';

function summarize(tokens, errors) {
  const tokenText = `${tokens.length} token${tokens.length === 1 ? '' : 's'}`;
  const errorText = `${errors.length} lexical error${errors.length === 1 ? '' : 's'}`;
  return [
    { kind: errors.length ? 'warn' : 'ok', text: `Lexical analysis finished: ${tokenText}, ${errorText}.` },
    ...errors.map((e) => ({ kind: 'error', text: `Line ${e.line}, Col ${e.col}: ${e.message}` })),
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
        setConsoleLines([{ kind: 'info', text: 'No source code to analyze.' }]);
        return;
      }
      const result = await lexSource(source);
      setTokens(result.tokens);
      setConsoleLines(summarize(result.tokens, result.errors));
    } catch (err) {
      setTokens([]);
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
        <CodeEditor value={source} onChange={setSource} onRun={handleRun} running={running} />
        <div className="side-column">
          <KeywordReference />
          <TokenTable tokens={tokens} />
        </div>
        <ConsolePanel lines={consoleLines} />
      </main>
    </div>
  );
}

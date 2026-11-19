import { useEffect, useMemo, useRef, useState } from 'react';
import CodeEditor from './components/CodeEditor.jsx';
import ConsolePanel from './components/ConsolePanel.jsx';
import KeywordReference from './components/KeywordReference.jsx';
import PhaseTabs from './components/PhaseTabs.jsx';
import TokenTable from './components/TokenTable.jsx';
import ThemeToggle from './components/ThemeToggle.jsx';
import { lexSource } from './lexerApi.js';
import { readStorage, writeStorage } from './storage.js';

// New key so browsers that saved the old light default pick up dark. Keep in sync with index.html.
const THEME_KEY = 'pork-theme-v2';

// The compiler phases shown as tabs. Run always performs every phase in order.
const PHASES = [
  { id: 'lexical', label: 'Lexical' },
  // Syntax tab hidden until the parser exists. Uncomment to show it again.
  // { id: 'syntax', label: 'Syntax' },
];

const NO_RUN = { status: 'idle' };

const plural = (count, word) => `${count} ${word}${count === 1 ? '' : 's'}`;

// Console lines for one phase: a summary line, then each error message exactly
// as the analyzer wrote it ("Line <n>, Col <n>: ..."). Clicking an error line
// selects it in the source code.
function summarize(phase, tokens, errors) {
  const name = phase === 'lexical' ? 'Lexical' : 'Syntax';
  const tokenText = phase === 'lexical' ? `${plural(tokens.length, 'token')}, ` : '';
  if (errors.length === 0) {
    return [{ kind: 'ok', text: `No ${name.toLowerCase()} errors: ${tokenText}0 errors.` }];
  }
  let counts = '';
  if (phase === 'lexical') {
    const unavailable = errors.filter((e) => e.status === 'Unavailable').length;
    counts = ` (${errors.length - unavailable} invalid, ${unavailable} unavailable)`;
  }
  return [
    { kind: 'warn', text: `${name} analysis complete with errors: ${tokenText}${plural(errors.length, 'error')}${counts}.` },
    ...errors.map((e) => ({ kind: 'error', text: e.message, error: e })),
  ];
}

// What the console shows for `phase` after `run` (see the run states below).
function consoleLines(phase, run) {
  if (run.status === 'idle') return [];
  if (run.status === 'empty') return [{ kind: 'info', text: 'No source code to analyze.' }];
  if (run.status === 'failed') return [{ kind: 'error', text: run.message }];
  if (phase === 'lexical') return summarize('lexical', run.tokens, run.lexErrors);
  const { syntax } = run;
  if (syntax.status === 'skipped') {
    return [{ kind: 'warn', text: 'Syntax analysis skipped: fix the lexical errors first.' }];
  }
  if (syntax.status === 'unavailable') {
    return [{ kind: 'info', text: 'Syntax analysis is not available yet.' }];
  }
  return summarize('syntax', run.tokens, syntax.status === 'error' ? syntax.errors : []);
}

export default function App() {
  const [theme, setTheme] = useState(() =>
    readStorage(THEME_KEY, 'dark') === 'light' ? 'light' : 'dark'
  );
  const [tab, setTab] = useState('lexical');
  const [source, setSource] = useState('');
  const [running, setRunning] = useState(false);
  // The last run, with the exact source it analyzed:
  //   { status: 'idle' }                      nothing run yet
  //   { status: 'empty' }                     run with no source code
  //   { status: 'failed', message }           the server could not be reached
  //   { status: 'done', source, tokens, lexErrors, syntax }
  // syntax: { status: 'skipped' } when the lexer found errors,
  //         { status: 'unavailable' } until the parser exists,
  //         { status: 'ok' } or { status: 'error', errors } once it does.
  const [run, setRun] = useState(NO_RUN);
  const editorRef = useRef(null);

  const tokens = run.status === 'done' ? run.tokens : [];

  // Highlights only apply to the text that was analyzed, and only for the phase
  // whose tab is open. Editing hides them until the next run (undoing back to
  // that text shows them again).
  const noErrors = useMemo(() => [], []);
  let editorErrors = noErrors;
  if (run.status === 'done' && run.source === source) {
    if (tab === 'lexical') editorErrors = run.lexErrors;
    else if (run.syntax.status === 'error') editorErrors = run.syntax.errors;
  }

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    writeStorage(THEME_KEY, theme);
  }, [theme]);

  const handleRun = async () => {
    if (running) return;
    setRunning(true);
    try {
      if (source.length === 0) {
        setRun({ status: 'empty' });
        return;
      }
      const result = await lexSource(source);
      // The lexer still tokenizes spaces (its delimiter rules need them); they
      // are just left out of the Lexer Table and the token count.
      const shown = result.tokens.filter((t) => t.type !== 'space');
      const lexErrors = result.errors;
      // The parser only runs on a program with no lexical errors.
      const syntax = lexErrors.length > 0 ? { status: 'skipped' } : { status: 'unavailable' };
      setRun({ status: 'done', source, tokens: shown, lexErrors, syntax });
      // Open the first phase that found errors.
      if (lexErrors.length > 0) setTab('lexical');
      else if (syntax.status === 'error') setTab('syntax');
    } catch (err) {
      setRun({ status: 'failed', message: err.message });
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">
          <img
            className="app-logo"
            src={theme === 'dark' ? '/logo-dark.png' : '/logo.png'}
            alt="PORK CCIG Compiler"
          />
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
          <TokenTable tokens={tokens} title={tab === 'syntax' ? 'Tokens' : 'Lexer Table'} />
        </div>
        <ConsolePanel
          // The tab bar only appears once there is more than one phase to switch between.
          tabs={PHASES.length > 1 ? <PhaseTabs phases={PHASES} active={tab} onSelect={setTab} /> : null}
          lines={consoleLines(tab, run)}
          onSelectError={(error) => editorRef.current?.revealError(error)}
        />
      </main>
    </div>
  );
}

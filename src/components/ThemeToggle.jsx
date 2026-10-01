export default function ThemeToggle({ theme, onToggle }) {
  const next = theme === 'light' ? 'dark' : 'light';
  return (
    <button
      type="button"
      className="btn btn-secondary theme-toggle"
      onClick={onToggle}
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
    >
      <span aria-hidden="true">{theme === 'light' ? '☾' : '☀'}</span>
      {theme === 'light' ? 'Dark' : 'Light'} mode
    </button>
  );
}

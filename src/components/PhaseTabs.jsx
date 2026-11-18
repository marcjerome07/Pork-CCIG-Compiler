// One tab per compiler phase, shown as folder tabs on the Console Output panel.
// The tabs only switch what the console shows and the editor marks; the source
// code and the Run button are shared.
export default function PhaseTabs({ phases, active, onSelect }) {
  return (
    <nav className="phase-tabs" role="tablist" aria-label="Compiler phase">
      {phases.map((phase) => (
        <button
          key={phase.id}
          type="button"
          role="tab"
          aria-selected={phase.id === active}
          className={`phase-tab${phase.id === active ? ' active' : ''}`}
          onClick={() => onSelect(phase.id)}
        >
          {phase.label}
        </button>
      ))}
    </nav>
  );
}

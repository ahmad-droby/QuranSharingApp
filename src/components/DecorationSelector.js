/**
 * Decoration selection component
 */
export const DecorationSelector = ({ decorations, decoration, setDecoration }) => (
  <section className="section">
    <h3 className="section-title"><span>🎨</span> Decorations</h3>
    <div className="deco-opts">
      {decorations.map(d => (
        <button
          key={d.id}
          className={`deco-btn ${decoration === d.id ? 'selected' : ''}`}
          onClick={() => setDecoration(d.id)}
        >
          {d.name}
        </button>
      ))}
    </div>
  </section>
);

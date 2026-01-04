/**
 * Saved designs gallery component
 */
export const Gallery = ({
  savedDesigns,
  surahInfo,
  loadDesign,
  deleteDesign,
  setActiveTab
}) => (
  <section className="gallery">
    <div className="gallery-header">
      <h2 className="gallery-title">Saved Designs</h2>
      <p className="gallery-sub">Click to edit</p>
    </div>

    {savedDesigns.length === 0 ? (
      <div className="empty">
        <div className="empty-icon">💾</div>
        <p className="empty-text">No saved designs yet.</p>
        <button
          className="btn btn-primary"
          onClick={() => setActiveTab('create')}
        >
          Create First Design
        </button>
      </div>
    ) : (
      <div className="gallery-grid">
        {savedDesigns.map(d => (
          <div
            key={d.id}
            className="gallery-item"
            onClick={() => loadDesign(d)}
          >
            <img src={d.thumb} alt="Saved design" className="gallery-img" />
            <div className="gallery-info">
              <div className="gallery-meta">
                <span>
                  {surahInfo.find(s => s.number === d.surahNum)?.name} {d.startAyah}
                  {d.endAyah !== d.startAyah ? `-${d.endAyah}` : ''}
                </span>
                <button
                  onClick={e => deleteDesign(d.id, e)}
                  style={{
                    background: 'rgba(255,0,0,0.2)',
                    border: 'none',
                    borderRadius: '4px',
                    padding: '4px 8px',
                    color: '#ff6b6b',
                    cursor: 'pointer'
                  }}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    )}
  </section>
);

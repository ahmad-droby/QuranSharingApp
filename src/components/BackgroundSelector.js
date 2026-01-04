/**
 * Background selection component
 */
export const BackgroundSelector = ({
  backgrounds,
  bgCategory,
  setBgCategory,
  background,
  setBackground,
  fileInputRef,
  handleUpload
}) => {
  const renderBgPreview = (bg) => (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: `linear-gradient(135deg, ${bg.colors.join(', ')})`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
    >
      {bg.pattern && <span style={{ fontSize: '1.2rem', opacity: 0.5 }}>☪</span>}
    </div>
  );

  return (
    <section className="section">
      <h3 className="section-title"><span>🖼️</span> Background</h3>

      <div className="bg-tabs">
        {Object.keys(backgrounds).map(c => (
          <button
            key={c}
            className={`bg-tab ${bgCategory === c ? 'active' : ''}`}
            onClick={() => setBgCategory(c)}
          >
            {c.charAt(0).toUpperCase() + c.slice(1)}
          </button>
        ))}
      </div>

      <div className="bg-grid">
        {backgrounds[bgCategory].map(bg => (
          <div
            key={bg.id}
            className={`bg-opt ${background.id === bg.id ? 'selected' : ''}`}
            onClick={() => setBackground(bg)}
            title={bg.name}
          >
            {renderBgPreview(bg)}
          </div>
        ))}
        <div
          className="bg-opt upload"
          onClick={() => fileInputRef.current?.click()}
        >
          <span>📤</span>
          <span>Upload</span>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleUpload}
          />
        </div>
      </div>
    </section>
  );
};

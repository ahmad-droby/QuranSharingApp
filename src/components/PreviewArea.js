/**
 * Canvas preview and actions component
 */
export const PreviewArea = ({
  canvasRef,
  formats,
  format,
  setFormat,
  download,
  setShowShareModal,
  saveDesign
}) => (
  <section className="preview-area">
    <div className="preview-container">
      <div className="preview-header">
        <h2 className="preview-title">Live Preview</h2>
        <div className="format-tabs">
          {Object.entries(formats).map(([k, v]) => (
            <button
              key={k}
              className={`format-tab ${format === k ? 'active' : ''}`}
              onClick={() => setFormat(k)}
            >
              {v.label}
            </button>
          ))}
        </div>
      </div>
      <div className="canvas-wrap">
        <canvas ref={canvasRef} className="canvas" />
      </div>
    </div>
    <div className="actions">
      <button className="action-btn download" onClick={download}>
        <span>⬇️</span> Download HD
      </button>
      <button className="action-btn share" onClick={() => setShowShareModal(true)}>
        <span>📤</span> Share
      </button>
      <button className="action-btn save" onClick={saveDesign}>
        <span>💾</span> Save
      </button>
    </div>
  </section>
);

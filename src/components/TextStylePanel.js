/**
 * Text styling panel component
 */
export const TextStylePanel = ({
  textColors,
  textColor,
  setTextColor,
  customColor,
  setCustomColor,
  autoFitText,
  setAutoFitText,
  arabicFontSize,
  setArabicFontSize,
  secondaryFontSize,
  setSecondaryFontSize,
  textPosition,
  setTextPosition,
  showArabic,
  setShowArabic,
  showSecondary,
  setShowSecondary,
  showReference,
  setShowReference,
  textType
}) => (
  <section className="section">
    <h3 className="section-title"><span>✏️</span> Text Style</h3>

    {/* Color selection */}
    <div className="custom-row">
      <span className="custom-label">Color</span>
      <div className="colors">
        {textColors.map(c => (
          <div
            key={c}
            className={`color-opt ${textColor === c ? 'selected' : ''}`}
            style={{ background: c }}
            onClick={() => setTextColor(c)}
          />
        ))}
        <div className="color-opt custom">
          <input
            type="color"
            value={customColor}
            onChange={e => {
              setCustomColor(e.target.value);
              setTextColor(e.target.value);
            }}
          />
        </div>
      </div>
    </div>

    {/* Auto-fit toggle */}
    <div className="toggle-row" style={{ marginBottom: '0.5rem' }}>
      <span className="toggle-label">Auto-fit Text</span>
      <div
        className={`toggle ${autoFitText ? 'on' : ''}`}
        onClick={() => setAutoFitText(!autoFitText)}
      />
    </div>

    {/* Arabic font size slider */}
    <div className="custom-row" style={{ opacity: autoFitText ? 0.5 : 1 }}>
      <span className="custom-label">Arabic Size</span>
      <div className="slider-wrap custom-ctrl">
        <input
          type="range"
          className="slider"
          min="16"
          max="72"
          value={arabicFontSize}
          onChange={e => setArabicFontSize(parseInt(e.target.value))}
          disabled={autoFitText}
        />
        <span className="slider-val">{arabicFontSize}px</span>
      </div>
    </div>

    {/* Secondary font size slider */}
    <div className="custom-row" style={{ opacity: autoFitText ? 0.5 : 1 }}>
      <span className="custom-label">{textType === 'tafsir' ? 'Tafsir Size' : 'English Size'}</span>
      <div className="slider-wrap custom-ctrl">
        <input
          type="range"
          className="slider"
          min="10"
          max="42"
          value={secondaryFontSize}
          onChange={e => setSecondaryFontSize(parseInt(e.target.value))}
          disabled={autoFitText}
        />
        <span className="slider-val">{secondaryFontSize}px</span>
      </div>
    </div>

    {/* Position selector */}
    <div className="custom-row">
      <span className="custom-label">Position</span>
      <div className="pos-grid custom-ctrl">
        {['top', 'center', 'bottom'].map(p => (
          <button
            key={p}
            className={`pos-btn ${textPosition === p ? 'selected' : ''}`}
            onClick={() => setTextPosition(p)}
          >
            <div className="pos-dot" />
          </button>
        ))}
      </div>
    </div>

    {/* Visibility toggles */}
    <div className="toggle-row">
      <span className="toggle-label">Show Arabic</span>
      <div
        className={`toggle ${showArabic ? 'on' : ''}`}
        onClick={() => setShowArabic(!showArabic)}
      />
    </div>

    <div className="toggle-row">
      <span className="toggle-label">Show {textType === 'tafsir' ? 'Tafsir' : 'Translation'}</span>
      <div
        className={`toggle ${showSecondary ? 'on' : ''}`}
        onClick={() => setShowSecondary(!showSecondary)}
      />
    </div>

    <div className="toggle-row">
      <span className="toggle-label">Show Reference</span>
      <div
        className={`toggle ${showReference ? 'on' : ''}`}
        onClick={() => setShowReference(!showReference)}
      />
    </div>
  </section>
);

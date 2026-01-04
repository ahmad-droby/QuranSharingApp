/**
 * Text type selection component (English/Tafsir)
 */
export const TextTypeSelector = ({
  textType,
  setTextType,
  tafsirAvailable,
  tafsirSurahsCount
}) => (
  <section className="section">
    <h3 className="section-title"><span>📝</span> Text Type</h3>

    <div className="text-type-tabs">
      <button
        className={`text-type-tab ${textType === 'english' ? 'active' : ''}`}
        onClick={() => setTextType('english')}
      >
        🌐 English Translation
      </button>
      <button
        className={`text-type-tab ${textType === 'tafsir' ? 'active' : ''} ${!tafsirAvailable ? 'disabled' : ''}`}
        onClick={() => tafsirAvailable && setTextType('tafsir')}
        title={tafsirAvailable ? 'التفسير الميسر' : 'Tafsir not available for this surah'}
      >
        📗 التفسير العربي
      </button>
    </div>

    {textType === 'tafsir' && tafsirAvailable && (
      <div className="tafsir-note">التفسير الميسر - Tafsir Al-Muyassar</div>
    )}
    {textType === 'tafsir' && !tafsirAvailable && (
      <div className="tafsir-note" style={{ background: 'rgba(255,100,100,0.1)' }}>
        التفسير غير متاح لهذه السورة - Tafsir available for: {tafsirSurahsCount} surahs
      </div>
    )}
  </section>
);

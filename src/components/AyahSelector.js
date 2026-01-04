/**
 * Ayah selection panel component
 */
export const AyahSelector = ({
  surahInfo,
  surahNum,
  setSurahNum,
  startAyah,
  setStartAyah,
  endAyah,
  setEndAyah,
  searchTerm,
  setSearchTerm,
  filteredSurahs,
  currentSurah,
  selectRandom,
  selectAll,
  hasTafsir,
  tafsirAvailable,
  arabicText,
  translationText,
  tafsirText,
  textType,
  referenceText,
  ayahsLength
}) => (
  <section className="section">
    <h3 className="section-title"><span>📖</span> Select Ayah Range</h3>

    <div className="search-box">
      <span className="search-icon">🔍</span>
      <input
        className="input"
        placeholder="Search surah..."
        value={searchTerm}
        onChange={e => setSearchTerm(e.target.value)}
        style={{ paddingLeft: '2.5rem' }}
      />
    </div>

    <div className="row">
      <select
        value={surahNum}
        onChange={e => setSurahNum(parseInt(e.target.value))}
        style={{ flex: 2 }}
      >
        {filteredSurahs.map(s => (
          <option key={s.number} value={s.number}>
            {s.number}. {s.name} ({s.arabicName}) - {s.ayahCount} ayahs {hasTafsir(s.number) ? '📗' : ''}
          </option>
        ))}
      </select>
      <button
        className="btn btn-primary btn-icon"
        onClick={selectRandom}
        title="Random Ayah"
      >
        🎲
      </button>
    </div>

    <div className="range-sel">
      <div className="range-col">
        <label className="range-label">From Ayah</label>
        <select
          value={startAyah}
          onChange={e => {
            const val = parseInt(e.target.value);
            setStartAyah(val);
            if (val > endAyah) setEndAyah(val);
          }}
        >
          {Array.from({ length: currentSurah?.ayahCount || 1 }, (_, i) => i + 1).map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
      <div className="range-col">
        <label className="range-label">To Ayah</label>
        <select
          value={endAyah}
          onChange={e => setEndAyah(parseInt(e.target.value))}
        >
          {Array.from({ length: (currentSurah?.ayahCount || 1) - startAyah + 1 }, (_, i) => startAyah + i).map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
    </div>

    <button
      className="btn btn-secondary"
      onClick={selectAll}
      style={{ width: '100%' }}
    >
      📜 Select Entire Surah ({currentSurah?.ayahCount} ayahs)
    </button>

    {ayahsLength > 0 && (
      <div className="preview-box">
        <div className="ayah-count">
          {endAyah - startAyah + 1} ayah{endAyah > startAyah ? 's' : ''} selected
          {tafsirAvailable && <span style={{ color: '#4CAF50' }}> • تفسير متاح</span>}
        </div>
        <p className="arabic">
          {arabicText.substring(0, 250)}{arabicText.length > 250 ? '...' : ''}
        </p>
        {textType === 'english' ? (
          <p className="translation">
            "{translationText.substring(0, 300)}{translationText.length > 300 ? '...' : ''}"
          </p>
        ) : (
          <p className="tafsir-text">
            {tafsirText.substring(0, 300)}{tafsirText.length > 300 ? '...' : ''}
          </p>
        )}
        <p className="reference">— {referenceText}</p>
      </div>
    )}
  </section>
);

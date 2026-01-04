/**
 * Main Application Component
 * Quran Ayah Canvas Generator
 */

const { useState, useEffect, useRef, useCallback, useMemo } = React;

// Import data
import { QURAN_DATA } from './data/quran-data.js';

// Import utilities
import { storage, createAyahMarker, wrapArabicText, wrapLTRText, calculateFontSizes, drawPattern, drawDecoration } from './utils/index.js';

// Import configuration
import { BACKGROUNDS, TEXT_COLORS, DECORATIONS, FORMATS, STORAGE_KEYS, FONTS } from './config/constants.js';

// Import components
import {
  Header,
  AyahSelector,
  TextTypeSelector,
  BackgroundSelector,
  TextStylePanel,
  DecorationSelector,
  PreviewArea,
  Gallery,
  ShareModal
} from './components/index.js';

// Extract data from QURAN_DATA safely
const surahInfo = QURAN_DATA?.surahs || [];
const quranAyahs = QURAN_DATA?.ayahs || {};
const quranTafsir = QURAN_DATA?.tafsir || {};

/**
 * Check if tafsir is available for a specific surah
 */
const hasTafsir = (surahNum) => {
  const tafsir = quranTafsir[surahNum];
  return Array.isArray(tafsir) && tafsir.length > 0;
};

function App() {
  // Navigation state
  const [activeTab, setActiveTab] = useState('create');

  // Ayah selection state
  const [surahNum, setSurahNum] = useState(1);
  const [startAyah, setStartAyah] = useState(1);
  const [endAyah, setEndAyah] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');

  // Background state
  const [bgCategory, setBgCategory] = useState('nature');
  const [background, setBackground] = useState(BACKGROUNDS.nature[0]);

  // Text styling state
  const [textColor, setTextColor] = useState('#FFFFFF');
  const [customColor, setCustomColor] = useState('#FFFFFF');
  const [arabicFontSize, setArabicFontSize] = useState(48);
  const [secondaryFontSize, setSecondaryFontSize] = useState(24);
  const [autoFitText, setAutoFitText] = useState(true);
  const [textPosition, setTextPosition] = useState('center');
  const [showArabic, setShowArabic] = useState(true);
  const [showSecondary, setShowSecondary] = useState(true);
  const [showReference, setShowReference] = useState(true);
  const [textType, setTextType] = useState('english');

  // Decoration state
  const [decoration, setDecoration] = useState('none');
  const [format, setFormat] = useState('square');

  // UI state
  const [showShareModal, setShowShareModal] = useState(false);
  const [savedDesigns, setSavedDesigns] = useState(() => storage.get(STORAGE_KEYS.SAVED_DESIGNS, []));

  // Refs
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const imageCache = useRef(new Map());

  // Persist saved designs to localStorage
  useEffect(() => {
    storage.set(STORAGE_KEYS.SAVED_DESIGNS, savedDesigns);
  }, [savedDesigns]);

  // Filtered surahs based on search
  const filteredSurahs = useMemo(() => {
    if (!searchTerm) return surahInfo;
    const term = searchTerm.toLowerCase();
    return surahInfo.filter(s =>
      s.name.toLowerCase().includes(term) ||
      s.arabicName.includes(searchTerm) ||
      String(s.number).includes(searchTerm)
    );
  }, [searchTerm]);

  // Current surah data
  const currentSurah = useMemo(() =>
    surahInfo.find(s => s.number === surahNum),
    [surahNum]
  );

  const ayahs = useMemo(() =>
    quranAyahs[surahNum] || [],
    [surahNum]
  );

  const tafsirAvailable = useMemo(() =>
    hasTafsir(surahNum),
    [surahNum]
  );

  // Reset ayah range when surah changes
  useEffect(() => {
    setStartAyah(1);
    setEndAyah(1);
  }, [surahNum]);

  // Switch to English if tafsir not available
  useEffect(() => {
    if (textType === 'tafsir' && !tafsirAvailable) {
      setTextType('english');
    }
  }, [tafsirAvailable, textType]);

  // Get selected ayahs
  const selectedAyahs = useMemo(() =>
    ayahs.filter(a => a.n >= startAyah && a.n <= endAyah),
    [ayahs, startAyah, endAyah]
  );

  // Generate Arabic text with ayah markers
  const arabicText = useMemo(() => {
    return selectedAyahs.map(a => {
      const text = a.a.trim();
      const marker = createAyahMarker(a.n);
      return text + marker;
    }).join(' ');
  }, [selectedAyahs]);

  // Generate translation text
  const translationText = useMemo(() =>
    selectedAyahs.map(a => a.t).join(' '),
    [selectedAyahs]
  );

  // Generate tafsir text
  const tafsirText = useMemo(() => {
    if (!tafsirAvailable) return '';
    const tafsirData = quranTafsir[surahNum];
    return selectedAyahs
      .map(a => tafsirData[a.n - 1] || '')
      .filter(t => t)
      .join(' ');
  }, [selectedAyahs, surahNum, tafsirAvailable]);

  // Get secondary text based on type
  const secondaryText = textType === 'tafsir' ? tafsirText : translationText;

  // Generate reference text
  const referenceText = useMemo(() => {
    if (!currentSurah) return '';
    return startAyah === endAyah
      ? `${currentSurah.name} ${startAyah}`
      : `${currentSurah.name} ${startAyah}-${endAyah}`;
  }, [currentSurah, startAyah, endAyah]);

  // Select random ayah
  const selectRandom = useCallback(() => {
    const randomSurah = surahInfo[Math.floor(Math.random() * surahInfo.length)];
    setSurahNum(randomSurah.number);
    const randomAyah = Math.floor(Math.random() * randomSurah.ayahCount) + 1;
    requestAnimationFrame(() => {
      setStartAyah(randomAyah);
      setEndAyah(randomAyah);
    });
  }, []);

  // Select entire surah
  const selectAll = useCallback(() => {
    if (currentSurah) {
      setStartAyah(1);
      setEndAyah(currentSurah.ayahCount);
    }
  }, [currentSurah]);

  // Handle custom background upload
  const handleUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setBackground({
        id: 'custom',
        type: 'custom',
        url: event.target.result
      });
    };
    reader.readAsDataURL(file);
  }, []);

  // Main canvas drawing function
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !ayahs.length) return;

    const ctx = canvas.getContext('2d');
    const size = FORMATS[format];
    canvas.width = size.w;
    canvas.height = size.h;

    const isTafsir = textType === 'tafsir';

    // Calculate font sizes
    let as = arabicFontSize;
    let ss = secondaryFontSize;
    if (autoFitText) {
      const calculated = calculateFontSizes(size.w, size.h, arabicText, secondaryText, isTafsir);
      as = calculated.arabicSize;
      ss = calculated.secondarySize;
    }

    // Draw content function
    const drawContent = () => {
      ctx.textAlign = 'center';
      const maxWidth = size.w * 0.85;
      const arabicLineHeight = as * 1.6;
      const secondaryLineHeight = ss * (isTafsir ? 1.8 : 1.5);

      // Wrap text
      ctx.font = `${as}px ${FONTS.arabic}`;
      const arabicLines = showArabic ? wrapArabicText(ctx, arabicText, maxWidth) : [];

      if (isTafsir) {
        ctx.font = `${ss}px ${FONTS.arabic}`;
      } else {
        ctx.font = `italic ${ss}px ${FONTS.english}`;
      }
      const secondaryLines = showSecondary
        ? (isTafsir ? wrapArabicText(ctx, secondaryText, maxWidth) : wrapLTRText(ctx, secondaryText, maxWidth * 0.95))
        : [];

      // Calculate total height
      let totalHeight = 0;
      if (showArabic) totalHeight += arabicLines.length * arabicLineHeight + 40;
      if (showSecondary) totalHeight += secondaryLines.length * secondaryLineHeight + 30;
      if (showReference) totalHeight += 40;

      // Calculate starting Y position
      let y;
      switch (textPosition) {
        case 'top': y = size.h * 0.12; break;
        case 'bottom': y = size.h - totalHeight - size.h * 0.08; break;
        default: y = (size.h - totalHeight) / 2;
      }

      // Apply text shadow
      ctx.shadowColor = 'rgba(0,0,0,0.8)';
      ctx.shadowBlur = 20;
      ctx.shadowOffsetX = 2;
      ctx.shadowOffsetY = 2;

      // Draw Arabic text
      if (showArabic) {
        ctx.font = `${as}px ${FONTS.arabic}`;
        ctx.fillStyle = textColor;
        arabicLines.forEach((line, i) => ctx.fillText(line, size.w / 2, y + i * arabicLineHeight));
        y += arabicLines.length * arabicLineHeight + 40;
      }

      // Draw secondary text
      if (showSecondary && secondaryText) {
        ctx.font = isTafsir ? `${ss}px ${FONTS.arabic}` : `italic ${ss}px ${FONTS.english}`;
        ctx.fillStyle = textColor;

        const quotedLines = [...secondaryLines];
        if (!isTafsir && quotedLines.length) {
          quotedLines[0] = '"' + quotedLines[0];
          quotedLines[quotedLines.length - 1] += '"';
        }

        quotedLines.forEach((line, i) => ctx.fillText(line, size.w / 2, y + i * secondaryLineHeight));
        y += secondaryLines.length * secondaryLineHeight + 30;
      }

      // Draw reference
      if (showReference) {
        ctx.font = `18px ${FONTS.english}`;
        ctx.fillStyle = textColor;
        ctx.globalAlpha = 0.9;
        const refText = isTafsir ? `— ${referenceText} (التفسير الميسر)` : `— ${referenceText}`;
        ctx.fillText(refText, size.w / 2, y + 10);
        ctx.globalAlpha = 1;
      }

      // Reset shadow
      ctx.shadowColor = 'transparent';
      ctx.shadowBlur = 0;

      // Draw decoration
      if (decoration !== 'none') {
        drawDecoration(ctx, size.w, size.h, decoration, textColor);
      }
    };

    // Draw background and content
    if (background.type === 'custom' && background.url) {
      let img = imageCache.current.get(background.url);
      if (img && img.complete) {
        const scale = Math.max(size.w / img.width, size.h / img.height);
        ctx.drawImage(img, (size.w - img.width * scale) / 2, (size.h - img.height * scale) / 2, img.width * scale, img.height * scale);
        ctx.fillStyle = 'rgba(0,0,0,0.4)';
        ctx.fillRect(0, 0, size.w, size.h);
        drawContent();
      } else {
        img = new Image();
        img.onload = () => {
          imageCache.current.set(background.url, img);
          const scale = Math.max(size.w / img.width, size.h / img.height);
          ctx.drawImage(img, (size.w - img.width * scale) / 2, (size.h - img.height * scale) / 2, img.width * scale, img.height * scale);
          ctx.fillStyle = 'rgba(0,0,0,0.4)';
          ctx.fillRect(0, 0, size.w, size.h);
          drawContent();
        };
        img.onerror = () => {
          ctx.fillStyle = '#1a1a2e';
          ctx.fillRect(0, 0, size.w, size.h);
          drawContent();
        };
        img.src = background.url;
      }
    } else {
      // Draw gradient background
      const gradient = ctx.createLinearGradient(0, 0, size.w, size.h);
      background.colors.forEach((color, i) => gradient.addColorStop(i / (background.colors.length - 1), color));
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, size.w, size.h);

      if (background.pattern) {
        drawPattern(ctx, size.w, size.h, background.pattern, '#C9A227');
      }

      drawContent();
    }
  }, [ayahs, format, textType, arabicFontSize, secondaryFontSize, autoFitText, arabicText, secondaryText, showArabic, showSecondary, showReference, textPosition, textColor, referenceText, decoration, background]);

  // Redraw canvas when dependencies change
  useEffect(() => { draw(); }, [draw]);

  // Download image
  const download = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement('a');
    link.download = `ayah-${referenceText.replace(/\s+/g, '-')}.png`;
    link.href = canvas.toDataURL('image/png', 1.0);
    link.click();
  }, [referenceText]);

  // Save design
  const saveDesign = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const newDesign = {
      id: Date.now(),
      thumb: canvas.toDataURL('image/png', 0.5),
      surahNum, startAyah, endAyah,
      settings: { bgCategory, background, textColor, arabicFontSize, secondaryFontSize, autoFitText, textPosition, showArabic, showSecondary, showReference, textType, decoration, format }
    };

    setSavedDesigns(prev => [...prev, newDesign]);
  }, [surahNum, startAyah, endAyah, bgCategory, background, textColor, arabicFontSize, secondaryFontSize, autoFitText, textPosition, showArabic, showSecondary, showReference, textType, decoration, format]);

  // Load saved design
  const loadDesign = useCallback((design) => {
    setSurahNum(design.surahNum);
    requestAnimationFrame(() => {
      setStartAyah(design.startAyah);
      setEndAyah(design.endAyah);
    });

    const s = design.settings;
    setBgCategory(s.bgCategory);
    setBackground(s.background);
    setTextColor(s.textColor);
    setArabicFontSize(s.arabicFontSize);
    setSecondaryFontSize(s.secondaryFontSize);
    setAutoFitText(s.autoFitText);
    setTextPosition(s.textPosition);
    setShowArabic(s.showArabic);
    setShowSecondary(s.showSecondary);
    setShowReference(s.showReference);
    setTextType(s.textType || 'english');
    setDecoration(s.decoration);
    setFormat(s.format);
    setActiveTab('create');
  }, []);

  // Delete saved design
  const deleteDesign = useCallback((id, e) => {
    e.stopPropagation();
    setSavedDesigns(prev => prev.filter(d => d.id !== id));
  }, []);

  const tafsirSurahs = Object.keys(quranTafsir).map(Number);

  return (
    <div className="app">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        savedDesignsCount={savedDesigns.length}
      />

      {activeTab === 'create' && (
        <main className="main">
          <aside className="panel">
            <AyahSelector
              surahInfo={surahInfo}
              surahNum={surahNum}
              setSurahNum={setSurahNum}
              startAyah={startAyah}
              setStartAyah={setStartAyah}
              endAyah={endAyah}
              setEndAyah={setEndAyah}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              filteredSurahs={filteredSurahs}
              currentSurah={currentSurah}
              selectRandom={selectRandom}
              selectAll={selectAll}
              hasTafsir={hasTafsir}
              tafsirAvailable={tafsirAvailable}
              arabicText={arabicText}
              translationText={translationText}
              tafsirText={tafsirText}
              textType={textType}
              referenceText={referenceText}
              ayahsLength={ayahs.length}
            />

            <TextTypeSelector
              textType={textType}
              setTextType={setTextType}
              tafsirAvailable={tafsirAvailable}
              tafsirSurahsCount={tafsirSurahs.length}
            />

            <BackgroundSelector
              backgrounds={BACKGROUNDS}
              bgCategory={bgCategory}
              setBgCategory={setBgCategory}
              background={background}
              setBackground={setBackground}
              fileInputRef={fileInputRef}
              handleUpload={handleUpload}
            />

            <TextStylePanel
              textColors={TEXT_COLORS}
              textColor={textColor}
              setTextColor={setTextColor}
              customColor={customColor}
              setCustomColor={setCustomColor}
              autoFitText={autoFitText}
              setAutoFitText={setAutoFitText}
              arabicFontSize={arabicFontSize}
              setArabicFontSize={setArabicFontSize}
              secondaryFontSize={secondaryFontSize}
              setSecondaryFontSize={setSecondaryFontSize}
              textPosition={textPosition}
              setTextPosition={setTextPosition}
              showArabic={showArabic}
              setShowArabic={setShowArabic}
              showSecondary={showSecondary}
              setShowSecondary={setShowSecondary}
              showReference={showReference}
              setShowReference={setShowReference}
              textType={textType}
            />

            <DecorationSelector
              decorations={DECORATIONS}
              decoration={decoration}
              setDecoration={setDecoration}
            />
          </aside>

          <PreviewArea
            canvasRef={canvasRef}
            formats={FORMATS}
            format={format}
            setFormat={setFormat}
            download={download}
            setShowShareModal={setShowShareModal}
            saveDesign={saveDesign}
          />
        </main>
      )}

      {activeTab === 'saved' && (
        <Gallery
          savedDesigns={savedDesigns}
          surahInfo={surahInfo}
          loadDesign={loadDesign}
          deleteDesign={deleteDesign}
          setActiveTab={setActiveTab}
        />
      )}

      <ShareModal
        showShareModal={showShareModal}
        setShowShareModal={setShowShareModal}
        download={download}
        translationText={translationText}
        referenceText={referenceText}
      />
    </div>
  );
}

// Export for use in index.html
window.App = App;

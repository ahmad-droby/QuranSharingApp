/**
 * Quran API Service
 * Fetches Quran data from AlQuran.cloud API
 * https://alquran.cloud/api
 */

const API_BASE = 'https://api.alquran.cloud/v1';

// Cache key for localStorage
const CACHE_KEY = 'quran_data_cache';
const CACHE_VERSION = '1.0';

/**
 * Get cached data if available and valid
 */
const getCachedData = () => {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (cached) {
      const parsed = JSON.parse(cached);
      if (parsed.version === CACHE_VERSION && parsed.data) {
        return parsed.data;
      }
    }
  } catch (e) {
    console.warn('Cache read error:', e);
  }
  return null;
};

/**
 * Save data to cache
 */
const setCachedData = (data) => {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      version: CACHE_VERSION,
      timestamp: Date.now(),
      data
    }));
  } catch (e) {
    console.warn('Cache write error:', e);
  }
};

/**
 * Fetch all surahs metadata
 */
const fetchSurahList = async () => {
  const response = await fetch(`${API_BASE}/surah`);
  if (!response.ok) throw new Error('Failed to fetch surah list');
  const result = await response.json();
  return result.data;
};

/**
 * Fetch Arabic text for entire Quran (Uthmani script)
 */
const fetchArabicQuran = async () => {
  const response = await fetch(`${API_BASE}/quran/quran-uthmani`);
  if (!response.ok) throw new Error('Failed to fetch Arabic Quran');
  const result = await response.json();
  return result.data.surahs;
};

/**
 * Fetch English translation (Sahih International)
 */
const fetchEnglishTranslation = async () => {
  const response = await fetch(`${API_BASE}/quran/en.sahih`);
  if (!response.ok) throw new Error('Failed to fetch English translation');
  const result = await response.json();
  return result.data.surahs;
};

/**
 * Fetch Arabic Tafsir (if available)
 * Using ar.muyassar (التفسير الميسر)
 */
const fetchArabicTafsir = async () => {
  try {
    const response = await fetch(`${API_BASE}/quran/ar.muyassar`);
    if (!response.ok) return null;
    const result = await response.json();
    return result.data.surahs;
  } catch (e) {
    console.warn('Tafsir not available:', e);
    return null;
  }
};

/**
 * Transform API data into app format
 */
const transformData = (arabicSurahs, englishSurahs, tafsirSurahs) => {
  const surahs = [];
  const ayahs = {};
  const tafsir = {};

  arabicSurahs.forEach((surah, index) => {
    const englishSurah = englishSurahs[index];
    const tafsirSurah = tafsirSurahs ? tafsirSurahs[index] : null;

    // Surah metadata
    surahs.push({
      number: surah.number,
      name: surah.englishName,
      arabicName: surah.name,
      englishNameTranslation: surah.englishNameTranslation,
      ayahCount: surah.numberOfAyahs,
      revelationType: surah.revelationType
    });

    // Ayahs for this surah
    ayahs[surah.number] = surah.ayahs.map((ayah, ayahIndex) => ({
      n: ayah.numberInSurah,
      a: ayah.text, // Arabic text
      t: englishSurah.ayahs[ayahIndex]?.text || '' // English translation
    }));

    // Tafsir for this surah (if available)
    if (tafsirSurah && tafsirSurah.ayahs) {
      tafsir[surah.number] = tafsirSurah.ayahs.map(ayah => ayah.text);
    }
  });

  return { surahs, ayahs, tafsir };
};

/**
 * Fetch complete Quran data
 * Returns cached data if available, otherwise fetches from API
 */
export const fetchQuranData = async (forceRefresh = false) => {
  // Check cache first
  if (!forceRefresh) {
    const cached = getCachedData();
    if (cached) {
      console.log('Using cached Quran data');
      return cached;
    }
  }

  console.log('Fetching Quran data from API...');

  // Fetch all data in parallel
  const [arabicSurahs, englishSurahs, tafsirSurahs] = await Promise.all([
    fetchArabicQuran(),
    fetchEnglishTranslation(),
    fetchArabicTafsir()
  ]);

  // Transform to app format
  const data = transformData(arabicSurahs, englishSurahs, tafsirSurahs);

  // Cache the data
  setCachedData(data);

  console.log('Quran data loaded:', data.surahs.length, 'surahs');
  return data;
};

/**
 * Clear cached data
 */
export const clearCache = () => {
  try {
    localStorage.removeItem(CACHE_KEY);
    console.log('Quran cache cleared');
  } catch (e) {
    console.warn('Failed to clear cache:', e);
  }
};

export default {
  fetchQuranData,
  clearCache
};

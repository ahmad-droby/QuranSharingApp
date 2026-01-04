/**
 * Application constants and configuration
 */

// Background presets
export const BACKGROUNDS = {
  nature: [
    { id: 'n1', name: 'Sunset', colors: ['#1a1a2e', '#16213e', '#0f3460', '#533483'] },
    { id: 'n2', name: 'Ocean', colors: ['#0c2461', '#1e3799', '#4a69bd', '#6a89cc'] },
    { id: 'n3', name: 'Forest', colors: ['#0a3d62', '#1e5f74', '#133b5c', '#1d566e'] },
    { id: 'n4', name: 'Mountain', colors: ['#2c2c54', '#474787', '#706fd3', '#40407a'] },
    { id: 'n5', name: 'Desert', colors: ['#8B4513', '#CD853F', '#DEB887', '#D2691E'] },
  ],
  islamic: [
    { id: 'i1', name: 'Royal', colors: ['#1a1a2e', '#0f3460', '#16213e'], pattern: 'geometric' },
    { id: 'i2', name: 'Emerald', colors: ['#0a3d62', '#1e5f74', '#2c786c'], pattern: 'arabesque' },
    { id: 'i3', name: 'Golden', colors: ['#2d132c', '#801336', '#c72c41'], pattern: 'star' },
    { id: 'i4', name: 'Midnight', colors: ['#1a1a2e', '#16213e', '#533483'], pattern: 'lattice' },
  ],
  abstract: [
    { id: 'a1', name: 'Purple', colors: ['#667eea', '#764ba2', '#f77062'] },
    { id: 'a2', name: 'Teal', colors: ['#11998e', '#38ef7d', '#1a535c'] },
    { id: 'a3', name: 'Rose', colors: ['#f5af19', '#f12711', '#e8d5b7'] },
    { id: 'a4', name: 'Aurora', colors: ['#43cea2', '#185a9d', '#43cea2'] },
  ],
  solid: [
    { id: 's1', name: 'Navy', colors: ['#1A1A2E', '#16213E'] },
    { id: 's2', name: 'Charcoal', colors: ['#2D2D2D', '#1A1A1A'] },
    { id: 's3', name: 'Blue', colors: ['#0F3460', '#16213E'] },
    { id: 's4', name: 'Purple', colors: ['#4A1942', '#1A1A2E'] },
    { id: 's5', name: 'Green', colors: ['#1B4332', '#081C15'] },
  ]
};

// Text color presets
export const TEXT_COLORS = [
  '#FFFFFF', '#C9A227', '#E8D48A', '#F5F5DC', '#87CEEB',
  '#FFB6C1', '#98FB98', '#DDA0DD', '#F0E68C', '#B0C4DE'
];

// Decoration styles
export const DECORATIONS = [
  { id: 'none', name: 'None' },
  { id: 'border', name: 'Border' },
  { id: 'frame', name: 'Frame' },
  { id: 'vignette', name: 'Vignette' },
  { id: 'ornament', name: 'Ornament' },
  { id: 'corners', name: 'Corners' }
];

// Export format dimensions
export const FORMATS = {
  square: { w: 1080, h: 1080, label: 'Square' },
  portrait: { w: 1080, h: 1350, label: 'Portrait' },
  story: { w: 1080, h: 1920, label: 'Story' }
};

// Storage keys
export const STORAGE_KEYS = {
  SAVED_DESIGNS: 'ayahCanvas_saved'
};

// Font families
export const FONTS = {
  arabic: "'Scheherazade New', 'Amiri', serif",
  english: "'Poppins', sans-serif"
};

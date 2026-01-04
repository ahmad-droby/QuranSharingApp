/**
 * Arabic text utilities
 */

const ARABIC_NUMERALS = '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669';

/**
 * Convert Western numerals to Arabic numerals
 */
export const toArabicNumeral = (n) => {
  return String(n)
    .split('')
    .map(digit => ARABIC_NUMERALS[parseInt(digit)] || digit)
    .join('');
};

/**
 * Create ayah end marker with Arabic numerals
 * Uses U+06DD (۝) - the proper Unicode "Arabic End of Ayah" character
 * This character is designed to hold digits and renders as a single unit
 */
export const createAyahMarker = (n) => `\u06DD${toArabicNumeral(n)}`;

/**
 * Wrap Arabic (RTL) text to fit within max width
 * Keeps ayah markers together with the preceding word as a single unit
 */
export const wrapArabicText = (ctx, text, maxWidth) => {
  // Split into tokens, keeping word+marker together as single units
  // U+06DD is the Arabic End of Ayah character which holds digits
  const tokenRegex = /\S+\u06DD[\u0660-\u0669]+|\S+/g;
  const tokens = text.match(tokenRegex) || [];

  const lines = [];
  let currentLine = '';

  for (const token of tokens) {
    const testLine = currentLine ? currentLine + ' ' + token : token;
    const testWidth = ctx.measureText(testLine).width;

    if (testWidth > maxWidth && currentLine !== '') {
      lines.push(currentLine);
      currentLine = token;
    } else {
      currentLine = testLine;
    }
  }

  if (currentLine) {
    lines.push(currentLine);
  }

  return lines.filter(line => line.trim());
};

/**
 * Wrap LTR (English) text to fit within max width
 */
export const wrapLTRText = (ctx, text, maxWidth) => {
  const words = text.split(' ');
  const lines = [];
  let currentLine = '';

  for (const word of words) {
    const testLine = currentLine + word + ' ';
    if (ctx.measureText(testLine).width > maxWidth && currentLine !== '') {
      lines.push(currentLine.trim());
      currentLine = word + ' ';
    } else {
      currentLine = testLine;
    }
  }

  if (currentLine.trim()) {
    lines.push(currentLine.trim());
  }

  return lines;
};

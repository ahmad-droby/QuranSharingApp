/**
 * Canvas drawing utilities
 */

/**
 * Calculate optimal font sizes based on content length
 */
export const calculateFontSizes = (width, height, arabicText, secondaryText, isTafsir) => {
  const arabicLength = arabicText.length;
  const secondaryLength = secondaryText.length;

  // Arabic text sizing
  let arabicSize;
  if (arabicLength > 800) arabicSize = 22;
  else if (arabicLength > 600) arabicSize = 26;
  else if (arabicLength > 400) arabicSize = 30;
  else if (arabicLength > 300) arabicSize = 34;
  else if (arabicLength > 200) arabicSize = 38;
  else if (arabicLength > 100) arabicSize = 44;
  else arabicSize = 50;

  // Secondary text sizing
  let secondarySize;
  if (isTafsir) {
    if (secondaryLength > 800) secondarySize = 18;
    else if (secondaryLength > 500) secondarySize = 22;
    else if (secondaryLength > 300) secondarySize = 26;
    else if (secondaryLength > 150) secondarySize = 30;
    else secondarySize = 34;
  } else {
    if (secondaryLength > 1000) secondarySize = 12;
    else if (secondaryLength > 800) secondarySize = 14;
    else if (secondaryLength > 500) secondarySize = 16;
    else if (secondaryLength > 300) secondarySize = 18;
    else if (secondaryLength > 150) secondarySize = 20;
    else secondarySize = 24;
  }

  // Adjust for portrait formats
  if (height > width) {
    arabicSize = Math.min(arabicSize + 4, 54);
    secondarySize = Math.min(secondarySize + (isTafsir ? 3 : 2), isTafsir ? 38 : 26);
  }

  return { arabicSize, secondarySize };
};

/**
 * Draw decorative Islamic patterns
 */
export const drawPattern = (ctx, width, height, pattern, color) => {
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.globalAlpha = 0.15;

  const spacing = pattern === 'star' ? 100 : pattern === 'arabesque' ? 80 : pattern === 'geometric' ? 60 : 40;

  switch (pattern) {
    case 'geometric':
      for (let x = 0; x < width + spacing; x += spacing) {
        for (let y = 0; y < height + spacing; y += spacing) {
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(x + spacing / 2, y + spacing / 2);
          ctx.lineTo(x, y + spacing);
          ctx.lineTo(x - spacing / 2, y + spacing / 2);
          ctx.closePath();
          ctx.stroke();
        }
      }
      break;

    case 'arabesque':
      for (let x = 0; x < width + spacing; x += spacing) {
        for (let y = 0; y < height + spacing; y += spacing) {
          ctx.beginPath();
          ctx.arc(x, y, spacing / 3, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
      break;

    case 'star':
      for (let x = spacing / 2; x < width; x += spacing) {
        for (let y = spacing / 2; y < height; y += spacing) {
          ctx.beginPath();
          for (let i = 0; i < 8; i++) {
            const angle = (i * Math.PI) / 4;
            const radius = i % 2 === 0 ? spacing / 3 : spacing / 6;
            const px = x + Math.cos(angle) * radius;
            const py = y + Math.sin(angle) * radius;
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
          }
          ctx.closePath();
          ctx.stroke();
        }
      }
      break;

    case 'lattice':
      for (let x = 0; x < width + spacing; x += spacing) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height + spacing; y += spacing) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }
      break;
  }

  ctx.globalAlpha = 1;
};

/**
 * Draw border decorations
 */
export const drawDecoration = (ctx, width, height, decoration, color) => {
  ctx.strokeStyle = color;
  ctx.lineWidth = 3;
  ctx.globalAlpha = 0.8;

  switch (decoration) {
    case 'border':
      ctx.strokeRect(40, 40, width - 80, height - 80);
      break;

    case 'frame':
      ctx.strokeRect(30, 30, width - 60, height - 60);
      ctx.lineWidth = 1;
      ctx.strokeRect(45, 45, width - 90, height - 90);
      break;

    case 'vignette':
      const gradient = ctx.createRadialGradient(
        width / 2, height / 2, width * 0.3,
        width / 2, height / 2, width * 0.8
      );
      gradient.addColorStop(0, 'rgba(0,0,0,0)');
      gradient.addColorStop(1, 'rgba(0,0,0,0.7)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);
      break;

    case 'ornament':
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(width / 2 - 150, 80);
      ctx.quadraticCurveTo(width / 2 - 75, 50, width / 2, 60);
      ctx.quadraticCurveTo(width / 2 + 75, 50, width / 2 + 150, 80);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(width / 2 - 150, height - 80);
      ctx.quadraticCurveTo(width / 2 - 75, height - 50, width / 2, height - 60);
      ctx.quadraticCurveTo(width / 2 + 75, height - 50, width / 2 + 150, height - 80);
      ctx.stroke();
      break;

    case 'corners':
      const cs = 60;
      const corners = [
        [30, 30 + cs, 30, 30, 30 + cs, 30],
        [width - 30 - cs, 30, width - 30, 30, width - 30, 30 + cs],
        [30, height - 30 - cs, 30, height - 30, 30 + cs, height - 30],
        [width - 30 - cs, height - 30, width - 30, height - 30, width - 30, height - 30 - cs]
      ];
      corners.forEach(([x1, y1, x2, y2, x3, y3]) => {
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.lineTo(x3, y3);
        ctx.stroke();
      });
      break;
  }

  ctx.globalAlpha = 1;
};

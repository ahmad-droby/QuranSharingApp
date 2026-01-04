# Ayah Canvas - Quran Post Generator

A beautiful web application for creating shareable Quran verse images and videos with customizable backgrounds, translations, tafsir, and audio recitations.

## Features

### Image Generation
- **Multiple Formats**: Support for Instagram Post (1080x1080), Instagram Story (1080x1920), Twitter/X Post (1200x675), Facebook Post (1200x630), and WhatsApp Status (1080x1920)
- **Beautiful Backgrounds**: Choose from solid colors, gradients, NASA Astronomy Picture of the Day, or random nature images from Picsum
- **Custom Backgrounds**: Upload your own images
- **Arabic Text**: Display Quranic verses in beautiful Arabic typography (Scheherazade New, Amiri fonts)
- **Translations**: Multiple language translations available
- **Tafsir**: Islamic commentary/explanation from various scholars
- **Text Positioning**: Flexible text placement (center, top, bottom)
- **Decorative Elements**: Optional Islamic decorative borders
- **Auto-fit Text**: Automatically adjusts font sizes for optimal display

### Video Generation
- **Multi-Ayah Videos**: Create videos with multiple verses
- **Smooth Transitions**: Fade, slide (left/right/up), zoom, or cut transitions between verses
- **Audio Recitation**: Include audio from popular Quran reciters:
  - Mishary Rashid Alafasy
  - Abdul Basit Abdul Samad
  - Abdurrahmaan As-Sudais
  - Mahmoud Khalil Al-Husary
  - Mohamed Siddiq El-Minshawi
- **Precise Audio Sync**: Uses Quran.com API for millisecond-accurate audio-text synchronization
- **Preview & Download**: Preview videos before downloading

### Data Sources
- **Quran Text**: Al-Quran Cloud API
- **Translations**: Multiple languages via Al-Quran Cloud
- **Tafsir**: Various tafsir sources via Al-Quran Cloud
- **Audio**: Islamic Network CDN with timing data from Quran.com API
- **Backgrounds**: NASA APOD API, Picsum Photos API

## Deployment

### Option 1: Static File (Simplest)

The app is a single HTML file with all dependencies loaded from CDNs. Simply:

1. Open `public/index.html` directly in a modern web browser
2. Or serve it from any static file server

**Note**: When opening directly from file system (`file://`), audio features use CORS proxies automatically.

### Option 2: Local Development Server

Using Python:
```bash
cd public
python -m http.server 8000
# Open http://localhost:8000
```

Using Node.js:
```bash
npx serve public
# Or
npx http-server public
```

Using PHP:
```bash
cd public
php -S localhost:8000
```

### Option 3: Deploy to GitHub Pages

1. Fork this repository
2. Go to Settings > Pages
3. Select "Deploy from a branch"
4. Choose `main` branch and `/public` folder (or root if you move index.html)
5. Your app will be available at `https://yourusername.github.io/QuranSharingApp/public/`

### Option 4: Deploy to Netlify/Vercel

**Netlify:**
1. Connect your GitHub repository
2. Set build command: (leave empty)
3. Set publish directory: `public`
4. Deploy

**Vercel:**
1. Import your GitHub repository
2. Framework Preset: Other
3. Root Directory: `public`
4. Deploy

### Option 5: Deploy to Cloudflare Pages

1. Connect your GitHub repository
2. Build command: (leave empty)
3. Build output directory: `public`
4. Deploy

## Usage Guide

### Creating an Image

1. **Select Surah**: Use the dropdown to choose a Surah (chapter)
2. **Select Ayah(s)**:
   - Single ayah: Select start ayah only
   - Multiple ayahs: Select start and end ayah range
3. **Choose Content Type**:
   - Translation: Shows Arabic + selected translation
   - Tafsir: Shows Arabic + scholarly commentary
4. **Customize Appearance**:
   - Select background (color, gradient, NASA image, nature photo, or custom)
   - Choose text color
   - Set text position (center, top, bottom)
   - Toggle Arabic text, secondary text, and reference display
   - Enable/disable decorative borders
   - Select output format (Instagram, Twitter, etc.)
5. **Generate & Download**: Click the download button to save your image

### Creating a Video

1. **Select Multiple Ayahs**: Choose a range of verses (start to end)
2. **Switch to Video Mode**: Toggle from Image to Video output
3. **Configure Video Options**:
   - **Transition**: Choose how verses transition (fade, slide, zoom, cut)
   - **Audio**: Enable/disable recitation audio
   - **Reciter**: Select your preferred Quran reciter
4. **Generate Video**: Click generate and wait for processing
5. **Preview**: Watch the video preview in the modal
6. **Download**: Save the video as WebM format

### Tips

- **Long Verses**: Enable "Auto-fit text" for automatic font size adjustment
- **Video Length**: Each verse displays for the exact duration of its audio recitation
- **Background Images**: NASA APOD and Picsum images are fetched fresh - click refresh for new images
- **Custom Colors**: Use the color picker for precise text and background colors
- **Sharing**: Generated images/videos are optimized for social media platforms

## Project Structure

```
QuranSharingApp/
├── public/
│   └── index.html      # Main application (single-file React app)
├── src/
│   ├── styles/
│   │   └── main.css    # Application styles
│   ├── components/     # (Optional) React components
│   ├── services/       # (Optional) API services
│   ├── data/           # (Optional) Static data
│   └── utils/          # (Optional) Utility functions
└── README.md
```

## Technologies Used

- **React 18** - UI framework (loaded via CDN)
- **Babel** - JSX transformation (loaded via CDN)
- **Canvas API** - Image generation
- **MediaRecorder API** - Video recording
- **Web Audio API** - Audio processing and synchronization

## APIs Used

- [Al-Quran Cloud API](https://alquran.cloud/api) - Quran text, translations, tafsir
- [Quran.com API](https://api.quran.com) - Precise audio timing data
- [Islamic Network CDN](https://cdn.islamic.network) - Audio recitations
- [NASA APOD API](https://api.nasa.gov) - Astronomy pictures
- [Picsum Photos](https://picsum.photos) - Random nature images

## Browser Support

- Chrome 80+ (recommended)
- Firefox 75+
- Safari 14+
- Edge 80+

**Note**: Video generation with audio requires a modern browser with MediaRecorder and Web Audio API support.

## License

This project is open source and available for personal and educational use.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Acknowledgments

- Quran data provided by [Al-Quran Cloud](https://alquran.cloud)
- Audio timing data from [Quran.com](https://quran.com)
- Audio recitations from [Islamic Network](https://islamic.network)
- Background images from [NASA](https://nasa.gov) and [Picsum](https://picsum.photos)

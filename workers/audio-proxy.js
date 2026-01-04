/**
 * Cloudflare Worker - Audio CORS Proxy
 *
 * Deploy this worker to Cloudflare and use it to proxy audio requests
 * This bypasses CORS restrictions for the Quran audio CDN
 *
 * Setup:
 * 1. Go to Cloudflare Dashboard > Workers & Pages > Create Worker
 * 2. Paste this code and deploy
 * 3. Note your worker URL (e.g., audio-proxy.yourusername.workers.dev)
 * 4. Update CORS_PROXIES in index.html to use your worker URL
 */

export default {
  async fetch(request) {
    // Get the URL to proxy from query parameter
    const url = new URL(request.url);
    const targetUrl = url.searchParams.get('url');

    if (!targetUrl) {
      return new Response('Missing url parameter', { status: 400 });
    }

    // Only allow proxying from trusted audio CDNs
    const allowedDomains = [
      'cdn.islamic.network',
      'download.quranicaudio.com',
      'verses.quran.com',
      'audio.qurancdn.com'
    ];

    const targetHostname = new URL(targetUrl).hostname;
    if (!allowedDomains.some(domain => targetHostname.includes(domain))) {
      return new Response('Domain not allowed', { status: 403 });
    }

    try {
      // Fetch the audio file
      const response = await fetch(targetUrl, {
        headers: {
          'User-Agent': 'QuranSharingApp/1.0'
        }
      });

      if (!response.ok) {
        return new Response(`Upstream error: ${response.status}`, { status: response.status });
      }

      // Create new response with CORS headers
      const newResponse = new Response(response.body, {
        status: response.status,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Content-Type': response.headers.get('Content-Type') || 'audio/mpeg',
          'Cache-Control': 'public, max-age=86400' // Cache for 24 hours
        }
      });

      return newResponse;
    } catch (error) {
      return new Response(`Proxy error: ${error.message}`, { status: 500 });
    }
  }
};

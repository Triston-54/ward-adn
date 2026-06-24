
  const WardData = {
    loadContent,
    preloadContent,
    safeSample,
    shuffleArray,
    jsonResponse,
    textResponse,
    MODULES,
    Microbiology,
    Terminology,
    Dosage,
    Assessment,
    MentalHealth,
    Pathophysiology,
    MaternalChild,
    Verify,
    Audit,
    handleApiRequest,
  };

  function installFetchInterceptor() {
    _nativeFetch = global.fetch.bind(global);
    global.fetch = async function wardFetch(input, init = {}) {
      const url = typeof input === 'string' ? input : input.url;
      try {
        const parsed = new URL(url, global.location?.origin || 'http://localhost');
        if (parsed.pathname.startsWith('/api/')) {
          return WardData.handleApiRequest(parsed.pathname + parsed.search, init);
        }
      } catch { /* relative or opaque URL — fall through to native fetch */ }
      return _nativeFetch(input, init);
    };
  }

  global.WardData = WardData;
  installFetchInterceptor();
})(typeof window !== 'undefined' ? window : globalThis);
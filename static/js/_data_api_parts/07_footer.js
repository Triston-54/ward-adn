
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
      let pathname = url;
      try { pathname = new URL(url, global.location?.origin || 'http://localhost').pathname; } catch { /* */ }
      if (pathname.startsWith('/api/')) return WardData.handleApiRequest(pathname, init);
      return _nativeFetch(input, init);
    };
  }

  global.WardData = WardData;
  installFetchInterceptor();
})(typeof window !== 'undefined' ? window : globalThis);
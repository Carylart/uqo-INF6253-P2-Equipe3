const CACHE_DURATION = 24 * 60 * 60 * 1000;

async function getCachedData(key) {
  const result = await chrome.storage.local.get(key);
  if (result[key]) {
    const cached = result[key];
    if (Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.data;
    }
  }
  return null;
}

async function setCachedData(key, data) {
  const cacheEntry = {
    data: data,
    timestamp: Date.now()
  };
  await chrome.storage.local.set({ [key]: cacheEntry });
}

async function fetchFromAPI(endpoint, apiUrl) {
  const url = `${apiUrl}${endpoint}`;
  console.log('Fetching from API:', url);
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API fetch error:', error);
    throw error;
  }
}

async function getTermDiff(goId, apiUrl, cacheEnabled) {
  const cacheKey = `diff_${goId}`;
  
  if (cacheEnabled) {
    const cached = await getCachedData(cacheKey);
    if (cached) {
      console.log('Returning cached data for', goId);
      return cached;
    }
  }
  
  try {
    const data = await fetchFromAPI(`/api/term/${goId}/diff`, apiUrl);
    
    if (cacheEnabled) {
      await setCachedData(cacheKey, data);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching term diff:', error);
    return {
      go_id: goId,
      error: error.message,
      has_changes: false,
      is_deprecated: false,
      is_new: false
    };
  }
}

async function getTermInfo(goId, apiUrl, cacheEnabled) {
  const cacheKey = `term_${goId}`;
  
  if (cacheEnabled) {
    const cached = await getCachedData(cacheKey);
    if (cached) {
      return cached;
    }
  }
  
  try {
    const data = await fetchFromAPI(`/api/term/${goId}`, apiUrl);
    
    if (cacheEnabled) {
      await setCachedData(cacheKey, data);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching term info:', error);
    return null;
  }
}

async function getDomainStats(domainId, apiUrl, cacheEnabled) {
  const cacheKey = `stats_${domainId}`;
  
  if (cacheEnabled) {
    const cached = await getCachedData(cacheKey);
    if (cached) {
      return cached;
    }
  }
  
  try {
    const data = await fetchFromAPI(`/api/domain/${domainId}/stats`, apiUrl);
    
    if (cacheEnabled) {
      await setCachedData(cacheKey, data);
    }
    
    return data;
  } catch (error) {
    console.error('Error fetching domain stats:', error);
    return null;
  }
}

async function searchTerms(query, apiUrl) {
  try {
    const encodedQuery = encodeURIComponent(query);
    return await fetchFromAPI(`/api/search?q=${encodedQuery}`, apiUrl);
  } catch (error) {
    console.error('Error searching terms:', error);
    return [];
  }
}

async function clearCache() {
  await chrome.storage.local.clear();
  console.log('Cache cleared');
}

async function getCacheStats() {
  const allData = await chrome.storage.local.get(null);
  const keys = Object.keys(allData);
  
  let totalSize = 0;
  let validEntries = 0;
  let expiredEntries = 0;
  
  for (const key of keys) {
    const entry = allData[key];
    const size = JSON.stringify(entry).length;
    totalSize += size;
    
    if (Date.now() - entry.timestamp < CACHE_DURATION) {
      validEntries++;
    } else {
      expiredEntries++;
    }
  }
  
  return {
    totalEntries: keys.length,
    validEntries: validEntries,
    expiredEntries: expiredEntries,
    totalSize: totalSize,
    totalSizeKB: (totalSize / 1024).toFixed(2)
  };
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'fetchTermDiff') {
    getTermDiff(request.goId, request.apiUrl, request.cacheEnabled)
      .then(sendResponse);
    return true;
  }
  
  if (request.action === 'fetchTermInfo') {
    getTermInfo(request.goId, request.apiUrl, request.cacheEnabled)
      .then(sendResponse);
    return true;
  }
  
  if (request.action === 'fetchDomainStats') {
    getDomainStats(request.domainId, request.apiUrl, request.cacheEnabled)
      .then(sendResponse);
    return true;
  }
  
  if (request.action === 'searchTerms') {
    searchTerms(request.query, request.apiUrl)
      .then(sendResponse);
    return true;
  }
  
  if (request.action === 'clearCache') {
    clearCache().then(() => sendResponse({ success: true }));
    return true;
  }
  
  if (request.action === 'getCacheStats') {
    getCacheStats().then(sendResponse);
    return true;
  }
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.sync.set({
    apiUrl: 'http://localhost:8000',
    domain: 'GO:0012501',
    cacheEnabled: true
  });
  console.log('GO Evolution Tracker installed');
});

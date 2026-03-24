document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  await updateCacheStats();
  
  document.getElementById('saveSettings').addEventListener('click', saveSettings);
  document.getElementById('clearCache').addEventListener('click', clearCache);
  document.getElementById('testConnection').addEventListener('click', testConnection);
});

async function loadSettings() {
  const settings = await chrome.storage.sync.get({
    apiUrl: 'http://localhost:8000',
    domain: 'GO:0012501',
    cacheEnabled: true
  });
  
  document.getElementById('apiUrl').value = settings.apiUrl;
  document.getElementById('domain').value = settings.domain;
  document.getElementById('cacheEnabled').checked = settings.cacheEnabled;
}

async function saveSettings() {
  const apiUrl = document.getElementById('apiUrl').value.trim();
  const domain = document.getElementById('domain').value;
  const cacheEnabled = document.getElementById('cacheEnabled').checked;
  
  if (!apiUrl) {
    showMessage('Veuillez entrer une URL valide', 'error');
    return;
  }
  
  await chrome.storage.sync.set({
    apiUrl: apiUrl,
    domain: domain,
    cacheEnabled: cacheEnabled
  });
  
  showMessage('Paramètres enregistrés avec succès!', 'success');
}

function showMessage(text, type) {
  const messageEl = document.getElementById('saveMessage');
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
  
  setTimeout(() => {
    messageEl.className = 'message';
  }, 3000);
}

async function updateCacheStats() {
  try {
    const stats = await chrome.runtime.sendMessage({ action: 'getCacheStats' });
    
    document.getElementById('totalEntries').textContent = stats.totalEntries;
    document.getElementById('validEntries').textContent = stats.validEntries;
    document.getElementById('expiredEntries').textContent = stats.expiredEntries;
    document.getElementById('cacheSize').textContent = stats.totalSizeKB;
  } catch (error) {
    console.error('Error getting cache stats:', error);
  }
}

async function clearCache() {
  if (confirm('Êtes-vous sûr de vouloir vider le cache?')) {
    try {
      await chrome.runtime.sendMessage({ action: 'clearCache' });
      await updateCacheStats();
      showMessage('Cache vidé avec succès!', 'success');
    } catch (error) {
      showMessage('Erreur lors du vidage du cache', 'error');
    }
  }
}

async function testConnection() {
  const goId = document.getElementById('testGoId').value.trim();
  const resultEl = document.getElementById('testResult');
  
  if (!goId) {
    resultEl.className = 'test-result error';
    resultEl.textContent = 'Veuillez entrer un identifiant GO';
    return;
  }
  
  if (!goId.match(/^GO:\d{7}$/)) {
    resultEl.className = 'test-result error';
    resultEl.textContent = 'Format invalide. Utilisez le format GO:XXXXXXX';
    return;
  }
  
  resultEl.className = 'test-result';
  resultEl.textContent = 'Test en cours...';
  
  try {
    const settings = await chrome.storage.sync.get({
      apiUrl: 'http://localhost:8000',
      cacheEnabled: false
    });
    
    const response = await chrome.runtime.sendMessage({
      action: 'fetchTermDiff',
      goId: goId,
      apiUrl: settings.apiUrl,
      cacheEnabled: false
    });
    
    if (response && !response.error) {
      resultEl.className = 'test-result success';
      resultEl.innerHTML = `
        <strong>✓ Connexion réussie!</strong>
        <pre>${JSON.stringify(response, null, 2)}</pre>
      `;
    } else {
      resultEl.className = 'test-result error';
      resultEl.textContent = `✗ Erreur: ${response.error || 'Réponse invalide'}`;
    }
  } catch (error) {
    resultEl.className = 'test-result error';
    resultEl.textContent = `✗ Erreur de connexion: ${error.message}`;
  }
}

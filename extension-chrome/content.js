const GO_ID_PATTERNS = [
  /GO[:_](\d{7})/gi,
  /term\/GO[:_](\d{7})/gi
];

function extractGOId() {
  const url = window.location.href;
  
  for (const pattern of GO_ID_PATTERNS) {
    const match = url.match(pattern);
    if (match) {
      const goId = match[0].replace(/[:_]/g, ':').replace('term/', '');
      return goId.startsWith('GO:') ? goId : `GO:${goId}`;
    }
  }
  
  const bodyText = document.body.innerText;
  const bodyMatch = bodyText.match(/GO[:_]\d{7}/i);
  if (bodyMatch) {
    return bodyMatch[0].replace('_', ':');
  }
  
  return null;
}

function createBadge(status, goId) {
  const badge = document.createElement('div');
  badge.id = 'go-evolution-badge';
  badge.className = `go-badge go-badge-${status.toLowerCase()}`;
  
  const statusText = {
    'stable': 'Stable',
    'modified': 'Modifié',
    'deprecated': 'Déprécié',
    'new': 'Nouveau'
  }[status.toLowerCase()] || 'Inconnu';
  
  badge.innerHTML = `
    <div class="go-badge-header">
      <span class="go-badge-icon">🔬</span>
      <span class="go-badge-title">GO Evolution Tracker</span>
      <button class="go-badge-close" id="go-badge-close">×</button>
    </div>
    <div class="go-badge-content">
      <div class="go-badge-status">
        <span class="status-indicator status-${status.toLowerCase()}"></span>
        <strong>${statusText}</strong>
      </div>
      <div class="go-badge-id">${goId}</div>
      <button class="go-badge-details" id="go-show-details">Voir les détails</button>
    </div>
  `;
  
  return badge;
}

function createDetailsModal(diffData) {
  const modal = document.createElement('div');
  modal.id = 'go-evolution-modal';
  modal.className = 'go-modal';
  
  const oldDef = diffData.old_definition || 'Non disponible';
  const newDef = diffData.new_definition || 'Non disponible';
  const oldParents = diffData.old_parents || [];
  const newParents = diffData.new_parents || [];
  const addedRelations = diffData.added_relations || [];
  const removedRelations = diffData.removed_relations || [];
  
  modal.innerHTML = `
    <div class="go-modal-content">
      <div class="go-modal-header">
        <h2>Détails de l'évolution - ${diffData.go_id}</h2>
        <button class="go-modal-close" id="go-modal-close">×</button>
      </div>
      <div class="go-modal-body">
        <div class="go-comparison-section">
          <h3>Définitions</h3>
          <div class="go-comparison-grid">
            <div class="go-comparison-old">
              <h4>Ancienne version</h4>
              <p>${oldDef}</p>
            </div>
            <div class="go-comparison-new">
              <h4>Nouvelle version</h4>
              <p>${newDef}</p>
            </div>
          </div>
        </div>
        
        <div class="go-comparison-section">
          <h3>Hiérarchie (Parents)</h3>
          <div class="go-comparison-grid">
            <div class="go-comparison-old">
              <h4>Anciens parents</h4>
              <ul>
                ${oldParents.map(p => `<li>${p}</li>`).join('') || '<li>Aucun</li>'}
              </ul>
            </div>
            <div class="go-comparison-new">
              <h4>Nouveaux parents</h4>
              <ul>
                ${newParents.map(p => `<li>${p}</li>`).join('') || '<li>Aucun</li>'}
              </ul>
            </div>
          </div>
        </div>
        
        ${addedRelations.length > 0 ? `
        <div class="go-comparison-section">
          <h3>Relations ajoutées</h3>
          <ul>
            ${addedRelations.map(r => `<li>${r}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
        
        ${removedRelations.length > 0 ? `
        <div class="go-comparison-section">
          <h3>Relations supprimées</h3>
          <ul>
            ${removedRelations.map(r => `<li>${r}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
        
        <div class="go-comparison-section">
          <h3>Métadonnées</h3>
          <p><strong>Date de changement:</strong> ${diffData.change_date || 'Non disponible'}</p>
          ${diffData.release_notes_url ? `<p><a href="${diffData.release_notes_url}" target="_blank">Voir les release notes</a></p>` : ''}
        </div>
      </div>
    </div>
  `;
  
  return modal;
}

async function fetchTermEvolution(goId) {
  try {
    const settings = await chrome.storage.sync.get({
      apiUrl: 'http://localhost:8000',
      cacheEnabled: true
    });
    
    const response = await chrome.runtime.sendMessage({
      action: 'fetchTermDiff',
      goId: goId,
      apiUrl: settings.apiUrl,
      cacheEnabled: settings.cacheEnabled
    });
    
    return response;
  } catch (error) {
    console.error('Erreur lors de la récupération des données:', error);
    return null;
  }
}

function determineStatus(diffData) {
  if (!diffData) return 'unknown';
  if (diffData.is_deprecated) return 'deprecated';
  if (diffData.is_new) return 'new';
  if (diffData.has_changes) return 'modified';
  return 'stable';
}

async function injectEvolutionInfo() {
  const goId = extractGOId();
  
  if (!goId) {
    console.log('Aucun identifiant GO détecté sur cette page');
    return;
  }
  
  console.log('GO ID détecté:', goId);
  
  const diffData = await fetchTermEvolution(goId);
  const status = determineStatus(diffData);
  
  const badge = createBadge(status, goId);
  document.body.appendChild(badge);
  
  document.getElementById('go-badge-close').addEventListener('click', () => {
    badge.remove();
  });
  
  document.getElementById('go-show-details').addEventListener('click', () => {
    if (diffData) {
      const modal = createDetailsModal(diffData);
      document.body.appendChild(modal);
      
      document.getElementById('go-modal-close').addEventListener('click', () => {
        modal.remove();
      });
      
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.remove();
        }
      });
    }
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', injectEvolutionInfo);
} else {
  injectEvolutionInfo();
}

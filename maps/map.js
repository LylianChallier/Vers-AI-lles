class SimpleTileMap {
  constructor(options = {}) {
    // Options de base
    this.level = options.level ?? 4; // Niveau utilisé dans le nom de fichier: plan_<level>_<row>_<col>.jpg
    this.minRow = options.minRow ?? 1;
    this.maxRow = options.maxRow ?? 15;
    this.minCol = options.minCol ?? 1;
    this.maxCol = options.maxCol ?? 15;

    this.tileSize = options.tileSize ?? 256;
  this.minScale = options.minScale ?? 0.1;
    this.maxScale = options.maxScale ?? 3;

    // Éléments DOM
    this.mapWrapper = document.getElementById('mapWrapper');
    this.tileLayer = document.getElementById('tileLayer');

    // État de la vue
    this.scale = 1;
    this.translateX = 0;
    this.translateY = 0;

    // Dragging
    this.isDragging = false;
    this.startX = 0;
    this.startY = 0;

    // Taille de la grille
    this.gridWidth = (this.maxCol - this.minCol + 1);
    this.gridHeight = (this.maxRow - this.minRow + 1);

  // Dimensionner la zone carte comme une section fixe intégrée à la page
  this.sizeWrapperFixed(options.wrapperWidth, options.wrapperHeight);

    // Chargement des tuiles
    this.loadTiles();

    // Écouteurs d'événements
    this.initEvents();

    // Vue initiale
    this.setInitialView();
  }

  sizeWrapperFixed(widthPx, heightPx) {
    const w = typeof widthPx === 'number' ? widthPx : 960;
    const h = typeof heightPx === 'number' ? heightPx : 600;
    this.mapWrapper.style.width = `${w}px`;
    this.mapWrapper.style.height = `${h}px`;
  }

  loadTiles() {
    // (Optionnel) définir les dimensions de la couche pour débogage/mesure
    this.tileLayer.style.width = `${this.gridWidth * this.tileSize}px`;
    this.tileLayer.style.height = `${this.gridHeight * this.tileSize}px`;

    for (let row = this.minRow; row <= this.maxRow; row++) {
      for (let col = this.minCol; col <= this.maxCol; col++) {
        const tile = document.createElement('div');
        tile.className = 'tile';
        tile.style.left = `${(col - this.minCol) * this.tileSize}px`;
        tile.style.top = `${(row - this.minRow) * this.tileSize}px`;

        const img = document.createElement('img');
        img.src = `tuiles/plan_${this.level}_${row}_${col}.jpg`;

        img.onload = () => tile.classList.add('loaded');
        img.onerror = () => {
          // Si l'image n'existe pas, on peut soit afficher un placeholder, soit retirer la tuile
          // Ici: on retire la tuile pour éviter les "trous vides"
          tile.remove();
        };

        tile.appendChild(img);
        this.tileLayer.appendChild(tile);
      }
    }
  }

  initEvents() {
    // Drag
    this.mapWrapper.addEventListener('mousedown', (e) => {
      e.preventDefault();
      this.isDragging = true;
      this.startX = e.clientX - this.translateX;
      this.startY = e.clientY - this.translateY;
      this.mapWrapper.classList.add('dragging');
    });

    document.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      const newX = e.clientX - this.startX;
      const newY = e.clientY - this.startY;
      const { minX, maxX, minY, maxY } = this.calculateLimits();
      this.translateX = Math.max(minX, Math.min(maxX, newX));
      this.translateY = Math.max(minY, Math.min(maxY, newY));
      this.updateTransform();
    });

    document.addEventListener('mouseup', () => {
      if (!this.isDragging) return;
      this.isDragging = false;
      this.mapWrapper.classList.remove('dragging');
      // Snap aux bornes si nécessaire
      const { minX, maxX, minY, maxY } = this.calculateLimits();
      this.translateX = Math.max(minX, Math.min(maxX, this.translateX));
      this.translateY = Math.max(minY, Math.min(maxY, this.translateY));
      this.updateTransform();
    });

    // Zoom molette centré sur la souris
    this.mapWrapper.addEventListener('wheel', (e) => {
      e.preventDefault();
      const rect = this.mapWrapper.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const factor = e.deltaY > 0 ? 0.93 : 1.075;
      this.zoomToPoint(mouseX, mouseY, factor);
    }, { passive: false });
  }

  calculateLimits() {
    const rect = this.mapWrapper.getBoundingClientRect();
    const mapWidth = this.gridWidth * this.tileSize * this.scale;
    const mapHeight = this.gridHeight * this.tileSize * this.scale;

    const padding = 0; // pas de zone "vide" volontaire
    return {
      minX: rect.width - mapWidth - padding,
      maxX: padding,
      minY: rect.height - mapHeight - padding,
      maxY: padding,
    };
  }

  updateTransform() {
    this.tileLayer.style.transform = `translate3d(${this.translateX}px, ${this.translateY}px, 0) scale(${this.scale})`;
  }

  zoomToPoint(x, y, factor) {
    const oldScale = this.scale;
    const newScale = Math.max(this.minScale, Math.min(this.maxScale, oldScale * factor));
    if (newScale === oldScale) return;

    // Conserver le point sous le curseur
    const scaleChange = newScale / oldScale;
    this.translateX = x - scaleChange * (x - this.translateX);
    this.translateY = y - scaleChange * (y - this.translateY);
    this.scale = newScale;

    // Recalage aux limites
    const { minX, maxX, minY, maxY } = this.calculateLimits();
    this.translateX = Math.max(minX, Math.min(maxX, this.translateX));
    this.translateY = Math.max(minY, Math.min(maxY, this.translateY));

    this.updateTransform();
  }

  setInitialView() {
    const rect = this.mapWrapper.getBoundingClientRect();
    const mapPixelWidth = this.gridWidth * this.tileSize;
    const mapPixelHeight = this.gridHeight * this.tileSize;

    // Adapter la carte à la section fixe et empêcher de dézoomer en dessous
    const scaleW = rect.width / mapPixelWidth;
    const scaleH = rect.height / mapPixelHeight;
    const fitScale = Math.min(scaleW, scaleH);
    this.minScale = fitScale; // min = la carte entière tient dans la section
    this.scale = fitScale;

    // Centrer la carte dans la section
    const centerMapX = mapPixelWidth / 2;
    const centerMapY = mapPixelHeight / 2;
    const viewCenterX = rect.width / 2;
    const viewCenterY = rect.height / 2;
    this.translateX = viewCenterX - (centerMapX * this.scale);
    this.translateY = viewCenterY - (centerMapY * this.scale);

    // Limites
    const { minX, maxX, minY, maxY } = this.calculateLimits();
    this.translateX = Math.max(minX, Math.min(maxX, this.translateX));
    this.translateY = Math.max(minY, Math.min(maxY, this.translateY));

    this.updateTransform();
  }

  // API boutons
  zoomIn() {
    const rect = this.mapWrapper.getBoundingClientRect();
    this.zoomToPoint(rect.width / 2, rect.height / 2, 1.1);
  }
  zoomOut() {
    const rect = this.mapWrapper.getBoundingClientRect();
    this.zoomToPoint(rect.width / 2, rect.height / 2, 0.91);
  }
  resetView() { this.setInitialView(); }

}

// Instance globale et fonctions pour les boutons inline dans index.html
let tileMap;
window.zoomIn = () => tileMap?.zoomIn();
window.zoomOut = () => tileMap?.zoomOut();
window.resetView = () => tileMap?.resetView();

window.addEventListener('DOMContentLoaded', () => {
  tileMap = new SimpleTileMap({
    level: 4,
    minRow: 1,
    maxRow: 15,
    minCol: 1,
    maxCol: 15,
    tileSize: 256,
    // Dimensions de la section carte (ajustables)
    wrapperWidth: 450,
    wrapperHeight: 450,
  });

  // Charger et afficher les points d'intérêt
  let poiData = [];
  fetch('./catalog.json')
    .then(r => r.json())
    .then(data => {
      if (Array.isArray(data)) {
        poiData = data;
        data.forEach(poi => {
          if (poi.x && poi.y) {
            addPOIMarker(poi);
          }
        });
        initSearch(poiData);
      }
    })
    .catch(err => console.error('Erreur chargement catalog.json:', err));
});

// Ajouter un marqueur POI sur la carte
function addPOIMarker(poi) {
  const marker = document.createElement('div');
  marker.className = 'poi-marker';
  marker.title = poi.nom || poi.id;
  marker.dataset.id = poi.id;

  // Positionner le marqueur en fonction des coordonnées
  // Les coordonnées dans catalog.json sont en pourcentage (0-100) de la carte complète
  const gridWidth = 15 * 256; // 15 colonnes de 256px
  const gridHeight = 15 * 256; // 15 lignes de 256px

  let xPx, yPx;
  // Les coordonnées sont toujours en pourcentage dans catalog.json
  xPx = (poi.x / 100) * gridWidth;
  yPx = (poi.y / 100) * gridHeight;

  marker.style.left = `${xPx}px`;
  marker.style.top = `${yPx}px`;

  // Info-bulle au survol
  marker.addEventListener('click', () => {
    alert(`${poi.nom || poi.id}\n${poi.info || ''}`);
  });

  document.getElementById('tileLayer').appendChild(marker);
}

// Système de recherche
function initSearch(pois) {
  const searchInput = document.getElementById('searchInput');
  const searchResults = document.getElementById('searchResults');
  let currentResults = [];

  const performSearch = () => {
    const query = searchInput.value.toLowerCase().trim();

    if (query.length < 2) {
      searchResults.classList.remove('show');
      return;
    }

    currentResults = pois.filter(poi =>
      (poi.nom && poi.nom.toLowerCase().includes(query)) ||
      (poi.id && poi.id.toLowerCase().includes(query)) ||
      (poi.info && poi.info.toLowerCase().includes(query))
    );

    displaySearchResults(currentResults);
  };

  searchInput.addEventListener('input', performSearch);

  // Gérer la touche Entrée
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (currentResults.length > 0) {
        centerOnPOI(currentResults[0].id);
      }
    }
  });

  // Fermer les résultats si on clique ailleurs
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-container')) {
      searchResults.classList.remove('show');
    }
  });
}

function displaySearchResults(results) {
  const searchResults = document.getElementById('searchResults');

  if (results.length === 0) {
    searchResults.innerHTML = '<div class="search-result-item"><div class="search-result-name">Aucun résultat</div></div>';
    searchResults.classList.add('show');
    return;
  }

  searchResults.innerHTML = results.map(poi => `
    <div class="search-result-item" onclick="centerOnPOI('${poi.id}')">
      <div class="search-result-name">${poi.nom || poi.id}</div>
      <div class="search-result-info">${poi.info ? poi.info.substring(0, 80) + '...' : ''}</div>
    </div>
  `).join('');

  searchResults.classList.add('show');
}

function centerOnPOI(poiId) {
  // Fermer les résultats de recherche
  document.getElementById('searchResults').classList.remove('show');
  document.getElementById('searchInput').value = '';

  // Trouver le marqueur
  const marker = document.querySelector(`.poi-marker[data-id="${poiId}"]`);
  if (!marker) return;

  // Récupérer les coordonnées du marqueur
  const markerX = parseFloat(marker.style.left);
  const markerY = parseFloat(marker.style.top);

  // Centrer la vue sur le marqueur
  const rect = tileMap.mapWrapper.getBoundingClientRect();
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;

  // Zoomer un peu
  tileMap.scale = 1.5;

  // Calculer le déplacement nécessaire
  tileMap.translateX = centerX - (markerX * tileMap.scale);
  tileMap.translateY = centerY - (markerY * tileMap.scale);

  // Appliquer les limites
  const { minX, maxX, minY, maxY } = tileMap.calculateLimits();
  tileMap.translateX = Math.max(minX, Math.min(maxX, tileMap.translateX));
  tileMap.translateY = Math.max(minY, Math.min(maxY, tileMap.translateY));

  tileMap.updateTransform();

  // Animer le marqueur
  marker.style.animation = 'pulse 1s ease-in-out 3';

  // Ajouter une flèche pointant vers le marqueur
  highlightPOI(marker);
}

function highlightPOI(marker) {
  // Supprimer l'ancienne flèche si elle existe
  const oldArrow = document.querySelector('.poi-arrow');
  if (oldArrow) oldArrow.remove();

  // Créer une nouvelle flèche
  const arrow = document.createElement('div');
  arrow.className = 'poi-arrow';
  arrow.innerHTML = '▼';

  // Positionner la flèche au-dessus du marqueur
  arrow.style.left = marker.style.left;
  arrow.style.top = marker.style.top;

  document.getElementById('tileLayer').appendChild(arrow);

  // Retirer la flèche après 3 secondes
  setTimeout(() => {
    arrow.remove();
  }, 3000);
}

// Variables globales pour le zoom et le pan
let currentScale = 1;
let currentTranslateX = 0;
let currentTranslateY = 0;
let isDragging = false;
let startX, startY;
let selectedEtape = null;

// Éléments DOM
const svg = document.getElementById('planSVG');
const marqueursGroup = document.getElementById('marqueursGroup');
const trajetsGroup = document.getElementById('trajetsGroup');
const tooltip = document.getElementById('tooltip');

// ===== INITIALISATION =====

function init() {
    initSidebar();
    dessinerTrajets();
    dessinerMarqueurs();
    initEventListeners();
}

// Initialiser la liste des étapes dans la sidebar
function initSidebar() {
    const listeEtapes = document.getElementById('listeEtapes');
    listeEtapes.innerHTML = '';
    
    document.getElementById('nbEtapes').textContent = itineraire.etapes.length;
    document.getElementById('dureeTotal').textContent = itineraire.duree_totale;
    
    itineraire.etapes.forEach((etape) => {
        const etapeDiv = document.createElement('div');
        etapeDiv.className = 'etape';
        etapeDiv.dataset.ordre = etape.ordre;
        etapeDiv.innerHTML = `
            <div>
                <span class="etape-numero">${etape.ordre}</span>
                <span class="etape-nom">${etape.lieu}</span>
            </div>
            <div class="etape-duree">⏱️ ${etape.duree}</div>
            <div class="etape-desc">${etape.description}</div>
        `;
        
        etapeDiv.addEventListener('click', () => {
            highlightEtape(etape.ordre);
        });
        
        listeEtapes.appendChild(etapeDiv);
    });
}

// ===== DESSIN SUR LE PLAN =====

// Dessiner les trajets entre les étapes
function dessinerTrajets() {
    trajetsGroup.innerHTML = '';
    
    for (let i = 0; i < itineraire.etapes.length - 1; i++) {
        const etape1 = itineraire.etapes[i];
        const etape2 = itineraire.etapes[i + 1];
        
        const x1 = (etape1.x / 100) * 1000;
        const y1 = (etape1.y / 100) * 800;
        const x2 = (etape2.x / 100) * 1000;
        const y2 = (etape2.y / 100) * 800;
        
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", x1);
        line.setAttribute("y1", y1);
        line.setAttribute("x2", x2);
        line.setAttribute("y2", y2);
        line.setAttribute("stroke", "#667eea");
        line.setAttribute("stroke-width", "3");
        line.setAttribute("class", "trajet");
        line.setAttribute("opacity", "0.7");
        
        trajetsGroup.appendChild(line);
    }
}

// Dessiner les marqueurs pour chaque étape
function dessinerMarqueurs() {
    marqueursGroup.innerHTML = '';
    
    itineraire.etapes.forEach(etape => {
        const x = (etape.x / 100) * 1000;
        const y = (etape.y / 100) * 800;
        
        const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
        g.setAttribute("class", "marqueur");
        g.dataset.ordre = etape.ordre;
        
        // Cercle extérieur (halo)
        const halo = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        halo.setAttribute("cx", x);
        halo.setAttribute("cy", y);
        halo.setAttribute("r", "20");
        halo.setAttribute("fill", "#667eea");
        halo.setAttribute("opacity", "0.3");
        
        // Cercle principal
        const cercle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        cercle.setAttribute("cx", x);
        cercle.setAttribute("cy", y);
        cercle.setAttribute("r", "15");
        cercle.setAttribute("fill", "#667eea");
        cercle.setAttribute("stroke", "white");
        cercle.setAttribute("stroke-width", "3");
        cercle.setAttribute("class", "marqueur-cercle");
        
        // Numéro
        const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
        text.setAttribute("x", x);
        text.setAttribute("y", y);
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("dominant-baseline", "central");
        text.setAttribute("fill", "white");
        text.setAttribute("font-size", "14");
        text.setAttribute("font-weight", "bold");
        text.setAttribute("pointer-events", "none");
        text.textContent = etape.ordre;
        
        g.appendChild(halo);
        g.appendChild(cercle);
        g.appendChild(text);
        
        // Events
        g.addEventListener('mouseenter', (e) => {
            showTooltip(e, etape);
        });
        
        g.addEventListener('mouseleave', () => {
            hideTooltip();
        });
        
        g.addEventListener('click', () => {
            highlightEtape(etape.ordre);
        });
        
        marqueursGroup.appendChild(g);
    });
}

// ===== INTERACTIONS =====

function showTooltip(e, etape) {
    tooltip.innerHTML = `
        <strong>${etape.ordre}. ${etape.lieu}</strong><br>
        ⏱️ ${etape.duree}<br>
        ${etape.description}
    `;
    tooltip.classList.add('show');
    
    tooltip.style.left = (e.clientX + 10) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
}

function hideTooltip() {
    tooltip.classList.remove('show');
}

function highlightEtape(ordre) {
    // Mettre à jour sidebar
    document.querySelectorAll('.etape').forEach(el => {
        el.classList.remove('active');
    });
    const activeEtape = document.querySelector(`.etape[data-ordre="${ordre}"]`);
    if (activeEtape) {
        activeEtape.classList.add('active');
        activeEtape.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    // Mettre à jour marqueurs
    document.querySelectorAll('.marqueur').forEach(el => {
        const cercle = el.querySelector('.marqueur-cercle');
        const halo = el.querySelector('circle');
        if (el.dataset.ordre == ordre) {
            cercle.setAttribute('fill', '#ff6b6b');
            halo.setAttribute('fill', '#ff6b6b');
        } else {
            cercle.setAttribute('fill', '#667eea');
            halo.setAttribute('fill', '#667eea');
        }
    });
}

// ===== ZOOM ET PAN =====

function updateTransform() {
    svg.style.transform = `translate(${currentTranslateX}px, ${currentTranslateY}px) scale(${currentScale})`;
}

function zoomIn() {
    currentScale *= 1.2;
    updateTransform();
}

function zoomOut() {
    currentScale /= 1.2;
    updateTransform();
}

function resetView() {
    currentScale = 1;
    currentTranslateX = 0;
    currentTranslateY = 0;
    updateTransform();
}

// ===== EVENT LISTENERS =====

function initEventListeners() {
    // Drag pour déplacer la carte
    svg.addEventListener('mousedown', (e) => {
        if (e.target.closest('.marqueur')) return;
        isDragging = true;
        startX = e.clientX - currentTranslateX;
        startY = e.clientY - currentTranslateY;
        svg.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        currentTranslateX = e.clientX - startX;
        currentTranslateY = e.clientY - startY;
        updateTransform();
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
        svg.style.cursor = 'move';
    });

    // Zoom avec la molette
    svg.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        currentScale *= delta;
        currentScale = Math.max(0.5, Math.min(currentScale, 3));
        updateTransform();
    });
}

// Lancer l'initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', init);
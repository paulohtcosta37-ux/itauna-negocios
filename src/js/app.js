import { formatISODate, fetchTodayNews } from './utils.js?v=1.2.0';

// Limpar Cache Storage imediatamente para evitar dados obsoletos
if ('caches' in window) {
  caches.keys().then(function(names) {
    for (let name of names) {
      caches.delete(name);
    }
  });
}

// Desregistrar qualquer service worker ativo para evitar cache persistente de PWAs anteriores e recarregar
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function(registrations) {
    if (registrations.length > 0) {
      console.log(`[Service Worker] Encontrados ${registrations.length} Service Workers ativos. Desregistrando e limpando cache...`);
      const unregisterPromises = registrations.map(r => r.unregister());
      Promise.all(unregisterPromises).then(() => {
        console.log('[Service Worker] Todos os Service Workers desregistrados.');
        if ('caches' in window) {
          caches.keys().then(function(names) {
            return Promise.all(names.map(name => caches.delete(name)));
          }).then(() => {
            console.log('[Cache] Cache limpo após desregistro. Recarregando página...');
            window.location.reload();
          });
        } else {
          window.location.reload();
        }
      });
    }
  });
}

// ==========================================================================
// ESTADO DA APLICAÇÃO
// ==========================================================================
const state = {
  currentNews: []          // Notícias do dia de hoje
};

// Elementos do DOM
const newsGrid = document.getElementById('newsGrid');
const loaderContainer = document.getElementById('loaderContainer');
const emptyState = document.getElementById('emptyState');
const emptyStateMessage = document.getElementById('emptyStateMessage');
const newsModal = document.getElementById('newsModal');
const modalCloseBtn = document.getElementById('modalCloseBtn');

// ==========================================================================
// INICIALIZAÇÃO
// ==========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  if (loaderContainer) loaderContainer.style.display = 'flex';
  setupEventListeners();
  
  // Carregar notícias para o dia de hoje
  await loadTodayNews();
});

// ==========================================================================
// CARREGAMENTO E RENDERIZAÇÃO DE DADOS
// ==========================================================================

/**
 * Busca notícias de hoje no JSON diário e as renderiza se passarem nas regras de horário e data
 */
async function loadTodayNews() {
  if (loaderContainer) loaderContainer.style.display = 'flex';
  if (newsGrid) {
    newsGrid.innerHTML = '';
    newsGrid.style.display = 'none';
  }
  if (emptyState) emptyState.style.display = 'none';

  const today = new Date();
  const todayISO = formatISODate(today);
  const currentHour = today.getHours();

  // Regra de negócio: Se antes das 8:00 AM locais, bloqueia exibição
  if (currentHour < 8) {
    console.log(`[News Portal] Acesso antes das 08:00 AM (${currentHour}:00). Bloqueando exibição.`);
    if (loaderContainer) loaderContainer.style.display = 'none';
    showEmptyState(todayISO);
    return;
  }

  // Buscar notícias de hoje
  console.log(`[News Portal] Carregando notícias de hoje...`);
  const news = await fetchTodayNews();
  
  if (loaderContainer) loaderContainer.style.display = 'none';

  // Verificar consistência de dados (se o JSON contiver notícias de hoje)
  if (news && news.length > 0) {
    const newsDate = news[0].date;
    if (newsDate === todayISO) {
      state.currentNews = news;
      renderNewsGrid(news);
      if (newsGrid) newsGrid.style.display = 'grid';
    } else {
      console.warn(`[News Portal] Data do JSON (${newsDate}) é diferente do dia de hoje (${todayISO}). Exibindo preparação.`);
      state.currentNews = [];
      showEmptyState(todayISO);
    }
  } else {
    console.warn(`[News Portal] Nenhuma notícia encontrada no JSON.`);
    state.currentNews = [];
    showEmptyState(todayISO);
  }
}

/**
 * Exibe a mensagem de ausência de notícias estilizada (Novidades a Caminho!)
 * @param {string} isoString 
 */
function showEmptyState(isoString) {
  const [year, month, day] = isoString.split('-');
  const formattedDateStr = `${day}/${month}/${year}`;
  
  const emptyStateIcon = document.getElementById('emptyStateIcon');
  const emptyStateTitle = document.getElementById('emptyStateTitle');
  
  if (emptyStateIcon) {
    emptyStateIcon.innerText = 'schedule';
    emptyStateIcon.className = 'material-symbols-rounded empty-icon animated-clock';
  }
  if (emptyStateTitle) {
    emptyStateTitle.innerText = 'Novidades a Caminho!';
  }
  if (emptyStateMessage) {
    emptyStateMessage.innerHTML = `As análises e oportunidades do dia <strong>${formattedDateStr}</strong> estão sendo preparadas pela nossa equipe.<br><span style="display:inline-block; margin-top:14px; font-weight:700; color:var(--primary); font-size: 1.05rem;">Volte após as 08:00 para acompanhar as notícias do dia!</span>`;
  }
  
  if (emptyState) emptyState.style.display = 'flex';
}

/**
 * Retorna o ícone geométrico minimalista de traço grosso baseado na categoria da notícia
 * @param {string} category 
 * @returns {string} Código SVG
 */
function getGeoIconSvg(category) {
  const cat = category.toLowerCase();
  if (cat.includes('evento')) {
    // Ícone "+" cruz geométrica
    return `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <line x1="12" y1="5" x2="12" y2="19"></line>
        <line x1="5" y1="12" x2="19" y2="12"></line>
      </svg>
    `;
  } else if (cat.includes('concorrência') || cat.includes('concorrencia')) {
    // Ícone "o" octógono
    return `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"></polygon>
      </svg>
    `;
  } else if (cat.includes('infraestrutura')) {
    // Ícone "x" cruz diagonal
    return `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    `;
  } else {
    // Ícone losango
    return `
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <polygon points="12 2 22 12 12 22 2 12 12 2"></polygon>
      </svg>
    `;
  }
}

/**
 * Retorna o SVG do gradiente abstrato de vidro refrativo interno
 * @param {string} impactLevel 
 * @returns {string} Código HTML/SVG
 */
function getCardBgGradientSvg(impactLevel) {
  let primaryColor = '#60a5fa'; // Azul Neon
  let secondaryColor = '#0353a4'; // Azul Profundo
  
  if (impactLevel === 'Alto') {
    primaryColor = '#f43f5e'; // Vermelho brilhante
    secondaryColor = '#2563eb'; // Azul brilhante
  } else if (impactLevel === 'Médio') {
    primaryColor = '#f97316'; // Laranja brilhante
    secondaryColor = '#0d9488'; // Teal brilhante
  } else {
    primaryColor = '#0d9488'; // Teal
    secondaryColor = '#60a5fa';
  }
  
  return `
    <div class="card-bg-gradient">
      <svg viewBox="0 0 200 200" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <filter id="glassBlurCard">
            <feGaussianBlur stdDeviation="28" />
          </filter>
        </defs>
        <circle cx="55" cy="55" r="45" fill="${primaryColor}" filter="url(#glassBlurCard)" />
        <circle cx="145" cy="145" r="55" fill="${secondaryColor}" filter="url(#glassBlurCard)" />
      </svg>
    </div>
  `;
}

/**
 * Renderiza o Grid de Notícias no formato Glassmorphism Uniforme
 * @param {Array} newsList 
 */
function renderNewsGrid(newsList) {
  newsGrid.innerHTML = '';
  
  newsList.forEach((newsItem) => {
    const card = document.createElement('article');
    
    // Classes de estilização base
    const impactClass = `impact-${newsItem.impactLevel.toLowerCase()}`;
    card.className = `news-card ${impactClass}`;
    
    card.innerHTML = `
      <!-- Fundo de Vidro Refrativo (Gradiente Abstrato) -->
      ${getCardBgGradientSvg(newsItem.impactLevel)}

      <div class="card-header-tags">
        <span class="category-tag">${newsItem.category}</span>
        <span class="impact-badge" aria-label="Nível de impacto comercial: ${newsItem.impactLevel}">
          ${newsItem.impactLevel} Impacto
        </span>
      </div>
      
      <!-- Ícone Geométrico Minimalista -->
      <div class="card-geo-icon" aria-hidden="true">
        ${getGeoIconSvg(newsItem.category)}
      </div>

      <div class="card-body-content">
        <h3 class="card-title">${newsItem.title}</h3>
        <p class="card-summary">${newsItem.executiveSummary}</p>
      </div>
      
      <div class="card-footer">
        <span class="read-more-text">
          Ver análise investigativa <span class="material-symbols-rounded">arrow_right_alt</span>
        </span>
      </div>
    `;
    
    card.addEventListener('click', () => openModal(newsItem));
    
    newsGrid.appendChild(card);
  });
}

// ==========================================================================
// CONTROLE DO MODAL DE DETALHES & DASHBOARD SVG
// ==========================================================================

/**
 * Preenche e abre o modal de detalhes estilo iOS
 * @param {Object} newsItem 
 */
function openModal(newsItem) {
  // Preencher textos do modal
  document.getElementById('modalCategory').innerText = newsItem.category;
  document.getElementById('modalTitle').innerText = newsItem.title;
  document.getElementById('modalSummary').innerText = newsItem.executiveSummary;
  
  // Imagens removidas a pedido do usuário
  
  // Formatar análise investigativa (processa quebras de linha para parágrafos)
  const analysisText = newsItem.investigativeAnalysis || "Nenhuma análise aprofundada fornecida.";
  document.getElementById('modalAnalysis').innerHTML = analysisText.split('\n').map(p => `<p style="margin-bottom:12px;">${p}</p>`).join('');
  
  // Renderizar gráficos se for de impacto Alto ou Médio (Dashboard de Análise)
  const intelSection = document.getElementById('modalIntelligenceSection');
  const chartContainer = document.getElementById('modalChartContainer');
  
  if (newsItem.impactLevel === 'Alto' || newsItem.impactLevel === 'Médio') {
    intelSection.style.display = 'block';
    renderSVGChart(chartContainer, newsItem);
  } else {
    intelSection.style.display = 'none';
  }
  
  // Formatar Como Agir e Como Lucrar
  document.getElementById('modalHowToAct').innerHTML = formatTextList(newsItem.howToAct || "Nenhuma recomendação registrada.");
  document.getElementById('modalHowToProfit').innerHTML = formatTextList(newsItem.howToProfit || "Nenhum insight de monetização registrado.");
  
  // Estilizar o badge de impacto no modal
  const modalImpact = document.getElementById('modalImpact');
  modalImpact.innerText = `${newsItem.impactLevel} Impacto`;
  
  modalImpact.className = 'modal-impact-badge';
  if (newsItem.impactLevel === 'Alto') {
    modalImpact.style.backgroundColor = 'var(--impact-high-bg)';
    modalImpact.style.color = 'var(--impact-high)';
    modalImpact.style.setProperty('--impact-color', 'var(--impact-high)');
  } else if (newsItem.impactLevel === 'Médio') {
    modalImpact.style.backgroundColor = 'var(--impact-medium-bg)';
    modalImpact.style.color = 'var(--impact-medium)';
    modalImpact.style.setProperty('--impact-color', 'var(--impact-medium)');
  } else {
    modalImpact.style.backgroundColor = 'var(--impact-low-bg)';
    modalImpact.style.color = 'var(--impact-low)';
    modalImpact.style.setProperty('--impact-color', 'var(--impact-low)');
  }
  
  modalImpact.innerHTML = `<span class="material-symbols-rounded" style="font-size:12px; color:var(--impact-color);">fiber_manual_record</span> ${newsItem.impactLevel} Impacto`;

  // Renderizar o link da fonte dinamicamente
  const modalSourceLink = document.getElementById('modalSourceLink');
  if (modalSourceLink) {
    if (newsItem.sourceName && newsItem.sourceUrl) {
      modalSourceLink.href = newsItem.sourceUrl;
      modalSourceLink.innerHTML = `<span class="material-symbols-rounded" style="font-size: 14px;">open_in_new</span> ${newsItem.sourceName}`;
      modalSourceLink.style.display = 'inline-flex';
    } else {
      modalSourceLink.style.display = 'none';
      modalSourceLink.href = '';
      modalSourceLink.innerHTML = '';
    }
  }

  // Exibir o modal
  newsModal.classList.add('active');
  newsModal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden'; // Trava scroll da página
}

/**
 * Fecha o modal
 */
function closeModal() {
  newsModal.classList.remove('active');
  newsModal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = ''; // Destrava scroll da página
}

/**
 * Transforma parágrafos numerados em listas HTML ordenadas ou parágrafos
 * @param {string} text 
 */
function formatTextList(text) {
  if (text.includes('\n')) {
    const lines = text.split('\n').filter(line => line.trim().length > 0);
    if (/^\d+\./.test(lines[0])) {
      return `<ol>${lines.map(line => `<li>${line.replace(/^\d+\.\s*/, '')}</li>`).join('')}</ol>`;
    } else {
      return `<ul>${lines.map(line => `<li>${line.replace(/^-\s*/, '')}</li>`).join('')}</ul>`;
    }
  }
  return `<p>${text}</p>`;
}

// ==========================================================================
// RENDERIZADORES GRÁFICOS SVG (DASHBOARD)
// ==========================================================================

/**
 * Desenha um gráfico de barras SVG dinâmico baseado na categoria do relatório
 * @param {HTMLElement} container 
 * @param {Object} newsItem 
 */
function renderSVGChart(container, newsItem) {
  let data = [];
  
  // Definir os eixos e valores com base na categoria para tornar o gráfico realista
  if (newsItem.category === 'Eventos') {
    data = [
      { name: 'Gastronomia', value: 45, label: '+45%' },
      { name: 'Hotelaria', value: 35, label: '+35%' },
      { name: 'Varejo/Roupas', value: 20, label: '+20%' },
      { name: 'Transporte', value: 30, label: '+30%' }
    ];
  } else if (newsItem.category === 'Concorrência') {
    data = [
      { name: 'Drogarias Locais', value: -12, label: '-12%' },
      { name: 'Convenção', value: 10, label: '+10%' },
      { name: 'Serviço Delivery', value: 25, label: '+25%' },
      { name: 'Fidelização', value: 30, label: '+30%' }
    ];
  } else if (newsItem.category === 'Infraestrutura') {
    data = [
      { name: 'Comércio Local', value: -15, label: '-15%' },
      { name: 'Serviço Delivery', value: 35, label: '+35%' },
      { name: 'Logística Insumos', value: 20, label: '+20%' },
      { name: 'Tráfego Pedestres', value: -8, label: '-8%' }
    ];
  } else {
    data = [
      { name: 'Varejo Centro', value: 15, label: '+15%' },
      { name: 'Serviços B2B', value: 20, label: '+20%' },
      { name: 'Mercado Imobiliário', value: 25, label: '+25%' },
      { name: 'Geração Empregos', value: 30, label: '+30%' }
    ];
  }

  const svgWidth = 340;
  const svgHeight = 180;
  
  let barsHTML = '';
  const barWidth = 36;
  const gap = 38;
  const startX = 48;
  const zeroY = 130; // Coordenada Y da linha de 0%
  const maxBarHeight = 90; // Altura máxima que representa o topo de 50%
  
  data.forEach((d, i) => {
    const x = startX + i * (barWidth + gap);
    
    // Mapear valor para a altura da barra (50% = maxBarHeight pixels)
    const barHeight = Math.abs(d.value) * (maxBarHeight / 50);
    const isNegative = d.value < 0;
    
    const y = isNegative ? zeroY : zeroY - barHeight;
    const color = isNegative ? '#f43f5e' : '#60a5fa'; // Vermelho Neon vs Azul Neon
    
    barsHTML += `
      <!-- Barra ${d.name} -->
      <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="5" fill="${color}" opacity="0.9" class="chart-bar">
        <title>${d.name}: ${d.label}</title>
      </rect>
      <!-- Texto do Eixo X -->
      <text x="${x + barWidth/2}" y="${zeroY + 18}" font-size="7.5" font-family="'Inter', sans-serif" font-weight="700" fill="#94a3b8" text-anchor="middle">${d.name}</text>
      <!-- Texto do Valor da Barra -->
      <text x="${x + barWidth/2}" y="${isNegative ? y + barHeight + 12 : y - 6}" font-size="8.5" font-family="'Inter', sans-serif" font-weight="800" fill="${color}" text-anchor="middle">${d.label}</text>
    `;
  });

  container.innerHTML = `
    <svg viewBox="0 0 ${svgWidth} ${svgHeight}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <!-- Linhas do Grid -->
      <line x1="30" y1="40" x2="330" y2="40" stroke="rgba(255, 255, 255, 0.08)" stroke-width="1"/>
      <line x1="30" y1="85" x2="330" y2="85" stroke="rgba(255, 255, 255, 0.08)" stroke-width="1"/>
      <line x1="30" y1="130" x2="330" y2="130" stroke="rgba(255, 255, 255, 0.2)" stroke-width="1.5"/>
      
      <!-- Indicadores de Eixo Y -->
      <text x="25" y="43" font-size="7" font-family="'Inter', sans-serif" font-weight="700" fill="#94a3b8" text-anchor="end">+50%</text>
      <text x="25" y="88" font-size="7" font-family="'Inter', sans-serif" font-weight="700" fill="#94a3b8" text-anchor="end">+25%</text>
      <text x="25" y="133" font-size="7" font-family="'Inter', sans-serif" font-weight="700" fill="#cbd5e1" text-anchor="end">0%</text>
      
      ${barsHTML}
    </svg>
  `;
}

/**
 * Renderiza um iframe do Google Maps interativo focado no local aproximado da notícia
 * @param {HTMLElement} container 
 * @param {Object} newsItem 
 */
function renderGoogleMap(container, newsItem) {
  let locationQuery = "Itaúna, MG";
  const titleLower = newsItem.title.toLowerCase();
  
  if (titleLower.includes('praça') || titleLower.includes('matriz') || titleLower.includes('arraial') || titleLower.includes('festival')) {
    locationQuery = "Praça Dr. Augusto Gonçalves, Itaúna - MG";
  } else if (titleLower.includes('jove soares') || titleLower.includes('araújo') || titleLower.includes('prainha') || titleLower.includes('avenida')) {
    locationQuery = "Avenida Jove Soares, Itaúna - MG";
  } else if (titleLower.includes('santanense')) {
    locationQuery = "Santanense, Itaúna - MG";
  } else if (newsItem.location) {
    locationQuery = `${newsItem.location}, Itaúna - MG`;
  }

  const embedUrl = `https://maps.google.com/maps?q=${encodeURIComponent(locationQuery)}&t=&z=16&ie=UTF8&iwloc=&output=embed`;
  
  container.innerHTML = `
    <iframe 
      width="100%" 
      height="100%" 
      style="border:0; border-radius:12px; filter: grayscale(0.2) contrast(1.15) brightness(0.95);" 
      loading="lazy" 
      allowfullscreen 
      referrerpolicy="no-referrer-when-downgrade" 
      src="${embedUrl}">
    </iframe>
  `;
}

// ==========================================================================
// CONFIGURAÇÃO DE EVENTOS
// ==========================================================================
function setupEventListeners() {
  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeModal);

  if (newsModal) {
    newsModal.addEventListener('click', (e) => {
      if (e.target === newsModal) {
        closeModal();
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && newsModal && newsModal.classList.contains('active')) {
      closeModal();
    }
  });
}

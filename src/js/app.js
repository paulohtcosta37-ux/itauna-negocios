import { formatISODate, getWeekdayName, getMonthName, fetchNewsByDate } from './utils.js';

// ==========================================================================
// ESTADO DA APLICAÇÃO
// ==========================================================================
const state = {
  selectedDate: new Date(), // Inicialmente hoje
  datesList: [],            // Últimos 14 dias
  currentNews: []           // Notícias do dia selecionado
};

// Elementos do DOM
const dateTimeline = document.getElementById('dateTimeline');
const calendarBtn = document.getElementById('calendarBtn');
const hiddenDateInput = document.getElementById('hiddenDateInput');
const newsGrid = document.getElementById('newsGrid');
const loaderContainer = document.getElementById('loaderContainer');
const emptyState = document.getElementById('emptyState');
const emptyStateMessage = document.getElementById('emptyStateMessage');
const newsModal = document.getElementById('newsModal');
const modalCloseBtn = document.getElementById('modalCloseBtn');

// ==========================================================================
// INICIALIZAÇÃO
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  setupDatesList();
  renderDateTimeline();
  setupEventListeners();
  
  // Carregar notícias para a data inicial (hoje)
  loadNewsForDate(state.selectedDate);
});

// ==========================================================================
// LÓGICA DE DATAS E LINHA DO TEMPO
// ==========================================================================

/**
 * Preenche a lista com os últimos 14 dias (a partir de hoje para trás)
 */
function setupDatesList() {
  state.datesList = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    state.datesList.push(d);
  }
}

/**
 * Renderiza o carrossel de datas no topo
 */
function renderDateTimeline() {
  dateTimeline.innerHTML = '';
  
  state.datesList.forEach((date) => {
    const isoString = formatISODate(date);
    const isSelected = formatISODate(state.selectedDate) === isoString;
    
    const dateItem = document.createElement('div');
    dateItem.className = `date-item ${isSelected ? 'active' : ''}`;
    dateItem.dataset.date = isoString;
    
    dateItem.innerHTML = `
      <span class="date-item-weekday">${getWeekdayName(date)}</span>
      <span class="date-item-day">${date.getDate()}</span>
      <span class="date-item-month">${getMonthName(date)}</span>
    `;
    
    dateItem.addEventListener('click', () => {
      selectDate(date);
      dateItem.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    });
    
    dateTimeline.appendChild(dateItem);
  });
}

/**
 * Modifica a data selecionada no estado e atualiza os componentes
 * @param {Date} date 
 */
function selectDate(date) {
  state.selectedDate = date;
  
  // Atualizar classe ativa na timeline
  const isoString = formatISODate(date);
  const items = dateTimeline.querySelectorAll('.date-item');
  let found = false;
  
  items.forEach(item => {
    if (item.dataset.date === isoString) {
      item.classList.add('active');
      found = true;
    } else {
      item.classList.remove('active');
    }
  });

  // Se a data selecionada não estiver na lista padrão (ex: escolhida via calendário)
  if (!found) {
    state.datesList.unshift(date);
    renderDateTimeline();
  }
  
  // Atualizar input do calendário invisível
  hiddenDateInput.value = isoString;
  
  // Carrega as notícias
  loadNewsForDate(date);
}

// ==========================================================================
// CARREGAMENTO E RENDERIZAÇÃO DE DADOS
// ==========================================================================

/**
 * Busca notícias no diretório local e as renderiza
 * @param {Date} date 
 */
async function loadNewsForDate(date) {
  const isoString = formatISODate(date);
  
  newsGrid.style.display = 'none';
  emptyState.style.display = 'none';
  loaderContainer.style.display = 'flex';
  
  const today = new Date();
  const todayISO = formatISODate(today);
  const currentHour = today.getHours();
  
  // Regra de negócio: se for a data de hoje (ou futura) e ainda for antes das 18:00 locais,
  // força a exibição do estado vazio avisando o horário de liberação.
  if (isoString > todayISO || (isoString === todayISO && currentHour < 18)) {
    loaderContainer.style.display = 'none';
    state.currentNews = [];
    showEmptyState(isoString);
    return;
  }
  
  const news = await fetchNewsByDate(isoString);
  
  loaderContainer.style.display = 'none';
  
  if (news && news.length > 0) {
    state.currentNews = news;
    renderNewsGrid(news);
    newsGrid.style.display = 'grid';
  } else {
    state.currentNews = [];
    showEmptyState(isoString);
  }
}

/**
 * Exibe a mensagem de ausência de notícias estilizada
 * @param {string} isoString 
 */
function showEmptyState(isoString) {
  const [year, month, day] = isoString.split('-');
  const formattedDateStr = `${day}/${month}/${year}`;
  
  const today = new Date();
  const todayISO = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0');
  
  const emptyStateIcon = document.getElementById('emptyStateIcon');
  const emptyStateTitle = document.getElementById('emptyStateTitle');
  
  if (isoString >= todayISO) {
    // Hoje ou Futuro
    if (emptyStateIcon) {
      emptyStateIcon.innerText = 'schedule';
      emptyStateIcon.className = 'material-symbols-rounded empty-icon animated-clock';
    }
    if (emptyStateTitle) {
      emptyStateTitle.innerText = 'Novidades a Caminho!';
    }
    emptyStateMessage.innerHTML = `As análises e oportunidades do dia <strong>${formattedDateStr}</strong> estão sendo preparadas pela nossa equipe.<br><span style="display:inline-block; margin-top:14px; font-weight:700; color:var(--primary); font-size: 1.05rem;">Volte após as 18:00 para acompanhar as notícias do dia!</span>`;
  } else {
    // Passado
    if (emptyStateIcon) {
      emptyStateIcon.innerText = 'history_toggle_off';
      emptyStateIcon.className = 'material-symbols-rounded empty-icon';
    }
    if (emptyStateTitle) {
      emptyStateTitle.innerText = 'Sem Relatórios Disponíveis';
    }
    emptyStateMessage.innerHTML = `Não há registros de análises comerciais cadastrados para o dia <strong>${formattedDateStr}</strong>.`;
  }
  
  emptyState.style.display = 'flex';
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
  if (calendarBtn) {
    calendarBtn.addEventListener('click', () => {
      if (hiddenDateInput) {
        hiddenDateInput.showPicker ? hiddenDateInput.showPicker() : hiddenDateInput.click();
      }
    });
  }
  
  if (hiddenDateInput) {
    hiddenDateInput.addEventListener('change', (e) => {
      if (e.target.value) {
        const [year, month, day] = e.target.value.split('-');
        const selectedDateObj = new Date(year, month - 1, day);
        selectDate(selectedDateObj);
      }
    });
  }

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

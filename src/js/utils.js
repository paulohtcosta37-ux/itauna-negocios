/**
 * UTILITÁRIOS - ITAÚNA NEGÓCIOS
 * Auxiliares de formatação de data e carregamento de dados
 */

/**
 * Formata um objeto Date para string YYYY-MM-DD respeitando o fuso local
 * @param {Date} date 
 * @returns {string}
 */
export function formatISODate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Retorna o nome abreviado do dia da semana em Português
 * @param {Date} date 
 * @returns {string}
 */
export function getWeekdayName(date) {
  const weekdays = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
  const today = new Date();
  
  // Se for hoje, retorna 'Hoje' ao invés do dia da semana
  if (formatISODate(date) === formatISODate(today)) {
    return 'Hoje';
  }
  
  return weekdays[date.getDay()];
}

/**
 * Retorna o nome abreviado do mês em Português
 * @param {Date} date 
 * @returns {string}
 */
export function getMonthName(date) {
  const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
  return months[date.getMonth()];
}

/**
 * Carrega o arquivo JSON de notícias para uma determinada data
 * @param {string} isoDate - Data no formato YYYY-MM-DD
 * @returns {Promise<Array|null>} - Retorna a lista de notícias ou null se não encontrar
 */
export async function fetchNewsByDate(isoDate) {
  // Cache busting dinâmico com timestamp em milissegundos para forçar o navegador a ignorar qualquer cache e baixar sempre o JSON atualizado
  const timestamp = new Date().getTime();
  const filePath = `./src/data/news/news_${isoDate}.json?v=${timestamp}`;
  console.log(`[News Portal] Buscando URL: ${filePath}`);
  
  try {
    const response = await fetch(filePath);
    console.log(`[News Portal] Status da resposta HTTP para ${isoDate}: ${response.status} ${response.statusText}`);
    if (!response.ok) {
      throw new Error(`Arquivo não encontrado para a data: ${isoDate} (HTTP ${response.status})`);
    }
    const data = await response.json();
    console.log(`[News Portal] JSON carregado com sucesso para ${isoDate}. Total de notícias: ${data ? data.length : 0}`);
    return data;
  } catch (error) {
    console.warn(`[News Portal] Erro ao carregar notícias para ${isoDate}:`, error.message);
    return null;
  }
}

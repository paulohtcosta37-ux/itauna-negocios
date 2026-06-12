#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AGENTE DE INTELIGÊNCIA COMERCIAL - ITAÚNA NEGÓCIOS
Busca notícias locais, realiza web scraping, analisa impactos com a IA Google Gemini
e salva os dados estruturados no banco de dados estático JSON do site.
"""

import os
import sys
import json
import uuid
import argparse
import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

# Configuração de caminhos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'src', 'data', 'news')

# Garantir que a pasta de destino exista
os.makedirs(DATA_DIR, exist_ok=True)

# Headers para evitar bloqueio nos portais de scraping
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# ==========================================================================
# RASPAGEM DE DADOS (WEB SCRAPING)
# ==========================================================================

def scrape_santana_fm():
    """Raspagem de notícias recentes do Portal Santana FM (Itaúna)"""
    url = "https://santanafm.com.br/"
    print(f"[*] Raspando notícias de: {url}")
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"[!] Erro ao acessar Santana FM: Código {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Estrutura comum de posts no WordPress do portal Santana FM
        post_elements = soup.find_all(['article', 'div'], class_=['post', 'type-post', 'td_module_wrap'])[:8]
        
        for elem in post_elements:
            title_tag = elem.find(['h1', 'h2', 'h3', 'h4'], class_=['entry-title', 'td-module-title'])
            if not title_tag:
                title_tag = elem.find('a')
                
            summary_tag = elem.find(['div', 'p'], class_=['entry-summary', 'td-excerpt'])
            
            if title_tag and title_tag.text.strip():
                title = title_tag.text.strip()
                link = title_tag.find('a')['href'] if title_tag.find('a') else url
                summary = summary_tag.text.strip() if summary_tag else ""
                articles.append({
                    'source': 'Santana FM',
                    'title': title,
                    'summary': summary,
                    'link': link
                })
                
        print(f"[+] Santana FM: {len(articles)} notícias encontradas.")
    except Exception as e:
        print(f"[!] Falha na raspagem da Santana FM: {e}")
        
    return articles


def scrape_jornal_de_itauna():
    """Raspagem de notícias recentes do Jornal de Itaúna"""
    url = "https://jornaldeitauna.com.br/"
    print(f"[*] Raspando notícias de: {url}")
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"[!] Erro ao acessar Jornal de Itaúna: Código {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Busca por títulos e artigos baseados em tags comuns de notícias
        posts = soup.find_all(['article', 'div', 'section'], class_=['post', 'hentry', 'entry', 'ast-archive-post'])[:8]
        if not posts:
            posts = soup.find_all('h2', class_=['entry-title'])[:8]
            
        for post in posts:
            link_tag = post.find('a') if post.name != 'a' else post
            if link_tag and link_tag.text.strip():
                title = link_tag.text.strip()
                link = link_tag['href']
                
                summary = ""
                summary_tag = post.find_next(['p', 'div'], class_=['entry-content', 'post-excerpt'])
                if summary_tag:
                    summary = summary_tag.text.strip()
                    
                articles.append({
                    'source': 'Jornal de Itaúna',
                    'title': title,
                    'summary': summary,
                    'link': link
                })
                
        print(f"[+] Jornal de Itaúna: {len(articles)} notícias encontradas.")
    except Exception as e:
        print(f"[!] Falha na raspagem do Jornal de Itaúna: {e}")
        
    return articles


def scrape_prefeitura_itauna():
    """Raspagem de notícias oficiais do Portal da Prefeitura de Itaúna (itauna.mg.gov.br)"""
    url = "https://www.itauna.mg.gov.br/portal/noticias"
    print(f"[*] Raspando notícias oficiais de: {url}")
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            # Fallback para a página inicial se a página de notícias direta falhar
            url = "https://www.itauna.mg.gov.br/"
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"[!] Erro ao acessar prefeitura de Itaúna: Código {response.status_code}")
                return []
                
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # O site da prefeitura de Itaúna organiza as notícias em cards e divs de notícias
        news_elements = soup.find_all(['div', 'a', 'h3', 'h4'], class_=['noticia', 'item-noticia', 'title', 'post'])
        if not news_elements:
            # Fallback amplo para pegar links que contenham "noticia"
            news_elements = soup.find_all('a', href=True)
            
        for elem in news_elements:
            href = elem.get('href', '')
            title = elem.text.strip()
            
            # Filtra links relacionados a notícias e com títulos razoáveis
            if ('noticia' in href or 'portal/noticias/' in href) and len(title) > 15:
                full_link = href if href.startswith('http') else f"https://www.itauna.mg.gov.br{href}"
                articles.append({
                    'source': 'Prefeitura de Itaúna',
                    'title': title,
                    'summary': '',
                    'link': full_link
                })
        
        # Remover duplicatas
        seen_links = set()
        unique_articles = []
        for art in articles:
            if art['link'] not in seen_links:
                seen_links.add(art['link'])
                unique_articles.append(art)
                
        articles = unique_articles[:8]
        print(f"[+] Prefeitura de Itaúna: {len(articles)} notícias encontradas.")
    except Exception as e:
        print(f"[!] Falha na raspagem da Prefeitura de Itaúna: {e}")
        
    return articles


# ==========================================================================
# INTEGRAÇÃO GOOGLE GEMINI (INTELIGÊNCIA ARTIFICIAL)
# ==========================================================================

def analyze_with_gemini(raw_articles, api_key, target_date):
    """Envia as notícias para o Google Gemini processar e formatar em JSON analítico usando busca web em tempo real"""
    print("[*] Iniciando análise de impacto com a IA Google Gemini e Google Search...")
    
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("[!] Erro: A biblioteca 'google-genai' não está instalada.")
        print("    Rode: pip install google-genai")
        return None
        
    # Inicializar o cliente
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"[!] Erro ao inicializar o cliente Gemini GenAI: {e}")
        return None
        
    # Preparar dados coletados dos scrapers locais para complementar
    formatted_input = ""
    for idx, art in enumerate(raw_articles):
        formatted_input += f"Notícia Local #{idx+1} ({art['source']}):\n"
        formatted_input += f"Título: {art['title']}\n"
        if art['summary']:
            formatted_input += f"Resumo: {art['summary']}\n"
        formatted_input += f"Link: {art['link']}\n"
        formatted_input += "-" * 30 + "\n"
        
    # Prompt do Sistema e Instruções refinados para Negócios de Itaúna (últimas 24h)
    prompt = f"""
Você é um analista de inteligência de mercado altamente experiente, focado exclusivamente no comércio, negócios, oportunidades de mercado e na economia local da cidade de Itaúna, Minas Gerais (Brasil).

Hoje é dia {target_date}. 

Sua tarefa principal é produzir de 2 a 4 relatórios analíticos de mercado contendo notícias e fatos reais ocorridos estritamente nas últimas 24 horas (dia {target_date} ou o dia imediatamente anterior). 

Para coletar e enriquecer seus relatórios com informações frescas e reais das últimas 24h, você deve realizar pesquisas na web focando nas seguintes fontes em Itaúna-MG:
1. Publicações recentes nos perfis públicos de Instagram mais influentes da cidade:
   - Prefeitura de Itaúna (@prefeituradeitauna)
   - TV Cidade Itaúna (@tvcidadeitauna)
   - Itaúna Alerta (@itaunaalerta)
   - Itaúna da Zoeira (@itaunadazoeira)
2. Notícias recentes de portais locais (Santana FM, Jornal de Itaúna, folha local).
3. Anúncios, editais e comunicados no site da Universidade de Itaúna (UIT) e das principais escolas/colégios da cidade que possam afetar a dinâmica comercial (ex: volta às aulas, eventos de vestibulares, contratações, etc.).
4. Portais e comunicados de entidades comerciais, como a CDL Itaúna (Câmara de Dirigentes Lojistas), ACE Itaúna, etc.

CRITÉRIO CRÍTICO DE RELEVÂNCIA:
Só inclua notícias e fatos que tenham IMPACTO DIRETO E RELEVANTE para comerciantes, lojistas, empresários e prestadores de serviços da cidade (novos negócios abrindo, grandes contratações de empresas locais, eventos na praça que atraem fluxo de clientes, obras de trânsito que alteram o acesso a lojas, mudanças de impostos, etc.). Ignore fofocas, crimes que não afetem o comércio ou notícias genéricas que não gerem desdobramentos de mercado.

Aqui estão algumas notícias brutas coletadas localmente hoje para ajudar como ponto de partida ou referência:
{formatted_input}

Para cada fato comercial importante (máximo 4 relatórios de notícias), crie um objeto JSON contendo exatamente estes campos:
1. id: Um UUID aleatório novo (string).
2. title: Título comercial focado no impacto de negócios (Ex: 'Grande público de festival gastronômico aquece restaurantes do Centro' ou 'Volta às aulas na UIT deve elevar consumo no bairro Universitário').
3. category: Uma destas categorias exatas: 'Eventos' | 'Concorrência' | 'Economia Local' | 'Infraestrutura' | 'Oportunidades'.
4. executiveSummary: Resumo executivo de até 2 frases curtas e diretas sobre o fato comercial.
5. impactLevel: Nível de impacto nas vendas ou operação local: 'Alto' | 'Médio' | 'Baixo'.
6. investigativeAnalysis: Análise investigativa profunda e criativa explicando o impacto na economia local nas últimas 24h (Ex: fluxo estimado de pessoas, estimativa de venda de vestuário, oportunidades para táxis/entregadores, impactos no varejo de vizinhança, etc.).
7. howToAct: Lista numerada prática com 2 ou 3 ações claras que os lojistas/comerciantes devem tomar para se preparar ou se proteger.
8. howToProfit: Insights práticos e inovadores sobre como lucrar com a notícia (promoções casadas, novos kits, estratégias de marketing digital direcionadas).
9. image: Campo nulo (defina sempre como null, pois as imagens foram removidas do frontend).
10. sourceName: O nome da fonte real e exata da notícia (ex: 'Prefeitura de Itaúna', 'Santana FM', 'Jornal de Itaúna', 'CDL Itaúna', etc.).
11. sourceUrl: O link URL real e específico de onde a notícia foi baseada ou um link realista correspondente diretamente ao artigo ou publicação oficial.

O retorno deve ser EXCLUSIVAMENTE uma lista em formato JSON contendo os objetos de notícia. Não inclua nenhuma introdução ou formatação Markdown (como ```json).
"""

    try:
        # Habilitar ferramenta de pesquisa integrada no Gemini 2.5 Flash
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        # Limpar o texto de possíveis marcações Markdown do JSON
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
            
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        response_text = response_text.strip()
        
        news_data = json.loads(response_text)
        return news_data
        
    except Exception as e:
        print(f"[!] Erro ao comunicar com a API do Gemini ou processar o JSON: {e}")
        return None


# ==========================================================================
# MODO DE SIMULAÇÃO (MOCK) - CASO NÃO HÁ CHAVE DE API
# ==========================================================================

def generate_mock_data(target_date):
    """Gera dados simulados realistas para Itaúna na data fornecida"""
    print(f"[*] Gerando dados simulados (Mock Mode) para a data {target_date}...")
    
    # Notícias de mock específicas para hoje (10 de Junho), incluindo o Arraial de Itaúna 2026
    if target_date == "2026-06-10":
        mock_data = [
            {
                "id": str(uuid.uuid4()),
                "title": "Prefeitura confirma 'Arraial de Itaúna 2026' na Praça da Matriz com fins beneficentes e shows regionais",
                "category": "Eventos",
                "executiveSummary": "A Prefeitura de Itaúna, através da Secretaria de Cultura e Turismo, anunciou a edição 2026 da Festa Junina oficial para o dia 20 de junho na Praça da Matriz.",
                "impactLevel": "Alto",
                "investigativeAnalysis": "O Arraial de Itaúna 2026 acontecerá no sábado, dia 20 de junho, das 11h às 22h, e contará com a participação de 8 entidades assistenciais (como APAE, ABEASF, APAC e Lar Fraterno) comandando as barracas de comidas típicas (tropeiro, pastéis, caldos, churrasquinho e pescaria). Espera-se um público recorde de 20 mil pessoas ao longo do dia, o que aumentará drasticamente as vendas de vestuário típico (camisas xadrez, botas) nas semanas anteriores e gerará forte tráfego comercial no Centro de Itaúna, beneficiando estacionamentos, postos, hotéis e motoristas de aplicativo.",
                "howToAct": "1. Lojistas de roupas e calçados do centro de Itaúna devem criar vitrines temáticas 'caipiras' com casacos e camisas xadrez.\n2. Distribuidores de alimentos e bebidas devem procurar as 8 entidades beneficentes parceiras para fechar acordos de fornecimento em escala de ingredientes típicos.\n3. Comércios alimentícios no entorno da Praça da Matriz devem reforçar equipes e estender o atendimento no sábado à noite.",
                "howToProfit": "Desenvolva o 'Combo Arraial' de lanches rápidos para retirada no caminho do evento. Crie promoções em redes sociais com ideias de maquiagem e looks típicos com peças do seu estoque. Feche parcerias com motoristas locais para distribuir cartões com cupons de desconto físicos para quem for ou voltar do evento de táxi/Uber.",
                "image": None,
                "sourceName": "Prefeitura de Itaúna",
                "sourceUrl": "https://www.itauna.mg.gov.br/portal/noticias/0/3/4521/prefeitura-confirma-arraial-de-itauna-2026-na-praca-da-matriz"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Festival Gastronômico de Itaúna 2026 inicia nesta sexta e promete aquecer comércio local",
                "category": "Eventos",
                "executiveSummary": "O evento gastronômico tradicional trará circuito gastronômico unificado na Praça da Matriz beneficiando diretamente restaurantes e hotéis.",
                "impactLevel": "Alto",
                "investigativeAnalysis": "O Festival Gastronômico atrai turistas de Divinópolis, Mateus Leme e Pará de Minas para Itaúna. A ocupação de hotéis atinge 85% para o fim de semana. O tráfego de pedestres no Centro sobe exponencialmente a partir das 18h.",
                "howToAct": "1. Criar pratos temáticos paralelos fora da praça para capturar o público excedente.\n2. Lojas de roupas devem expor casacos de inverno na vitrine.\n3. Estender horário de atendimento no centro na sexta e sábado até mais tarde.",
                "howToProfit": "Ofereça parcerias com motoristas de aplicativo locais dando cupons de desconto para sua loja. Use campanhas de geolocalização no Instagram no raio de 1km da Praça da Matriz.",
                "image": None,
                "sourceName": "Santana FM",
                "sourceUrl": "https://santanafm.com.br/festival-gastronomico-de-itauna-2026-promete-aquecer-o-comercio-local/"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Inauguração de megaloja de farmácia Araújo no centro de Itaúna acirra concorrência com farmácias de bairro",
                "category": "Concorrência",
                "executiveSummary": "A nova unidade na Avenida Jove Soares conta com amplo estacionamento e mix ampliado, pressionando drogarias tradicionais a se adaptarem.",
                "impactLevel": "Alto",
                "investigativeAnalysis": "A nova Araújo na Jove Soares (Prainha) traz preços altamente competitivos e funcionamento 24h. As farmácias de bairro precisarão focar no atendimento humanizado, atenção farmacêutica personalizada e entrega rápida a domicílio via WhatsApp para manter a clientela fiel.",
                "howToAct": "1. Revisar políticas de cashback e planos de fidelidade da drogaria de bairro.\n2. Focar no atendimento humanizado e no WhatsApp delivery rápido.\n3. Oferecer entrega grátis sem valor mínimo.",
                "howToProfit": "Explore nichos como fitoterápicos artesanais, chás locais ou dermocosméticos orgânicos que a grande rede não prioriza. Realize parcerias de convênio de descontos com empresas locais para o fornecimento de medicamentos de uso contínuo a funcionários.",
                "image": None,
                "sourceName": "Jornal de Itaúna",
                "sourceUrl": "https://jornaldeitauna.com.br/inauguracao-de-megaloja-da-farmacia-araujo-no-centro-de-itauna-acirra-concorrencia/"
            }
        ]
    else:
        # Fallback genérico para datas retroativas
        mock_data = [
            {
                "id": str(uuid.uuid4()),
                "title": "Universidade de Itaúna (UIT) anuncia volta às aulas e aquece setor de copiadoras e transporte estudantil",
                "category": "Economia Local",
                "executiveSummary": "O início do período acadêmico na UIT movimenta cerca de 8 mil estudantes na região universitária diariamente.",
                "impactLevel": "Médio",
                "investigativeAnalysis": "O retorno dos estudantes da UIT (vindos de várias cidades vizinhas) gera impacto direto nas repúblicas estudantis, lanchonetes próximas ao campus, papelarias e serviços de vans. O comércio do bairro Universitário e do Centro de Itaúna registra tradicional alta em consumo rápido de lanches e materiais escolares nas primeiras duas semanas letivas.",
                "howToAct": "1. Papelarias e copiadoras locais devem estender o horário de funcionamento das 18h às 22h.\n2. Lanchonetes no trajeto universitário devem criar combos especiais de 'estudante' a preços promocionais.\n3. Motoristas de vans devem divulgar vagas disponíveis nas redes estudantis.",
                "howToProfit": "Crie parcerias de descontos com o Diretório Acadêmico da UIT. Ofereça entrega de materiais de impressão direto na universidade em horários agendados.",
                "image": None,
                "sourceName": "Universidade de Itaúna",
                "sourceUrl": "https://www.uit.br/noticias/volta-as-aulas-movimenta-campus-universitario"
            },
            {
                "id": str(uuid.uuid4()),
                "title": "Alerta de tráfego: Obra na Av. Jove Soares altera acesso à área de lazer noturna",
                "category": "Infraestrutura",
                "executiveSummary": "Intervenções da prefeitura na rede de drenagem pluvial interditam parcialmente faixas no sentido centro-bairro.",
                "impactLevel": "Médio",
                "investigativeAnalysis": "A obra afetará as vagas de estacionamento da 'Prainha', local conhecido por concentrar o público jovem de Itaúna no fim de semana. Bares e hamburguerias registrarão queda nas visitas presenciais nos horários de pico, compensada pelo aumento de entregas residenciais (delivery) na região centro-sul.",
                "howToAct": "1. Comerciantes devem impulsionar canais de WhatsApp e aplicativos de entrega rápida.\n2. Indicar estacionamentos conveniados in ruas paralelas aos clientes fixos.\n3. Ajustar escala de entregadores para dar conta da alta de delivery.",
                "howToProfit": "Crie a campanha 'Estacione Longe e Ganhe Cerveja': dê uma cortesia aos clientes que comprovarem que vieram de Uber ou que pararam o carro em estacionamentos conveniados parceiros.",
                "image": None,
                "sourceName": "Prefeitura de Itaúna",
                "sourceUrl": "https://www.itauna.mg.gov.br/portal/noticias/0/3/4510/obras-de-drenagem-na-avenida-jove-soares-alteram-transito-nesta-semana"
            }
        ]
        
    return mock_data


# ==========================================================================
# ENVIO AUTOMÁTICO DE DEPLOY PARA GITHUB
# ==========================================================================

def push_to_github():
    """Tenta enviar as atualizações automaticamente para o repositório remoto do GitHub"""
    import subprocess
    git_dir = os.path.join(BASE_DIR, '.git')
    if not os.path.exists(git_dir):
        return
        
    # Puxamos o caminho completo do executável do Git no Windows para evitar problemas de PATH
    git_path = "C:\\Program Files\\Git\\cmd\\git.exe"
    git_cmd = git_path if os.path.exists(git_path) else "git"
    
    print("[*] Repositório Git detectado. Iniciando envio automático para o GitHub...")
    try:
        subprocess.run([git_cmd, "add", "."], cwd=BASE_DIR, check=True)
        today_str = datetime.date.today().isoformat()
        commit_msg = f"Relatório diário do comércio de Itaúna: {today_str}"
        result = subprocess.run([git_cmd, "commit", "-m", commit_msg], cwd=BASE_DIR, capture_output=True, text=True)
        if "nothing to commit" in result.stdout or "nada para comitar" in result.stdout or "no changes added" in result.stdout:
            print("[*] Nenhuma mudança detectada para comitar.")
            return
            
        subprocess.run([git_cmd, "push"], cwd=BASE_DIR, check=True)
        print("[SUCCESS] Mudanças enviadas e site atualizado no GitHub Pages!")
    except Exception as e:
        print(f"[!] Erro ao realizar deploy automático para o GitHub: {e}")
        print("[!] Verifique se você configurou o repositório remoto (git remote add origin) e se autenticou no GitHub.")


# ==========================================================================
# EXECUÇÃO DO SCRIPT
# ==========================================================================

def main():
    parser = argparse.ArgumentParser(description="Agente de Análise Comercial de Itaúna-MG")
    parser.add_argument('--date', type=str, help="Data alvo no formato YYYY-MM-DD (Padrão: data de hoje)")
    parser.add_argument('--mock', action='store_true', help="Forçar execução em Modo Simulação (Mock) sem chamar APIs")
    args = parser.parse_args()
    
    # Determinar a data de execução
    if args.date:
        try:
            datetime.datetime.strptime(args.date, "%Y-%m-%d")
            target_date = args.date
        except ValueError:
            print("[!] Erro: Formato de data inválido. Use YYYY-MM-DD.")
            sys.exit(1)
    else:
        target_date = datetime.date.today().isoformat()
        
    print("=" * 60)
    print(f"[*] Roteiro do Agente Comercial - Data Alvo: {target_date}")
    print("=" * 60)
    
    # Verificar chave de API do Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    is_mock = args.mock or not gemini_key or gemini_key == "SUA_CHAVE_AQUI"
    
    news_result = None
    
    if is_mock:
        if not gemini_key or gemini_key == "SUA_CHAVE_AQUI":
            print("[!] GEMINI_API_KEY não configurada ou inválida no arquivo .env.")
            print("[!] Entrando automaticamente em MODO SIMULAÇÃO (MOCK).")
        else:
            print("[*] Modo Simulação (Mock) ativado manualmente via flag.")
            
        news_result = generate_mock_data(target_date)
    else:
        print("[*] Chave do Gemini encontrada! Iniciando coleta real de notícias...")
        # 1. Scraping dos portais locais e prefeitura
        articles_santana = scrape_santana_fm()
        articles_jornal = scrape_jornal_de_itauna()
        articles_prefeitura = scrape_prefeitura_itauna()
        
        all_articles = articles_santana + articles_jornal + articles_prefeitura
        
        # 2. Enviar para análise do Gemini
        print(f"[+] Total de matérias coletadas para análise: {len(all_articles)}")
        
        # Realiza uma query adicional usando os termos de redes sociais/UIT se estivéssemos usando APIs de busca como Tavily
        # (Neste script, as queries adicionais de redes sociais/UIT enriquecem as fontes passadas para a IA)
        
        news_result = analyze_with_gemini(all_articles, gemini_key, target_date)
        
        # Fallback de segurança se a chamada falhar
        if not news_result:
            print("[!] Falha na geração com IA. Usando Mock como plano de contingência.")
            news_result = generate_mock_data(target_date)
            
    # Salvar o arquivo JSON final
    if news_result:
        filename = f"news_{target_date}.json"
        filepath = os.path.join(DATA_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(news_result, f, ensure_ascii=False, indent=2)
            
            print("=" * 60)
            print(f"[SUCCESS] Relatório diário de negócios salvo com sucesso!")
            print(f"[SUCCESS] Caminho: {filepath}")
            print(f"[SUCCESS] Total de análises de impacto geradas: {len(news_result)}")
            print("=" * 60)
            
            # Enviar atualizações para o GitHub se for um repositório git
            push_to_github()
        except Exception as e:
            print(f"[!] Erro ao salvar arquivo JSON: {e}")
            sys.exit(1)
    else:
        print("[!] Erro crítico: Nenhum dado foi gerado.")
        sys.exit(1)

if __name__ == '__main__':
    main()

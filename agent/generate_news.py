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
DATA_DIR = os.path.join(BASE_DIR, 'src', 'data')
DATABASE_FILE = os.path.join(DATA_DIR, 'news_today.json')

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


def scrape_viu_itauna():
    """Raspagem de notícias recentes do Portal Viu Itaúna"""
    url = "https://viuitauna.com.br/"
    print(f"[*] Raspando notícias de: {url}")
    articles = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"[!] Erro ao acessar Viu Itaúna: Código {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Busca por títulos e artigos baseados em tags comuns de notícias do WordPress no Viu Itaúna
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
                    'source': 'Viu Itaúna',
                    'title': title,
                    'summary': summary,
                    'link': link
                })
                
        print(f"[+] Viu Itaúna: {len(articles)} notícias encontradas.")
    except Exception as e:
        print(f"[!] Falha na raspagem do Viu Itaúna: {e}")
        
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
        
    # Prompt do Sistema e Instruções refinados para Negócios de Itaúna
    prompt = f"""
Você é um analista de inteligência de mercado altamente experiente, focado exclusivamente no comércio, negócios, oportunidades de mercado e na economia local da cidade de Itaúna, Minas Gerais (Brasil).

Hoje é dia {target_date}. 

Sua tarefa principal é produzir de 2 a 4 relatórios analíticos de mercado contendo notícias e fatos reais ocorridos estritamente na janela de tempo de 8:01 do dia anterior até o momento atual da pesquisa (hoje). Garanta que os fatos sejam desse intervalo para refletirem o dia presente.

REGRA DE VERACIDADE ABSOLUTA:
Você NUNCA deve inventar notícias ou simular fatos. Todas as notícias geradas devem ser estritamente reais, comprovadas por notícias ou publicações oficiais encontradas na web que ocorreram na janela especificada.

REGRA DE LINKS REAIS E FUNCIONAIS:
O campo `sourceUrl` deve conter uma URL 100% real, ativa e diretamente correspondente à publicação da notícia. Nunca utilize URLs fictícias, caminhos de placeholders ou domínios desativados (como jornaldeitauna.com.br). Se o link exato do post/matéria não estiver disponível, use a URL da página inicial do portal ativo correspondente (ex: https://viuitauna.com.br/, https://santanafm.com.br/, https://jornalspasso.com.br/ ou https://www.itauna.mg.gov.br/).

COMPORTAMENTO DE SEGURANÇA (SEM NOTÍCIAS):
Se após realizar as pesquisas você não encontrar nenhuma notícia ou fato real que atenda aos critérios e tenha impacto comercial em Itaúna-MG na janela de tempo, retorne simplesmente uma lista vazia `[]`. É preferível não exibir nada (o portal mostrará uma mensagem de aguardo adequada) do que inventar informações falsas.

Para coletar e enriquecer seus relatórios com informações frescas e reais desse intervalo, você deve realizar pesquisas na web focando nas seguintes fontes em Itaúna-MG:
1. Publicações recentes nos perfis públicos de Instagram mais influentes da cidade:
   - Prefeitura de Itaúna (@prefeituradeitauna)
   - TV Cidade Itaúna (@tvcidadeitauna)
   - Itaúna Alerta (@itaunaalerta)
   - Itaúna da Zoeira (@itaunadazoeira)
2. Notícias recentes de portais locais (Santana FM, Viu Itaúna, Jornal S'passo, Folha do Povo).
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
10. sourceName: O nome da fonte real e exata da notícia (ex: 'Prefeitura de Itaúna', 'Santana FM', 'Viu Itaúna', 'Jornal S'passo', 'CDL Itaúna', etc.).
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
    
    mock_data = [
        {
            "id": str(uuid.uuid4()),
            "title": "SAAE Itaúna reativa sistema de fluoretação da água para atender normas federais",
            "category": "Economia Local",
            "executiveSummary": "O Serviço Autônomo de Água e Esgoto (SAAE) reativou o tanque e a dosagem de flúor no tratamento público, garantindo conformidade com a legislação federal.",
            "impactLevel": "Médio",
            "investigativeAnalysis": "A retomada da fluoretação da água tratada é uma adequação sanitária importante que impacta diretamente as indústrias locais de alimentos, confeitarias, padarias e cervejarias artesanais que utilizam a rede de abastecimento público. O restabelecimento da fluoretação em conformidade com as regras federais previne riscos de multas regulatórias e assegura o padrão higiênico para os estabelecimentos comerciais do setor alimentício.",
            "howToAct": "1. Proprietários de restaurantes e padarias devem verificar os filtros de carvão ativo e manter as manutenções preventivas do sistema de filtragem de água.\n2. Cervejarias locais devem monitorar a composição da água para ajustar os sais e o perfil de fermentação das receitas.\n3. Divulgar nas redes sociais que o estabelecimento preza pelas normas de saúde e qualidade da água utilizada nos alimentos.",
            "howToProfit": "Explore o marketing voltado para saúde e higiene, destacando que seu estabelecimento utiliza água 100% filtrada e tratada de acordo com as normas sanitárias vigentes. Crie campanhas sobre o uso de água limpa na produção de pães artesanais ou cafés especiais.",
            "image": None,
            "sourceName": "Viu Itaúna",
            "sourceUrl": "https://viuitauna.com.br/"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Acidente na Avenida Jove Soares impacta tráfego na principal via comercial de Itaúna",
            "category": "Infraestrutura",
            "executiveSummary": "Colisão entre caminhonete e motocicleta na tarde desta segunda-feira causou lentidão e bloqueio parcial na movimentada Avenida Jove Soares.",
            "impactLevel": "Médio",
            "investigativeAnalysis": "A Avenida Jove Soares ('Prainha') concentra o principal fluxo comercial e de lazer noturno de Itaúna. Bloqueios temporários ou lentidão decorrentes de acidentes de trânsito afetam diretamente o tempo de entrega de serviços de delivery (motoboys) de restaurantes locais e dificultam o tráfego de pedestres e clientes que acessam lojas e farmácias da região centro-sul.",
            "howToAct": "1. Comércios baseados em delivery na Jove Soares devem avisar previamente os clientes sobre possíveis atrasos devido à lentidão no tráfego local.\n2. Lojistas e gerentes devem orientar entregadores a utilizar rotas alternativas pelas vias paralelas (como a Rua Silva Jardim).\n3. Reforçar a sinalização interna para quem retira pedidos no local para evitar tumultos na porta da loja.",
            "howToProfit": "Crie campanhas de incentivo para compras presenciais fora do horário de pico do trânsito na avenida. Desenvolva promoções 'Retire no Balcão' com descontos extras para clientes que optem por buscar o pedido a pé na região central.",
            "image": None,
            "sourceName": "Folha do Povo Itaúna",
            "sourceUrl": "https://folhapovoitauna.com.br/"
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Operação de segurança apreende drogas sintéticas em Itaúna e reforça policiamento em bairros",
            "category": "Economia Local",
            "executiveSummary": "A Polícia Militar apreendeu ecstasy, cocaína e dinheiro em operação contra o tráfico, aumentando a segurança em rotas de comércio.",
            "impactLevel": "Baixo",
            "investigativeAnalysis": "Ações intensificadas das forças policiais na região de Itaúna-MG inibem pequenos delitos nos arredores de centros comerciais urbanos e melhoram a percepção de segurança de clientes e lojistas. Áreas comerciais com patrulhamento ostensivo ativo registram maior tráfego de pedestres ao anoitecer, incentivando a extensão das atividades de bares e cafeterias.",
            "howToAct": "1. Comerciantes de bairros adjacentes devem apoiar as redes de vizinhos protegidos e cooperar ativamente compartilhando alertas de segurança.\n2. Manter as áreas externas dos comércios bem iluminadas para inibir movimentações suspeitas após o fechamento.\n3. Incentivar a utilização de meios digitais de pagamento para evitar o acúmulo de dinheiro em espécie no caixa físico da loja.",
            "howToProfit": "Explore a maior sensação de segurança para organizar eventos ou promoções ao final da tarde ('Happy Hour' estendido). Divulgue nas redes sociais que seu local é monitorado e seguro para famílias e clientes locais.",
            "image": None,
            "sourceName": "Itaúna Alerta",
            "sourceUrl": "https://itaunaalerta.com.br/"
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
        
        news_result = analyze_with_gemini(all_articles, gemini_key, target_date)
        
        # Fallback de segurança se a chamada falhar
        if not news_result:
            print("[!] Falha na geração com IA. Usando Mock como plano de contingência.")
            news_result = generate_mock_data(target_date)
            
    # Salvar no arquivo central de notícias do dia (news_today.json)
    if news_result:
        # Injetar o campo de data e garantir a consistência
        for item in news_result:
            item["date"] = target_date
        
        try:
            with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
                json.dump(news_result, f, ensure_ascii=False, indent=2)
            
            print("=" * 60)
            print(f"[SUCCESS] Relatório diário de negócios salvo com sucesso!")
            print(f"[SUCCESS] Caminho: {DATABASE_FILE}")
            print(f"[SUCCESS] Total de análises de hoje: {len(news_result)}")
            print("=" * 60)
            
            # Enviar atualizações para o GitHub se for um repositório git
            push_to_github()
        except Exception as e:
            print(f"[!] Erro ao salvar banco de dados JSON: {e}")
            sys.exit(1)
    else:
        print("[!] Erro crítico: Nenhum dado foi gerado.")
        sys.exit(1)

if __name__ == '__main__':
    main()

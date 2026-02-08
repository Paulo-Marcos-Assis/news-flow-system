import requests
from bs4 import BeautifulSoup
import json

def get_real_article_url(page_url):
    """Busca um link de artigo real na página de listagem"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(page_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procurar por links que parecem ser artigos (geralmente têm título/texto)
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Filtros para identificar artigos
            if (href and text and len(text) > 20 and 
                not any(skip in href.lower() for skip in ['javascript:', '#', 'mailto:', 'categoria', 'category', 'tag', 'author', 'page', 'pagina']) and
                not any(skip in text.lower() for skip in ['menu', 'contato', 'sobre', 'anuncie', 'assine', 'login', 'buscar'])):
                
                # Construir URL completa
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(page_url)
                    return f"{parsed.scheme}://{parsed.netloc}{href}"
        
        return None
    except Exception as e:
        print(f"Erro ao buscar artigo: {e}")
        return None

def analyze_article_detailed(article_url):
    """Analisa detalhadamente a estrutura de um artigo"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"  Analisando artigo: {article_url}")
        response = requests.get(article_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Título (h1)
        h1 = soup.find('h1')
        title_info = {
            'tag': 'h1',
            'class': h1.get('class', []) if h1 else None,
            'text': h1.get_text(strip=True)[:100] if h1 else None
        }
        
        # Data (time ou elementos com 'date' no class)
        date_info = []
        time_tags = soup.find_all('time')
        for t in time_tags[:3]:
            date_info.append({
                'tag': 'time',
                'class': t.get('class', []),
                'datetime': t.get('datetime'),
                'text': t.get_text(strip=True)[:50]
            })
        
        # Se não encontrou time, buscar por class com 'date'
        if not date_info:
            for tag in ['span', 'div', 'p']:
                elements = soup.find_all(tag, class_=True)
                for el in elements:
                    classes = ' '.join(el.get('class', []))
                    if 'date' in classes.lower() or 'data' in classes.lower():
                        date_info.append({
                            'tag': tag,
                            'class': el.get('class', []),
                            'text': el.get_text(strip=True)[:50]
                        })
                        if len(date_info) >= 3:
                            break
                if len(date_info) >= 3:
                    break
        
        # Subtítulo/Chamada
        subtitle_info = []
        for tag in ['h2', 'p', 'div']:
            elements = soup.find_all(tag, class_=True)
            for el in elements[:10]:
                classes = ' '.join(el.get('class', []))
                if any(kw in classes.lower() for kw in ['subtitle', 'chamada', 'lead', 'excerpt', 'resumo', 'deck']):
                    subtitle_info.append({
                        'tag': tag,
                        'class': el.get('class', []),
                        'text': el.get_text(strip=True)[:100]
                    })
                    break
            if subtitle_info:
                break
        
        # Conteúdo (div com muitos parágrafos)
        content_info = []
        for tag in ['article', 'div']:
            elements = soup.find_all(tag, class_=True)
            for el in elements:
                classes = ' '.join(el.get('class', []))
                paragraphs = el.find_all('p')
                if len(paragraphs) >= 3:  # Artigo geralmente tem vários parágrafos
                    content_info.append({
                        'tag': tag,
                        'class': el.get('class', []),
                        'paragraph_count': len(paragraphs)
                    })
                    if len(content_info) >= 2:
                        break
            if len(content_info) >= 2:
                break
        
        return {
            'url': article_url,
            'title': title_info,
            'date': date_info[:3],
            'subtitle': subtitle_info[:1],
            'content': content_info[:2]
        }
        
    except Exception as e:
        print(f"  Erro: {e}")
        return {'url': article_url, 'error': str(e)}

# Configurações manuais baseadas na análise
sites_config = {
    '4oito': {
        'base_url': 'https://www.4oito.com.br/ultimas-noticias',
        'test_page': 'https://www.4oito.com.br/ultimas-noticias',
        'pagination_pattern': None  # Precisa verificar se tem paginação
    },
    'ajnoticias': {
        'base_url': 'https://ajnoticias.com.br/ultimas-noticias/pagina/{}',
        'test_page': 'https://ajnoticias.com.br/ultimas-noticias/pagina/1',
        'pagination_pattern': 'https://ajnoticias.com.br/ultimas-noticias/pagina/{}'
    },
    'clickcamboriu': {
        'base_url': 'https://clickcamboriu.com.br/geral/page/{}',
        'test_page': 'https://clickcamboriu.com.br/geral/page/1',
        'pagination_pattern': 'https://clickcamboriu.com.br/geral/page/{}'
    },
    'blogdoprisco': {
        'base_url': 'https://www.blogdoprisco.com.br/noticias/page/{}/',
        'test_page': 'https://www.blogdoprisco.com.br/noticias/page/1/',
        'pagination_pattern': 'https://www.blogdoprisco.com.br/noticias/page/{}/'
    },
    'estado': {
        'base_url': 'https://estado.sc.gov.br/noticias/todas-as-noticias/page/{}/',
        'test_page': 'https://estado.sc.gov.br/noticias/todas-as-noticias/page/1/',
        'pagination_pattern': 'https://estado.sc.gov.br/noticias/todas-as-noticias/page/{}/'
    },
    'olharsc': {
        'base_url': 'https://olharsc.com.br/category/noticias/page/{}',
        'test_page': 'https://olharsc.com.br/category/noticias/',
        'pagination_pattern': 'https://olharsc.com.br/category/noticias/page/{}'
    },
    'gazetadopovo': {
        'base_url': 'https://www.gazetadopovo.com.br/ultimas-noticias/{}/',
        'test_page': 'https://www.gazetadopovo.com.br/ultimas-noticias/1/',
        'pagination_pattern': 'https://www.gazetadopovo.com.br/ultimas-noticias/{}/'
    },
    'correiosc': {
        'base_url': 'https://www.correiosc.com.br/categoria/estado/page/{}/',
        'test_page': 'https://www.correiosc.com.br/categoria/estado/page/1/',
        'pagination_pattern': 'https://www.correiosc.com.br/categoria/estado/page/{}/'
    },
    'diariodosul': {
        'base_url': 'https://diariodosul.com.br/geral/pagina-{}',
        'test_page': 'https://diariodosul.com.br/geral/pagina-1',
        'pagination_pattern': 'https://diariodosul.com.br/geral/pagina-{}'
    },
    'ederluiz': {
        'base_url': 'https://ederluiz.com.vc/ultimas-noticias/page/{}/',
        'test_page': 'https://ederluiz.com.vc/ultimas-noticias/page/1/',
        'pagination_pattern': 'https://ederluiz.com.vc/ultimas-noticias/page/{}/'
    }
}

if __name__ == '__main__':
    results = {}
    
    print("Analisando estrutura detalhada dos sites...\n")
    
    for name, config in sites_config.items():
        print(f"{'='*60}")
        print(f"Site: {name}")
        print(f"Página de teste: {config['test_page']}")
        
        # Buscar um artigo real
        article_url = get_real_article_url(config['test_page'])
        
        if article_url:
            print(f"  ✅ Artigo encontrado: {article_url[:80]}...")
            analysis = analyze_article_detailed(article_url)
            results[name] = {
                'base_url': config['base_url'],
                'pagination_pattern': config['pagination_pattern'],
                'analysis': analysis
            }
        else:
            print(f"  ❌ Nenhum artigo encontrado")
            results[name] = {
                'base_url': config['base_url'],
                'pagination_pattern': config['pagination_pattern'],
                'error': 'No article found'
            }
        
        print()
    
    # Salvar resultados
    with open('detailed_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"{'='*60}")
    print("Análise completa! Resultados salvos em detailed_analysis.json")

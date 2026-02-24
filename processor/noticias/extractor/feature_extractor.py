import os
import json
from typing import List, Dict, Optional
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

# ===========================
# CONFIGURAÇÕES (Carregadas de Var. de Ambiente ou Padrão)
# ===========================
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama-dev.ceos.ufsc.br")
SELECTED_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
LLM_TEMPERATURE = 0

# ===========================
# FUNÇÕES AUXILIARES
# ===========================
def normalize_edital(edital_str: Optional[str]) -> Optional[str]:
    """Remove zeros à esquerda do número do edital (ex: 005/2023 -> 5/2023)."""
    if edital_str is None:
        return None
    editorial = str(edital_str).strip()
    parts = editorial.split('/')
    if len(parts) == 2:
        num_norm = parts[0].lstrip('0')
        if not num_norm:
            num_norm = '0'
        return f"{num_norm}/{parts[1]}"
    else:
        return editorial

# ===========================
# CLASSE PRINCIPAL
# ===========================
class FeatureExtractor:
    def __init__(self):
        print(f"Feature Extractor configurado para usar Ollama em {OLLAMA_HOST} (modelo: {SELECTED_MODEL})")
        self.llm = None
        self._llm_initialized = False
    
    def _ensure_llm(self):
        """Lazy initialization do LLM - só conecta quando realmente precisar"""
        if not self._llm_initialized:
            print(f"Conectando ao Ollama em {OLLAMA_HOST}...")
            try:
                self.llm = ChatOllama(
                    model=SELECTED_MODEL,
                    base_url=OLLAMA_HOST,
                    temperature=LLM_TEMPERATURE,
                    timeout=120
                )
                self._llm_initialized = True
                print("Conexão com Ollama estabelecida com sucesso!")
            except Exception as e:
                print(f"ERRO ao conectar ao Ollama: {e}")
                self.llm = None
                self._llm_initialized = True

    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        Recebe o texto bruto da notícia e retorna o dicionário extraído.
        """
        default_return = {"municipio": [], "modalidade": [], "edital": [], "objeto": []}
        
        # Garante que o LLM está inicializado
        self._ensure_llm()
        
        if not self.llm:
            print("Erro: LLM não inicializado.")
            return default_return
        
        if not text or not isinstance(text, str):
            return default_return

        
        prompt_content = f"""
Você é um especialista em análise de notícias sobre licitações públicas.
Sua tarefa é identificar e extrair, de forma precisa e sem inferências, atributos específicos presentes **explicitamente** no texto.

Essas informações serão utilizadas posteriormente para cruzamento com bases públicas de licitações. Portanto, siga rigorosamente as regras de extração e normalização.

----------------------------------------------------------------------
INSTRUÇÕES GERAIS:
- Leia o todo o texto da notícia.
- Extraia SOMENTE informações que apareçam de forma explícita.
- Não faça inferências, não complete ausências e não reformule conteúdos.
- Para cada atributo, retorne uma lista (array). 
- Use [] quando não houver ocorrências.
- Remova duplicatas.
- A resposta deve ser APENAS um JSON válido.

----------------------------------------------------------------------
1) município:
- **O objetivo é encontrar o município relacionado à licitação**
- **Identifique e extraia o(s) município(s) que o texto da notícia aborda**.

Considerações:
- Se o texto mencionar vários municípios, mas um deles for claramente o principal, aquele que publicou o edital de licitação; aquele em que a fraude ocorre, retorne apenas o município principal. 
- Se o texto mencionar diversos municípios e todos tiverem a mesma importância, retorne a lista com todos os municípios
- Se no texto não houver menção de nenhum município, não retorne nada (vazio que será preenchido por [])
- Se houver menção de municípios que não são do estado de Santa Catarina, não retorne nada (vazio que será preenchido por [])

- Normalizações:
  - Remova expressões como "cidade de" ou "município de".
  - Mantenha apenas o nome principal.
  - Exemplo: "cidade de Florianópolis" → "Florianópolis"
  
### Exemplo few-shot:

Notícia 1:
"Operação mira 18 prefeituras de Santa Catarina por suspeita de fraude (...) a CNN apurou que 18 prefeituras do estado são alvos de busca e apreensão. São elas: São Miguel do Oeste, Guaraciaba, São José do Cedro, Bom Jesus do Oeste, Princesa, Bandeirantes, Flor do Sertão, São João do Oeste, Santa Helena, Sul Brasil, Descanso, Riqueza, Mondaí, Cordilheira Alta, Jardinópolis, Rio Fortuna, Águas Mornas e Antônio Carlos."

Saída esperada:
{{
  "municipio_ente": "São Miguel do Oeste, Guaraciaba, São José do Cedro, Bom Jesus do Oeste, Princesa, Bandeirantes, Flor do Sertão, São João do Oeste, Santa Helena, Sul Brasil, Descanso, Riqueza, Mondaí, Cordilheira Alta, Jardinópolis, Rio Fortuna, Águas Mornas e Antônio Carlos"
}}

Notícia 2:
"a polícia civil de santa catarina, por meio da 5ª delegacia especializada no combate à corrupção (5ª decor/chapecó), deflagrou uma operação na data de hoje, 02/05/2024, que resultou no cumprimento de nove mandados de busca e apreensão e três mandados de prisão nos municípios de quilombo/sc, são lourenço do oeste/sc e pato branco/pr.

a ação é um desdobramento da investigação de supostas fraudes em licitações no setor de obras do município de quilombo/sc, além de outras infrações penais correlatas, como formação de organização criminosa, lavagem de dinheiro e advocacia administrativa.
"
Note que: pelo eixo da fraude ser o municíio de quilombo/sc "*supostas fraudes em licitações no setor de obras do município de quilombo/sc*",a saída esperada nesse caso é:

Saída esperada:
{{
  "municipio_ente": "quilombo"
}}

----------------------------------------------------------------------
2) modalidade:
Extraia a modalidade de licitação **somente se claramente identificada como modalidade**.

Modalidades válidas (exemplos):
- pregão presencial
- pregão eletrônico 
- concorrência
- concorrência presencial
- concorrência eletrônica
- convite
- tomada de preços
- dispensa de licitação
- inexigibilidade de licitação
- leilão
- concurso (apenas quando modalidade de licitação, não para concurso público)
- regime diferenciado de contratação (RDC)

REGRAS DE NORMALIZAÇÃO:
- Converter plurais para singular (ex: "pregões" → "pregão").
- "dispensa" (singular ou plural) → normalizar para "dispensa de licitação".
- "concorrência pública" → normalizar para apenas "concorrência".
- "concorrência" → só extraia quando for CERTEZA que refere-se à modalidade.

O QUE IGNORAR (NÃO EXTRAIR EM NENHUMA HIPÓTESE):
- “registro de preço” ou “sistema de registro de preço”.
- “pregão público” (termo genérico).
- “concorrência” usada no sentido de competição (ex: “frustrar a concorrência”).
- “concurso” usado para seleção de pessoal (ex: "concurso público para cargos").

----------------------------------------------------------------------
3) edital:
- Extraia o número do edital quando presente.
- Normalizar para formato "NUMERO/ANO".
- Exemplos:
  - "Edital nº 123/2023" → "123/2023"
  - "pregão número 24 de 2022" → "24/2022"

----------------------------------------------------------------------
4) objeto:

objeto — descreve o que está sendo licitado (por exemplo: construção de obra, prestação de serviços, registro de preços, fornecimento de materiais, etc.)

A seguir, somente como exemplo, estão 6 amostras de como esses objetos podem aparecer nas notícias. Mas não se limite a elas! Outros tipos podem surgir. Apenas use-as como referência de contexto:

[<
"tinha como objeto o registro de preços para a contratação de serviços de horas-máquina, como motoniveladoras e rolos compactadores.";
"Construção da obra da chamada rua coberta no Município de Praia Grande, no Sul de Santa Catarina.";
"contratar empresa especializada em roçada e limpeza geral de áreas externas dos seus imóveis";
"fraudes em processos licitatórios no setor de coleta e destinação de resíduos sólidos no município de Pescaria Brava";
"Calçamento e asfaltamento";
"compra de livros e materiais didáticos para a área da educação"
>]

*Retorne exatamente o trecho da notícia que identifica o objeto.*

Retorne o resultado exclusivamente no formato JSON a seguir:
{{
  "objeto": "texto extraído ou []"
}}
----------------------------------------------------------------------
FORMATO DE RESPOSTA:
Retorne APENAS um JSON válido, no formato:

{{
  "municipio": [],
  "modalidade": [],
  "edital": [],
  "objeto": []
}}

Texto da notícia:
\"\"\"{text}\"\"\"

Responda APENAS com o JSON válido, sem texto adicional.
"""
        # ==============================================================================

        try:
            # Invoca o LLM com uma única mensagem humana (seu prompt completo)
            response = self.llm.invoke([HumanMessage(content=prompt_content)])
            
            result = response.content.strip()
            return self._parse_json_response(result, default_return)

        except Exception as e:
            # Em produção, logamos o erro mas não paramos o pipeline
            print(f"[Erro na Extração] {e}")
            return default_return

    def _parse_json_response(self, result_str: str, default_return: Dict) -> Dict:
        """
        Limpa e valida o JSON retornado pelo modelo.
        """
        # Limpeza de blocos de código Markdown (comum em LLMs)
        if result_str.startswith("```json"):
            result_str = result_str[7:]
        if result_str.startswith("```"):
            result_str = result_str[3:]
        if result_str.endswith("```"):
            result_str = result_str[:-3]
        
        result_str = result_str.strip()

        try:
            data = json.loads(result_str)
            
            # Garante a estrutura de saída
            out = {}
            for key in ["municipio", "modalidade", "edital", "objeto"]:
                value = data.get(key, [])
                
                # Força formato de lista de strings
                if isinstance(value, str):
                    value = [value] if value.strip() else []
                elif isinstance(value, (int, float)):
                    value = [str(value)]
                elif not isinstance(value, list):
                    value = []

                # Remove duplicatas e strings vazias
                clean_list = []
                seen = set()
                for item in value:
                    s = str(item).strip()
                    # Remove aspas duplas ou simples no início e fim
                    s = s.strip('"').strip("'").strip()
                    if s and s not in seen:
                        clean_list.append(s)
                        seen.add(s)
                
                out[key] = clean_list

            # Aplica normalização específica de editais
            out['edital'] = [normalize_edital(e) for e in out.get('edital', []) if e]

            return out

        except json.JSONDecodeError:
            print(f"Falha ao decodificar JSON. Início da resposta: {result_str[:50]}...")
            return default_return
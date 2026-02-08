import os
import json
from sqlalchemy import create_engine, text
from service_essentials.utils.logger import Logger
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

class NoticiaLicitacaoLinker(BasicProducerConsumerService):
    def __init__(self):
        # A classe pai valida filas e conecta ao Mongo no init.
        # As variáveis de ambiente são "mockadas" no bloco __main__ lá embaixo.
        super().__init__()
        self.logger.info("Iniciando Linker (Modo Híbrido: Banco ou JSON Direto)")
        
        # Conexão com Postgres (usa variável de ambiente para o nome do banco)
        db_name = os.getenv('DATABASE_PG', 'local')
        self.db_engine = self._setup_database_connection(db_name)
        
        # Configuração do LLM para desambiguação
        self.ollama_host = os.getenv('OLLAMA_HOST', 'https://ollama-dev.ceos.ufsc.br')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:32b-instruct')
        self.llm = None
        self._llm_initialized = False
        self.logger.info(f"LLM configurado: {self.ollama_model} @ {self.ollama_host}")

    def _setup_database_connection(self, db_name: str):
        print(f"[DEBUG] Tentando conectar ao banco: '{db_name}'...")
        try:
            db_user = os.getenv('USERNAME_PG', 'postgres')
            db_password = os.getenv('SENHA_PG', 'admin')
            db_host = os.getenv('HOST_PG', 'localhost')
            db_port = os.getenv('PORT_PG', '5432')
            
            print(f"[DEBUG] Config: {db_user}@{db_host}:{db_port}/{db_name}")
            
            if not all([db_user, db_password, db_host, db_port, db_name]):
                print("[DEBUG] ERRO: Variáveis de ambiente incompletas.")
                return None

            db_connection_str = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
            engine = create_engine(db_connection_str)
            
            # Testa a conexão imediatamente para garantir que funciona
            with engine.connect() as conn:
                print("[DEBUG] Conexão física estabelecida com sucesso!")
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
                    conn.commit()
                except Exception as ex:
                    print(f"[DEBUG] Aviso (pg_trgm): {ex}")

            return engine
        except Exception as e:
            print(f"\n[DEBUG] ERRO FATAL DE CONEXÃO: {e}\n")
            return None

    def process_message(self, record):
        """
        Processa mensagem do RabbitMQ (tópico db_events, binding insert.noticias).
        Formato esperado: {"routing_key": "insert.noticias", "ids_gerados_db": {...}}
        """
        self.logger.info(f"Mensagem recebida: {record}")
        
        # 1. Extração do ID da Notícia (mensagem real do inserter-updater)
        ids = record.get("ids_gerados_db", {}).get("inserted_ids", {})
        id_noticia = ids.get("noticia")
        
        # Fallback para formatos antigos ou testes manuais
        if not id_noticia:
            id_noticia = record.get("ids_gerados_db", {}).get("data", {}).get("insert", {}).get("noticia")

        if not id_noticia:
            # Modo de teste: tenta extrair dados do JSON diretamente
            self.logger.info("[TESTE] ID da notícia não encontrado. Tentando modo simulação...")
            dados_para_match = self.extrair_dados_json(record)
            
            if not dados_para_match:
                self.logger.warning("ID da notícia não encontrado e dados insuficientes para simulação. Ignorando.")
                return None
            
            # Executa match sem persistir no banco
            candidatos = self.buscar_candidatos_licitacao(dados_para_match)
            
            if len(candidatos) == 1:
                self.logger.info(f" [TESTE] MATCH encontrado: Processo {candidatos[0]} (sem persistência)")
                return {"status": "linked", "id_processo_licitatorio": candidatos[0], "test_mode": True}
            elif len(candidatos) > 1:
                self.logger.warning(f" [TESTE] AMBIGUIDADE: {len(candidatos)} processos encontrados.")
                return None
            else:
                self.logger.info(" [TESTE] Nenhum match encontrado.")
                return None

        # 2. Busca os dados da Notícia no Banco (modo produção)
        dados_noticia = self.buscar_dados_noticia_banco(id_noticia)
        
        if not dados_noticia:
            self.logger.warning(f"Notícia {id_noticia} não encontrada ou sem dados suficientes.")
            return None

        self.logger.info(f"Processando Notícia {id_noticia} | Edital: '{dados_noticia.get('numero_edital')}' | Mun ID: {dados_noticia.get('id_municipio')}")

        # 3. Executa a Lógica de Match (Cascata SQL + Similaridade)
        candidatos = self.buscar_candidatos_licitacao(dados_noticia)

        # 4. Análise de Resultados
        if len(candidatos) == 1:
            # SUCESSO: Match único e perfeito
            id_processo_match = candidatos[0]
            self.atualizar_noticia(id_noticia, id_processo_match)
            
            self.logger.info(f" MATCH SUCESSO! Notícia {id_noticia} vinculada ao Processo {id_processo_match}")
            return {
                "noticia": {
                    "id_noticia": id_noticia,
                    "id_processo_licitatorio": id_processo_match,
                    "status": "linked"
                }
            }
        
        elif len(candidatos) > 1:
            # AMBIGUIDADE: Muitos processos parecidos.
            # Usa LLM para comparar o 'objeto' e desempatar.
            self.logger.warning(f" AMBIGUIDADE: {len(candidatos)} processos encontrados. Iniciando desambiguação via LLM...")
            
            id_processo_match = self.desambiguar_com_llm(id_noticia, dados_noticia, candidatos)
            
            if id_processo_match:
                self.atualizar_noticia(id_noticia, id_processo_match)
                self.logger.info(f" DESAMBIGUAÇÃO SUCESSO! Notícia {id_noticia} vinculada ao Processo {id_processo_match} (via LLM)")
                return {
                    "noticia": {
                        "id_noticia": id_noticia,
                        "id_processo_licitatorio": id_processo_match,
                        "status": "linked_via_llm"
                    }
                }
            else:
                self.logger.warning(f" DESAMBIGUAÇÃO FALHOU: LLM não conseguiu determinar o melhor match para Notícia {id_noticia}.")
                return None
            
        else:
            self.logger.info(f" Nenhum match encontrado para Notícia {id_noticia}.")
            return None

    def extrair_dados_json(self, record):
        """Extrai dados do JSON e converte nomes em IDs (Município/Modalidade)"""
        print("[DEBUG] Entrou em extrair_dados_json...")
        try:
            noticia = record.get('noticia', {})
            municipio_json = record.get('municipio', {})
            modalidade_json = record.get('modalidade_licitacao', {})

            # 1. Resolver Município
            nome_municipio = municipio_json.get('nome_municipio')
            print(f"[DEBUG] Buscando ID para o município: '{nome_municipio}'")
            
            id_municipio = self.resolver_id_municipio(nome_municipio)
            
            if not id_municipio:
                print(f"[DEBUG] ERRO: Município '{nome_municipio}' não encontrado no banco!")
                # DICA: Liste alguns municípios do banco para ver como estão escritos
                return None
            
            print(f"[DEBUG] ID do Município encontrado: {id_municipio}")

            # 2. Resolver Modalidade
            id_modalidade = modalidade_json.get('id')
            if not id_modalidade:
                id_modalidade = noticia.get('id_modalidade_licitacao')
            
            print(f"[DEBUG] ID da Modalidade: {id_modalidade}")

            return {
                'numero_edital': noticia.get('numero_edital'),
                'id_municipio': id_municipio,
                'id_modalidade_licitacao': id_modalidade
            }
        except Exception as e:
            print(f"[DEBUG] EXCEPTION em extrair_dados_json: {e}")
            import traceback
            traceback.print_exc()
            return None

    def resolver_id_municipio(self, nome_municipio):
        if not nome_municipio: 
            print("[DEBUG] Nome do município veio vazio.")
            return None
            
        nome_limpo = nome_municipio.strip()
        
        # 1. TENTATIVA EXATA (Mais rápida e segura)
        query_exata = text("SELECT id_municipio, nome_municipio FROM public.municipio WHERE nome_municipio ILIKE :nome LIMIT 1;")
        
        # 2. TENTATIVA PARCIAL (Coringa % - para casos como "Mun. de Balneário Rincão")
        query_parcial = text("SELECT id_municipio, nome_municipio FROM public.municipio WHERE nome_municipio ILIKE :nome LIMIT 1;")
        
        # 3. TENTATIVA POR SIMILARIDADE (Salva casos de acentuação errada)
        # Requer pg_trgm instalado. Se falhar, retorna erro mas não quebra.
        query_similar = text("""
            SELECT id_municipio, nome_municipio, SIMILARITY(nome_municipio, :nome) as score 
            FROM public.municipio 
            WHERE SIMILARITY(nome_municipio, :nome) > 0.4 
            ORDER BY score DESC LIMIT 1;
        """)

        try:
            with self.db_engine.connect() as conn:
                # Tentativa 1: Exata
                print(f"[DEBUG] Tentando match EXATO para: '{nome_limpo}'")
                res = conn.execute(query_exata, {"nome": nome_limpo}).fetchone()
                if res:
                    print(f"[DEBUG] Match Exato: ID={res[0]} ({res[1]})")
                    return res[0]

                # Tentativa 2: Parcial (%nome%)
                print(f"[DEBUG] Tentando match PARCIAL para: '%{nome_limpo}%'")
                res = conn.execute(query_parcial, {"nome": f"%{nome_limpo}%"}).fetchone()
                if res:
                    print(f"[DEBUG] Match Parcial: ID={res[0]} ({res[1]})")
                    return res[0]
                
                # Tentativa 3: Similaridade
                print(f"[DEBUG] Tentando match SIMILARIDADE para: '{nome_limpo}'")
                try:
                    res = conn.execute(query_similar, {"nome": nome_limpo}).fetchone()
                    if res:
                        print(f"[DEBUG] Match Similaridade: ID={res[0]} ({res[1]}) - Score: {res[2]}")
                        return res[0]
                except Exception as e_sim:
                    print(f"[DEBUG] Aviso: Busca por similaridade falhou (pg_trgm ausente?): {e_sim}")

                print(f"[DEBUG] NENHUM município encontrado para '{nome_limpo}'")
                return None

        except Exception as e:
            print(f"[DEBUG] ERRO SQL ao resolver municipio: {e}")
            return None

    def buscar_dados_noticia_banco(self, id_noticia):
        """
        Busca atributos da notícia e o ID do município via tabela de relacionamento.
        """
        query = text("""
            SELECT 
                n.id_noticia,
                n.numero_edital,
                n.id_modalidade_licitacao,
                n.objeto,
                nm.id_municipio
            FROM public.noticia n
            LEFT JOIN public.noticia_municipio nm ON n.id_noticia = nm.id_noticia
            WHERE n.id_noticia = :id_noticia
            LIMIT 1;
        """)
        
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(query, {"id_noticia": id_noticia}).mappings().fetchone()
                if result:
                    return dict(result)
                return None
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados da notícia: {e}")
            return None

    def buscar_candidatos_licitacao(self, noticia):
        """
        Executa a CASCATA de relacionamentos:
        Municipio -> Ente -> Unidade Gestora -> Processo Licitatorio
        
        E aplica a SIMILARIDADE no Edital e Modalidade (descrição textual).
        """
        id_municipio = noticia.get('id_municipio')
        id_modalidade = noticia.get('id_modalidade_licitacao')
        edital_texto = noticia.get('numero_edital')

        # Filtro 1 (Rigoroso): Município é obrigatório para começar a cascata e garantir contexto
        if not id_municipio:
            self.logger.warning("Notícia sem município. Impossível filtrar entes/UGs.")
            return []

        # Tratamento do Edital para Similaridade
        if not edital_texto or str(edital_texto).lower() in ['nan', 'null', 'none', '']:
             self.logger.info("Notícia sem número de edital válido. Busca cancelada.")
             return []

        # Busca a descrição textual da modalidade (se tiver ID)
        modalidade_descricao = None
        if id_modalidade:
            try:
                with self.db_engine.connect() as conn:
                    query_modalidade = text("SELECT descricao FROM public.modalidade_licitacao WHERE id_modalidade_licitacao = :id_mod LIMIT 1;")
                    result = conn.execute(query_modalidade, {"id_mod": id_modalidade}).fetchone()
                    if result:
                        modalidade_descricao = result[0]
                        self.logger.info(f"Modalidade encontrada: '{modalidade_descricao}' (ID: {id_modalidade})")
            except Exception as e:
                self.logger.warning(f"Erro ao buscar descrição da modalidade: {e}")

        # --- QUERY SQL DE CASCATA + SIMILARIDADE ---
        # Implementa a lógica testada no pgAdmin com SIMILARITY em edital E modalidade
        
        query_sql = """
            SELECT 
                pl.id_processo_licitatorio,
                pl.numero_edital,
                ml.descricao as modalidade_descricao,
                SIMILARITY(pl.numero_edital, :edital_texto) as score_edital,
                SIMILARITY(ml.descricao, :modalidade_texto) as score_modalidade,
                (SIMILARITY(pl.numero_edital, :edital_texto) + SIMILARITY(ml.descricao, :modalidade_texto)) / 2.0 as score_total
            FROM public.processo_licitatorio pl
            
            -- JOIN com modalidade_licitacao para comparar descrição textual
            JOIN public.modalidade_licitacao ml ON pl.id_modalidade_licitacao = ml.id_modalidade_licitacao
            
            -- CASCATA RIGOROSA: Processo -> UG -> Ente -> Municipio
            JOIN public.unidade_gestora ug ON pl.id_unidade_gestora = ug.id_unidade_gestora
            JOIN public.ente e ON ug.id_ente = e.id_ente
            
            WHERE 
                e.id_municipio = :id_municipio
                
                -- LÓGICA DE SIMILARIDADE DE EDITAL
                AND (
                    SIMILARITY(pl.numero_edital, :edital_texto) > 0.5
                    OR pl.numero_edital ILIKE '%' || :edital_texto || '%'
                )
        """
        
        params = {
            "id_municipio": id_municipio,
            "edital_texto": edital_texto,
            "modalidade_texto": modalidade_descricao or ""  # String vazia se não tiver modalidade
        }

        # Filtro de SIMILARIDADE da Modalidade (se tiver descrição)
        if modalidade_descricao:
            query_sql += " AND SIMILARITY(ml.descricao, :modalidade_texto) > 0.5 "
            self.logger.info(f"Aplicando filtro de similaridade para modalidade: '{modalidade_descricao}'")

        # Ordena pelo score combinado (edital + modalidade)
        query_sql += " ORDER BY score_total DESC, score_edital DESC;"

        try:
            with self.db_engine.connect() as conn:
                results = conn.execute(text(query_sql), params).mappings().fetchall()
                
                ids_encontrados = [row['id_processo_licitatorio'] for row in results]
                
                if ids_encontrados:
                    self.logger.info(f"Candidatos encontrados via Cascata + Similaridade:")
                    for row in results[:3]:  # Mostra top 3
                        self.logger.info(f"  - ID: {row['id_processo_licitatorio']} | Edital: {row['numero_edital']} | "
                                       f"Score Edital: {row['score_edital']:.2f} | Score Modalidade: {row['score_modalidade']:.2f} | "
                                       f"Score Total: {row['score_total']:.2f}")
                
                return ids_encontrados

        except Exception as e:
            self.logger.error(f"Erro na query de match: {e}")
            return []

    def _ensure_llm(self):
        """Lazy initialization do LLM - só conecta quando realmente precisar"""
        if not self._llm_initialized:
            self.logger.info(f"Conectando ao Ollama em {self.ollama_host}...")
            try:
                self.llm = ChatOllama(
                    model=self.ollama_model,
                    base_url=self.ollama_host,
                    temperature=0,
                    timeout=120
                )
                self._llm_initialized = True
                self.logger.info("Conexão com Ollama estabelecida com sucesso!")
            except Exception as e:
                self.logger.error(f"ERRO ao conectar ao Ollama: {e}")
                self.llm = None
                self._llm_initialized = True

    def desambiguar_com_llm(self, id_noticia, dados_noticia, candidatos_ids):
        """
        Usa LLM para desambiguar entre múltiplos processos licitatórios candidatos.
        Compara o 'objeto' da notícia com os atributos dos processos.
        
        Retorna o ID do processo mais adequado ou None se não conseguir decidir.
        """
        # Busca informações dos processos candidatos
        processos_info = self.buscar_info_processos(candidatos_ids)
        
        if not processos_info:
            self.logger.warning("Não foi possível buscar informações dos processos candidatos.")
            return None
        
        # Verifica se todos os processos são idênticos (duplicatas no banco)
        if self._sao_processos_duplicados(processos_info):
            id_escolhido = processos_info[0]['id_processo_licitatorio']
            self.logger.info(f"Processos candidatos são duplicatas no banco. Escolhendo ID: {id_escolhido}")
            return id_escolhido
        
        # Busca o objeto da notícia
        objeto_noticia = dados_noticia.get('objeto', '')
        
        # Se não tem objeto, não consegue desambiguar via LLM
        if not objeto_noticia or str(objeto_noticia).lower() in ['nan', 'null', 'none', '']:
            self.logger.warning("Notícia sem objeto definido. Processos não são duplicatas. Impossível desambiguar.")
            return None
        
        # Tenta desambiguar via LLM usando o objeto
        self._ensure_llm()
        
        if not self.llm:
            self.logger.error("LLM não disponível para desambiguação.")
            return None
        
        # Monta o prompt para o LLM
        prompt = self._montar_prompt_desambiguacao(objeto_noticia, processos_info)
        
        try:
            self.logger.info("Enviando requisição ao LLM para desambiguação...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            result = response.content.strip()
            
            # Parse da resposta JSON
            id_escolhido = self._parse_resposta_llm(result)
            
            if id_escolhido and id_escolhido in candidatos_ids:
                self.logger.info(f"LLM escolheu o processo ID: {id_escolhido}")
                return id_escolhido
            else:
                self.logger.warning(f"LLM retornou ID inválido ou não encontrado: {id_escolhido}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro durante desambiguação com LLM: {e}")
            return None
    
    def buscar_info_processos(self, ids_processos):
        """
        Busca informações dos processos licitatórios candidatos.
        Retorna lista de dicts com {id, numero_edital, municipio, modalidade}
        Nota: objeto não existe na tabela processo_licitatorio, apenas em noticia.
        """
        if not ids_processos:
            return []
        
        ids_str = ','.join(str(id) for id in ids_processos)
        
        query = text(f"""
            SELECT 
                pl.id_processo_licitatorio,
                pl.numero_edital,
                m.nome_municipio,
                ml.descricao as modalidade
            FROM public.processo_licitatorio pl
            LEFT JOIN public.unidade_gestora ug ON pl.id_unidade_gestora = ug.id_unidade_gestora
            LEFT JOIN public.ente e ON ug.id_ente = e.id_ente
            LEFT JOIN public.municipio m ON e.id_municipio = m.id_municipio
            LEFT JOIN public.modalidade_licitacao ml ON pl.id_modalidade_licitacao = ml.id_modalidade_licitacao
            WHERE pl.id_processo_licitatorio IN ({ids_str})
        """)
        
        try:
            with self.db_engine.connect() as conn:
                results = conn.execute(query).mappings().fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            self.logger.error(f"Erro ao buscar informações dos processos: {e}")
            return []
    
    def _sao_processos_duplicados(self, processos_info):
        """
        Verifica se todos os processos candidatos são duplicatas
        (mesmo edital, mesmo município, mesma modalidade).
        """
        if len(processos_info) < 2:
            return False
        
        primeiro = processos_info[0]
        edital_ref = primeiro.get('numero_edital', '').strip().lower()
        municipio_ref = primeiro.get('nome_municipio', '').strip().lower()
        modalidade_ref = primeiro.get('modalidade', '').strip().lower()
        
        for proc in processos_info[1:]:
            edital = proc.get('numero_edital', '').strip().lower()
            municipio = proc.get('nome_municipio', '').strip().lower()
            modalidade = proc.get('modalidade', '').strip().lower()
            
            if edital != edital_ref or municipio != municipio_ref or modalidade != modalidade_ref:
                return False
        
        return True
    
    def _montar_prompt_desambiguacao(self, objeto_noticia, processos_info):
        """
        Monta o prompt para o LLM comparar o objeto da notícia com os objetos dos processos.
        """
        processos_texto = ""
        for i, proc in enumerate(processos_info, 1):
            processos_texto += f"\n{i}. ID: {proc['id_processo_licitatorio']}\n"
            processos_texto += f"   Edital: {proc.get('numero_edital', 'N/A')}\n"
            processos_texto += f"   Município: {proc.get('nome_municipio', 'N/A')}\n"
            processos_texto += f"   Modalidade: {proc.get('modalidade', 'N/A')}\n"
            processos_texto += f"   Objeto: {proc.get('objeto', 'Não informado')}\n"
        
        prompt = f"""Você é um especialista em análise de licitações públicas.

Sua tarefa é identificar qual processo licitatório corresponde melhor à notícia, analisando o objeto (descrição do que está sendo licitado) mencionado na notícia.

**OBJETO MENCIONADO NA NOTÍCIA:**
{objeto_noticia}

**PROCESSOS CANDIDATOS:**{processos_texto}

**CONTEXTO:**
Todos os processos candidatos já foram pré-filtrados e possuem o mesmo número de edital, município e modalidade da notícia. Sua tarefa é identificar qual deles melhor corresponde ao objeto descrito na notícia.

**INSTRUÇÕES:**
1. Analise o objeto mencionado na notícia
2. Compare com as características de cada processo candidato (edital, município, modalidade)
3. Identifique qual processo é mais provável de ser o mencionado na notícia
4. Considere o contexto semântico e possíveis variações de nomenclatura
5. **ATENÇÃO:** Processos com o mesmo número de edital mas de municípios DIFERENTES são processos distintos
6. Se não for possível determinar com razoável confiança qual processo corresponde à notícia, retorne null

**FORMATO DE RESPOSTA:**
Retorne APENAS um JSON válido no formato:
{{
  "id_processo_escolhido": <ID do processo> ou null,
  "justificativa": "breve explicação da escolha"
}}

Responda APENAS com o JSON, sem texto adicional."""
        
        return prompt
    
    def _parse_resposta_llm(self, resposta_str):
        """
        Faz parse da resposta JSON do LLM e extrai o ID escolhido.
        """
        # Limpeza de blocos de código Markdown
        if resposta_str.startswith("```json"):
            resposta_str = resposta_str[7:]
        if resposta_str.startswith("```"):
            resposta_str = resposta_str[3:]
        if resposta_str.endswith("```"):
            resposta_str = resposta_str[:-3]
        
        resposta_str = resposta_str.strip()
        
        try:
            data = json.loads(resposta_str)
            id_escolhido = data.get('id_processo_escolhido')
            justificativa = data.get('justificativa', 'Sem justificativa')
            
            self.logger.info(f"Justificativa do LLM: {justificativa}")
            
            return id_escolhido
        except json.JSONDecodeError as e:
            self.logger.error(f"Falha ao decodificar JSON da resposta LLM: {e}")
            self.logger.error(f"Resposta recebida: {resposta_str[:200]}...")
            return None

    def atualizar_noticia(self, id_noticia, id_processo):
        """
        Salva o match na tabela noticia.
        """
        query = text("""
            UPDATE public.noticia
            SET id_processo_licitatorio = :id_processo
            WHERE id_noticia = :id_noticia;
        """)
        try:
            with self.db_engine.begin() as conn: 
                conn.execute(query, {"id_processo": id_processo, "id_noticia": id_noticia})
                self.logger.info(f"[UPDATE] Notícia {id_noticia} atualizada com processo {id_processo}")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar notícia no banco: {e}")


if __name__ == '__main__':
    import os
    import sys
    
    # Verifica se está em modo de teste local (variável de ambiente TEST_MODE)
    test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
    
    if test_mode:
        # --- MODO TESTE LOCAL ---
        print("[SETUP] Executando em MODO TESTE LOCAL")
        
        # Mock do MongoDB
        try:
            from service_essentials.document_storage_manager.document_storage_manager_factory import DocumentStorageManagerFactory
            
            class DummyMongoManager:
                def save_document(self, *args, **kwargs):
                    pass
                    
            DocumentStorageManagerFactory.get_document_storage_manager = lambda: DummyMongoManager()
            print("[SETUP] Mock do MongoDB aplicado com sucesso.")
        except ImportError:
            print("[SETUP] Aviso: Não foi possível importar a Factory do Mongo.")

        # Variáveis de ambiente para teste local
        os.environ['INPUT_QUEUE'] = 'fila_teste_in'
        os.environ['OUTPUT_QUEUE'] = 'fila_teste_out'
        
        if not os.getenv('USERNAME_PG'): os.environ['USERNAME_PG'] = 'admin'
        if not os.getenv('SENHA_PG'):    os.environ['SENHA_PG'] = 'admin' 
        if not os.getenv('HOST_PG'):     os.environ['HOST_PG'] = 'localhost'
        if not os.getenv('PORT_PG'):     os.environ['PORT_PG'] = '5433'

        print(f"[SETUP] Conectando ao Postgres em localhost...")
        
        Logger(log_to_console=True)
        
        try:
            linker = NoticiaLicitacaoLinker()
            
            print("\n" + "="*40)
            print(" INICIANDO TESTE MANUAL (CROSS-REFERENCE)")
            print("="*40 + "\n")
            
            msg_teste = {
              "noticia": {
                "numero_edital": "PL 184/2021",
                "texto": "Texto simulado para teste de match..." 
              },
              "municipio": {
                "nome_municipio": "Balneário Rincão"
              },
              "modalidade_licitacao": {
                "descricao": "Procedimento Licitatório Lei 13.303/06",
                "id": 16 
              }
            }
            
            resultado = linker.process_message(msg_teste)
            
            print("\n" + "="*40)
            print(f" RESULTADO FINAL: {resultado}")
            print("="*40 + "\n")

        except Exception as e:
            print(f"\n[ERRO CRÍTICO NO TESTE]: {e}")
            import traceback
            traceback.print_exc()
    else:
        # --- MODO PRODUÇÃO (DOCKER) ---
        print("[SETUP] Executando em MODO PRODUÇÃO")
        Logger(log_to_console=True)
        
        try:
            linker = NoticiaLicitacaoLinker()
            print("[SETUP] Serviço iniciado. Aguardando mensagens do RabbitMQ...")
            linker.start()
        except KeyboardInterrupt:
            print("\n[SETUP] Serviço interrompido pelo usuário.")
        except Exception as e:
            print(f"\n[ERRO CRÍTICO]: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
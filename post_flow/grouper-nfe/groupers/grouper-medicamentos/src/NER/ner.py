
# -*- coding: utf-8 -*-
"""
Este script realiza o Named Entity Recognition (NER) para encontrar menções de medicamentos
em uma única descrição de nota fiscal, utilizando o Apache Solr e um banco PostgreSQL.

A lógica foi invertida em relação ao processo em lote: os medicamentos da base de conhecimento (PG)
são indexados no Solr, e a descrição de entrada é usada para buscar nesses dados.
"""

import logging
import re
import time
import pysolr
import sqlalchemy  # ADICIONADO
from sqlalchemy import text  # ADICIONADO
# from SPARQLWrapper import SPARQLWrapper, JSON # REMOVIDO


class NerProcessor:
    """
    Processador NER que inicializa com dados de medicamentos de um endpoint SPARQL,
    indexa-os no Solr e fornece um método para processar uma única descrição.
    """

    def __init__(self, solr_url: str, db_connection_string: str, score_threshold: float = 0.0): # MUDOU AQUI
        """
        Inicializa o processador, conecta-se aos serviços e indexa os medicamentos.
        """
        logging.info("Inicializando o NerProcessor...")
        self.solr = pysolr.Solr(
            "https://solr.ceos.ufsc.br/solr/medicamentos",
            timeout=120,
            auth=("solr", "RuleBasedAuthorizationPlugin") 
        )
        
        # MUDANÇAS AQUI
        # self.sparql_endpoint = sparql_endpoint # REMOVIDO
        self.db_engine = sqlalchemy.create_engine(db_connection_string) # ADICIONADO
        
        self.score_threshold = score_threshold
        
        # MUDOU AQUI
        # self.medications = self._get_enriched_medications_from_db() # Nome da função mudou
        
        # self._index_medications_in_solr()

    # ESTA FUNÇÃO FOI RENOMEADA E SEU CONTEÚDO TROCADO
    def _get_enriched_medications_from_db(self) -> list:
        """
        Consulta o banco PostgreSQL para recuperar uma lista de todos os medicamentos.
        """
        logging.info("Buscando medicamentos do PostgreSQL...")
        
        query_sql = text("""
            SELECT 
                g.apresentacao_registro AS registro_apresentacao, 
                g.nomecomercial AS nome_medicamento, 
                g.manufacturer AS manufacturer, 
                g.active_ingredient AS nome_principio_ativo, 
                g.dosage_form AS forma_farmaceutica,
                g.dosage_form_quantity AS qtde_dosage_form,         
                g.concentration_value AS concentracao,
                g.groupid AS id_grupo,
                g.packaging
            FROM 
                validacao.agrupamento_medicamentos_pedro_v0 g
        """)

        medications = []
        
        with self.db_engine.connect() as connection:
            results = connection.execute(query_sql)
            
            for row in results.mappings():
                medications.append({
                    "registro": str(row.registro_apresentacao),
                    "nome": row.nome_medicamento,
                    "principio_ativo": row.nome_principio_ativo,
                    "manufacturer": row.manufacturer,
                    "forma_farmaceutica": row.forma_farmaceutica or "",
                    "qtde_dosage_form": row.qtde_dosage_form,
                    "concentracao": row.concentracao,
                    "id_grupo": str(row.id_grupo),
                    "packaging": row.packaging
                })
        
        if medications:
            logging.info(f"Primeiro medicamento recuperado: {medications[0]}")
        logging.info(f"{len(medications)} medicamentos recuperados do PostgreSQL.")
        return medications

    #
    # NENHUMA MUDANÇA DAQUI PARA BAIXO
    #


    def _index_medications_in_solr(self):
        """
        Indexa a lista de medicamentos no Solr em lotes menores para evitar timeout/conexão fechada.
        """
        logging.info("Iniciando indexação de medicamentos no Solr...")
        if not self.medications:
            logging.warning("Nenhum medicamento para indexar.")
            return

        solr_docs = []
        for med in self.medications:
            text_search = f"{med['nome']} {med['principio_ativo']}"
            solr_docs.append({
                "id": med['registro'],
                "nome_med": med["nome"],
                "principio_ativo": med["principio_ativo"],
                "manufacturer": med["manufacturer"],
                "forma_farmaceutica": med["forma_farmaceutica"],
                "qtde_dosage_form": med.get("qtde_dosage_form"),
                "concentracao": med.get("concentracao"),
                "id_grupo": med.get("id_grupo"),
                "packaging": med.get("packaging"),
                "text_search": text_search,
            })

        # Limpa o índice antes de reindexar
        logging.info("Limpando o índice do Solr...")
        self.solr.delete(q='*:*', commit=True)

        total = len(solr_docs)
        batch_size = 1000
        logging.info(f"Indexando {total} medicamentos no Solr em lotes de {batch_size}...")

        for i in range(0, total, batch_size):
            batch = solr_docs[i:i + batch_size]
            attempt = 0
            while attempt < 3:
                try:
                    self.solr.add(batch, commit=False)
                    logging.info(f"Lote {i // batch_size + 1} / {total // batch_size + 1} indexado ({len(batch)} docs)")
                    break
                except Exception as e:
                    attempt += 1
                    wait = 5 * attempt
                    logging.warning(f"Erro ao indexar lote {i // batch_size + 1}: {e} – tentativa {attempt}/3. Aguardando {wait}s...")
                    time.sleep(wait)
            else:
                logging.error(f"Falha definitiva ao indexar lote {i // batch_size + 1}. Prosseguindo com os demais lotes.")

        # Commit final
        try:
            self.solr.commit()
            logging.info("✅ Indexação de medicamentos concluída com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao realizar commit final no Solr: {e}")


    def _query_solr_by_description(self, description: str, query_operator: str = "AND", rows: int = 50) -> list:
        """
        Busca no Solr usando os tokens da descrição de entrada.
        """
        tokens = re.findall(r'\w+', description.lower())
        if not tokens:
            return []

        # Constrói a query para buscar em nome_med ou principio_ativo
        query_parts = [f'(nome_med:{token} OR principio_ativo:{token})' for token in tokens]
        query_string = f' {query_operator} '.join(query_parts)

        try:
            results = self.solr.search(query_string, **{'fl': '*,score', 'rows': rows})
            docs = []
            for doc in results:
                docs.append({
                    "id": str(doc.get('id')).strip(),
                    "nome_med": doc.get('nome_med', ''),
                    "principio_ativo": doc.get('principio_ativo', ''),
                    "manufacturer": doc.get('manufacturer', ''),
                    "forma_farmaceutica": doc.get('forma_farmaceutica', ''),
                    "qtde_dosage_form": doc.get('qtde_dosage_form', ''),
                    "concentracao": doc.get('concentracao', ''),
                    "id_grupo": doc.get('id_grupo', ''),
                    "packaging": doc.get('packaging', ''),
                    "score": doc.get('score', 0),
                })
            return docs
        except Exception as e:
            logging.error(f"Erro na consulta ao Solr para a descrição '{description}': {e}")
            return []

    def process_description(self, description: str) -> list:
        """
        Processa uma única descrição, buscando por medicamentos candidatos no índice Solr.
        Tenta primeiro uma busca de alta precisão (AND) e, se falhar, uma de baixa precisão (OR).
        """
        logging.info(f"Processando descrição com NER: '{description}'")

        # 1. Busca de alta precisão com operador AND
        search_results = self._query_solr_by_description(description, query_operator="AND")

        # 2. Fallback para busca de baixa precisão com operador OR se não houver resultados
        if not search_results:
            logging.info("Nenhum resultado com a query AND, tentando com a query OR.")
            search_results = self._query_solr_by_description(description, query_operator="OR")

        # 3. Formata os resultados no formato esperado pelo restante do pipeline
        candidates = []
        for result in search_results:
            # Aplica o threshold de score, se definido
            if self.score_threshold and result['score'] < self.score_threshold:
                continue

            # Recria a string de informação do candidato como nos scripts originais
            info_str = (
                f"nome medicamento: {result['nome_med']} - "
                f"principio ativo: {result['principio_ativo']} - "
                f"manufacturer: {result['manufacturer']} - "
                f"forma_farmaceutica: {result['forma_farmaceutica']} - "
                f"qtde_dosage_form: {result.get('qtde_dosage_form', '')} - "
                f"concentracao: {result.get('concentracao', '')}"
            ).strip()

            result['info'] = info_str
            result['registro'] = result['id']
            candidates.append(result)

        logging.info(f"Encontrados {len(candidates)} candidatos para a descrição '{description}'")
        if candidates:
            logging.info(f"Primeiro candidato: {candidates[0]}")
        return candidates
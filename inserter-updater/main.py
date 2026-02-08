import os
import json
import time
import re
from datetime import datetime
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import psycopg2

# Assumindo que o logger é importado assim, como nos outros serviços
from service_essentials.utils.logger import Logger
from service_essentials.basic_service.basic_producer_consumer_service import (
    BasicProducerConsumerService,
)
from service_essentials.orientdb_manager.orient_ceos_client import CeosOrientDBClient
from service_essentials.relational_storage.relational_storage_manager_factory import RelationalStorageManagerFactory

# Instancia o logger para ser usado no módulo
logger = Logger()


class InserterUpdater(BasicProducerConsumerService):

    def __init__(self):
        super().__init__()
        self.fk_map = self.load_json("./db_identifiers/fks.json")
        self.table_insert_order = self.load_json("./db_identifiers/insert_order.json")
        self.table_identifiers = self.load_json("./db_identifiers/identifiers.json")
        self.relationship_tables = self.load_json("./db_identifiers/relationship_tables.json")
        self.primary_keys = self.load_json("./db_identifiers/primary_keys.json")
        
        # Controle de uso do OrientDB via variável de ambiente
        self.use_orientdb = os.getenv("USE_ORIENTDB", "true").lower() in ("true", "1", "yes")
        
        if self.use_orientdb:
            self.orient_client = CeosOrientDBClient(
                    host=os.getenv("HOST_ORIENT"),
                    port=os.getenv("PORT_ORIENT"),
                    username=os.getenv("USERNAME_ORIENT"),
                    password=os.getenv("SENHA_ORIENT"),
                    graph_name=os.getenv("DATABASE_ORIENT")
                )
            logger.info("OrientDB habilitado")
        else:
            self.orient_client = None
            logger.warning("OrientDB DESABILITADO via variável USE_ORIENTDB")
        
        self.db_manager = RelationalStorageManagerFactory.get_relational_storage_manager()


    def shutdown(self):
        """Método para fechar recursos (conexões) de forma limpa."""
        logger.info("Iniciando o desligamento do InserterUpdater...")
        if self.db_manager:
            self.db_manager.close_connection()
        # Se sua classe base tiver um método de shutdown, chame-o também
        # super().shutdown()

    def load_json(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def extract_postgres_error_details(self, exception):
        """
        Extrai detalhes completos de uma exceção do PostgreSQL.
        
        Args:
            exception: Exceção capturada
            
        Returns:
            dict: Dicionário com detalhes completos do erro
        """
        error_details = {
            "type": type(exception).__name__,
            "message": str(exception),
        }
        
        # Se for uma exceção do psycopg2, extrair detalhes adicionais
        if isinstance(exception, psycopg2.Error):
            # pgerror: mensagem de erro completa do PostgreSQL
            if hasattr(exception, 'pgerror') and exception.pgerror:
                error_details["postgres_error"] = exception.pgerror
            
            # pgcode: código de erro do PostgreSQL (ex: 23505 para duplicate key)
            if hasattr(exception, 'pgcode') and exception.pgcode:
                error_details["postgres_code"] = exception.pgcode
            
            # diag: objeto de diagnóstico com informações detalhadas
            if hasattr(exception, 'diag'):
                diag = exception.diag
                diag_info = {}
                
                # Extrair todos os atributos de diagnóstico disponíveis
                if hasattr(diag, 'severity'):
                    diag_info["severity"] = diag.severity
                if hasattr(diag, 'sqlstate'):
                    diag_info["sqlstate"] = diag.sqlstate
                if hasattr(diag, 'message_primary'):
                    diag_info["message_primary"] = diag.message_primary
                if hasattr(diag, 'message_detail'):
                    diag_info["message_detail"] = diag.message_detail
                if hasattr(diag, 'message_hint'):
                    diag_info["message_hint"] = diag.message_hint
                if hasattr(diag, 'statement_position'):
                    diag_info["statement_position"] = diag.statement_position
                if hasattr(diag, 'internal_position'):
                    diag_info["internal_position"] = diag.internal_position
                if hasattr(diag, 'internal_query'):
                    diag_info["internal_query"] = diag.internal_query
                if hasattr(diag, 'context'):
                    diag_info["context"] = diag.context
                if hasattr(diag, 'schema_name'):
                    diag_info["schema_name"] = diag.schema_name
                if hasattr(diag, 'table_name'):
                    diag_info["table_name"] = diag.table_name
                if hasattr(diag, 'column_name'):
                    diag_info["column_name"] = diag.column_name
                if hasattr(diag, 'datatype_name'):
                    diag_info["datatype_name"] = diag.datatype_name
                if hasattr(diag, 'constraint_name'):
                    diag_info["constraint_name"] = diag.constraint_name
                
                if diag_info:
                    error_details["postgres_diagnostics"] = diag_info
        
        return error_details
    
    def _is_date_string(self, value: str) -> bool:
        """Verifica se uma string está no formato de data (YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS)"""
        if not isinstance(value, str):
            return False
        # Formato de data: YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS
        date_pattern = r'^\d{4}-\d{2}-\d{2}'
        return bool(re.match(date_pattern, value.strip()))

    def get_primary_key(self, table, fk_map):
        # Check if table has explicit primary key mapping (for tables that don't follow id_{table} pattern)
        if table in self.primary_keys:
            return self.primary_keys[table]
        
        # CNPJ and CPF are unique identifiers, not primary keys
        # Primary keys are always id_{table} format
        for t, fks in fk_map.items():
            for _, (ref_table, ref_pk) in fks.items():
                if ref_table == table:
                    return ref_pk
        return f"id_{table}"

    def is_relationship_table(self, table):
        """Verifica se a tabela é uma tabela de relacionamento (many-to-many)."""
        return table in self.relationship_tables and self.relationship_tables[table].get("is_relationship_table", False)

    def get_composite_keys(self, table):
        """Retorna as chaves compostas de uma tabela de relacionamento."""
        if table in self.relationship_tables:
            return self.relationship_tables[table].get("composite_keys", [])
        return []

    def converter_datas(self, obj):
        if isinstance(obj, dict):
            return {k: self.converter_datas(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.converter_datas(v) for v in obj]
        elif isinstance(obj, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    dt = datetime.strptime(obj, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return obj  # Retorna original se nenhum formato bater
        else:
            return obj

        
    def get_postgres_columns(self, columns, table, cursor, schema='public'):
        cursor.execute(
            "SELECT * FROM schema_dinamico(%s, %s)",
            (table, schema)
        )
        try:
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        except Exception as e:
            logger.error(e)
            return []

        columns_list = [col['column_name'] for col in result]
        postgres_columns = [col for col in columns if col in columns_list]
        return postgres_columns


    def check_pessoa_exists_by_document(self, cursor, dados_completos: dict):
        """
        Verifica se uma pessoa já existe através do CNPJ ou CPF nas tabelas relacionadas.
        Retorna o id_pessoa se encontrado, None caso contrário.
        """
        # Verifica se há pessoa_pessoa_juridica com CNPJ
        if 'pessoa_pessoa_juridica' in dados_completos:
            pj_data = dados_completos['pessoa_pessoa_juridica']
            if isinstance(pj_data, dict) and 'cnpj' in pj_data:
                cnpj = pj_data['cnpj']
                logger.info(f"[check_pessoa] Verificando pessoa por CNPJ: {cnpj}")
                query = sql.SQL("SELECT id_pessoa FROM pessoa_pessoa_juridica WHERE cnpj = %s LIMIT 1")
                logger.info(f"[check_pessoa] Query SQL: {query.as_string(cursor)}")
                cursor.execute(query, [cnpj])
                row = cursor.fetchone()
                logger.info(f"[check_pessoa] Resultado da query: {row}")
                if row:
                    logger.info(f"[check_pessoa] Pessoa ENCONTRADA por CNPJ {cnpj}: id_pessoa={row['id_pessoa']}")
                    return row['id_pessoa']
                else:
                    logger.info(f"[check_pessoa] CNPJ {cnpj} não encontrado em pessoa_pessoa_juridica")
        
        # Verifica se há pessoa_fisica com CPF
        if 'pessoa_fisica' in dados_completos:
            pf_data = dados_completos['pessoa_fisica']
            if isinstance(pf_data, dict) and 'cpf' in pf_data:
                cpf = pf_data['cpf']
                logger.info(f"[check_pessoa] Verificando pessoa por CPF: {cpf}")
                query = sql.SQL("SELECT id_pessoa FROM pessoa_fisica WHERE cpf = %s LIMIT 1")
                cursor.execute(query, [cpf])
                row = cursor.fetchone()
                if row:
                    logger.info(f"[check_pessoa] Pessoa ENCONTRADA por CPF {cpf}: id_pessoa={row['id_pessoa']}")
                    return row['id_pessoa']
                else:
                    logger.info(f"[check_pessoa] CPF {cpf} não encontrado em pessoa_fisica")
        
        logger.info(f"[check_pessoa] Pessoa NÃO encontrada por documento")
        return None

    def registro_existe(self, cursor, tabela: str, dados: dict, identificadores:dict, id_postgres=None):
        if id_postgres:
            pk_column = self.get_primary_key(tabela, self.fk_map)
            query = sql.SQL("SELECT {} FROM {} WHERE {} LIMIT 1").format(
                sql.Identifier(pk_column),
                sql.Identifier(tabela),
                sql.SQL("{} = {}").format(sql.Identifier(pk_column), sql.Literal(id_postgres))
            )
            cursor.execute(query)
            row = cursor.fetchone()
            return row[pk_column] if row else None

        # Para tabelas de relacionamento, usar chaves compostas
        if self.is_relationship_table(tabela):
            composite_keys = self.get_composite_keys(tabela)
            if not composite_keys:
                return None

            filtros = []
            valores = []
            for chave in composite_keys:
                valor = dados.get(chave)
                if valor is None:
                    return None
                
                # Normalização de texto: LOWER e TRIM para campos de texto
                if isinstance(valor, str):
                    filtros.append(sql.SQL("LOWER(TRIM({})) = LOWER(TRIM(%s))").format(sql.Identifier(chave)))
                else:
                    filtros.append(sql.SQL("{} = %s").format(sql.Identifier(chave)))
                valores.append(valor)

            # Retorna dict com as chaves compostas se existir
            query = sql.SQL("SELECT {} FROM {} WHERE {} LIMIT 1").format(
                sql.SQL(", ").join([sql.Identifier(k) for k in composite_keys]),
                sql.Identifier(tabela),
                sql.SQL(" AND ").join(filtros),
            )
            cursor.execute(query, valores)
            row = cursor.fetchone()
            if row:
                return {k: row[k] for k in composite_keys}
            return None

        chaves = identificadores.get(tabela, [])
        if not chaves:
            logger.debug(f"[registro_existe] Tabela '{tabela}' não tem identificadores configurados")
            return None

        filtros = []
        valores = []
        for chave in chaves:
            valor = dados.get(chave)
            if valor is None:
                logger.debug(f"[registro_existe] Chave '{chave}' não encontrada nos dados de '{tabela}'")
                return None
            
            if isinstance(valor, str):
                if self._is_date_string(valor):
                    filtros.append(sql.SQL("{} = %s").format(sql.Identifier(chave)))
                else:
                    filtros.append(sql.SQL("LOWER(TRIM({})) = LOWER(TRIM(%s))").format(sql.Identifier(chave)))
            else:
                filtros.append(sql.SQL("{} = %s").format(sql.Identifier(chave)))
            valores.append(valor)

        pk_column = self.get_primary_key(tabela, self.fk_map)
        query = sql.SQL("SELECT {} FROM {} WHERE {} LIMIT 1").format(
            sql.Identifier(pk_column),
            sql.Identifier(tabela),
            sql.SQL(" AND ").join(filtros),
        )

        logger.info(f"[registro_existe] Verificando '{tabela}' com chaves {chaves}: {valores}")
        cursor.execute(query, valores)
        row = cursor.fetchone()
        if row:
            logger.info(f"[registro_existe] Registro ENCONTRADO em '{tabela}': ID={row[pk_column]}")
        else:
            logger.info(f"[registro_existe] Registro NÃO encontrado em '{tabela}'")
        return row[pk_column] if row else None

  
    def define_graph_edges(self, ids, source):
        """Define edges no OrientDB entre tabelas relacionadas via FKs.
        Valida RIDs antes de criar edges para evitar erros de sintaxe."""
        tables = ids.keys()
        pairs = []
        skipped_count = 0
        
        logger.info(f"[OrientDB] Iniciando definição de relacionamentos para {len(ids)} tabelas")
        
        for table_name, table_id in ids.items():
            # Valida se table_id não é vazio/None
            if not table_id or not self._is_valid_rid(table_id):
                continue
                
            for t, fks in self.fk_map.items():
                if t == table_name:
                    for _, (ref_table, ref_pk) in fks.items():
                        if ref_table in tables:
                            ref_id = ids[ref_table]
                            
                            # VALIDAÇÃO CRÍTICA: Só adiciona pares com RIDs válidos
                            if self._is_valid_rid(table_id) and self._is_valid_rid(ref_id):
                                pairs.append([table_id, ref_id])
                            else:
                                skipped_count += 1
                                logger.debug(f"[OrientDB] Relacionamento ignorado (RID inválido): {table_name}({table_id}) -> {ref_table}({ref_id})")
        
        if skipped_count > 0:
            logger.warning(f"[OrientDB] {skipped_count} relacionamentos ignorados por RIDs inválidos")
        
        if not pairs:
            logger.info("[OrientDB] Nenhum relacionamento válido para criar")
            return
        
        logger.info(f"[OrientDB] Criando {len(pairs)} relacionamentos válidos")
        
        try:
            result = self.orient_client.add_relationship_edge(source, batch_pairs=pairs)
            if result:
                logger.info("[OrientDB] Sucesso na definição de relacionamentos")    
        except Exception as e:
            logger.error(f"Erro ao definir os relacionamentos: {e}")            
        

    def completar_registro(self, cursor, tabela: str, existing_id: int, novos_valores: dict):
        """
        Atualiza somente as colunas que estão NULL no registro existente.
        Permite que dados de fontes diferentes complementem informações.
        Retorna dict com informações sobre campos atualizados.
        """
        pk_column = self.get_primary_key(tabela, self.fk_map)

        # Pega os valores atuais
        cursor.execute(
            sql.SQL("SELECT * FROM {} WHERE {} = %s").format(
                sql.Identifier(tabela),
                sql.Identifier(pk_column)
            ),
            (existing_id,)
        )
        registro_atual = cursor.fetchone()
        if not registro_atual:
            logger.warning(f"Nenhum registro encontrado para update na tabela '{tabela}' (id={existing_id}).")
            return None

        colunas_para_update = []
        valores_update = []
        campos_atualizados = {}

        for coluna, novo_valor in novos_valores.items():
            if coluna not in registro_atual:
                continue
            valor_atual = registro_atual[coluna]
            if (valor_atual is None or valor_atual == '') and novo_valor not in (None, ''):
                colunas_para_update.append(sql.SQL("{} = %s").format(sql.Identifier(coluna)))
                valores_update.append(novo_valor)
                campos_atualizados[coluna] = novo_valor

        if not colunas_para_update:
            logger.info(f"Nenhum campo nulo para atualizar em '{tabela}' (id={existing_id}).")
            return None

        query = sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
            sql.Identifier(tabela),
            sql.SQL(", ").join(colunas_para_update),
            sql.Identifier(pk_column)
        )
        valores_update.append(existing_id)

        logger.info(f"[UPDATE] Tabela: {tabela}, ID: {existing_id}, Campos atualizados: {len(colunas_para_update)}")
        cursor.execute(query, valores_update)

        return {
            "id": existing_id,
            **campos_atualizados
        }

    def _is_valid_rid(self, rid) -> bool:
        """Valida se um RID do OrientDB é válido.
        RID válido: não-vazio, não-None, formato #cluster:position ou lista de RIDs válidos."""
        if not rid:
            return False
        
        # Se for lista, valida cada elemento
        if isinstance(rid, list):
            # Lista vazia é inválida
            if not rid:
                return False
            # Todos os elementos devem ser válidos
            return all(self._is_valid_rid(r) for r in rid)
        
        # Se for string, deve começar com # e ter formato #cluster:position
        if isinstance(rid, str):
            rid = rid.strip()
            if not rid or rid == '' or rid == 'None':
                return False
            # Formato básico: #número:número
            if rid.startswith('#') and ':' in rid:
                try:
                    parts = rid[1:].split(':')
                    return len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit()
                except:
                    return False
            return False
        
        return False
    
    def normalize_array_values(self, values: dict) -> dict:
        """
        Normaliza valores que são arrays para seus primeiros elementos.
        Isso é necessário porque alguns processadores retornam arrays de um único elemento.
        """
        normalized = {}
        for key, value in values.items():
            if isinstance(value, list) and len(value) > 0:
                # Extrai o primeiro elemento do array
                normalized[key] = value[0]
            else:
                normalized[key] = value
        return normalized

    def insert_table(
        self, cursor, table, values, pk_column, identificadores, raw_data_id, data_source
    ):
        """Insere se não existir, senão retorna o ID existente e informação de operação"""

        # Normaliza arrays para seus primeiros elementos
        values = self.normalize_array_values(values)

        logger.info(f"\nInserção da tabela: {table} ")
        logger.info("Valores:")
        logger.info(f"{values}")
        new_rid = ''
        is_relationship = self.is_relationship_table(table)
        existing_rid = None
        existing_id = None
        
        # Métricas de tempo
        pg_time = 0.0
        orient_time = 0.0

        # Verifica se deve usar OrientDB (não usar para NFE e classificacao_produto_servico)
        skip_orientdb_sources = ["NFE", "CLASSIFICACAO_PRODUTO_SERVICO"]
        use_orientdb = data_source.upper() not in skip_orientdb_sources if data_source else True
        # use_orientdb = False

        # Detecta se o ID (chave primária) foi fornecido explicitamente
        # IMPORTANTE: Apenas IDs auto-incrementados (id_*) são tratados como referências
        # PKs naturais (cnpj, cpf, etc) sempre vêm nos dados e devem passar pela verificação normal
        id_provided = pk_column in values and values[pk_column] is not None and pk_column.startswith("id_")
        
        if id_provided:
            logger.info(f"[REFERÊNCIA] ID fornecido explicitamente para '{table}': {pk_column}={values[pk_column]}")
            # Verifica se o registro existe usando o ID fornecido
            pg_start = time.time()
            existing_id = self.registro_existe(cursor, table, values, identificadores, id_postgres=values[pk_column])
            pg_time += (time.time() - pg_start)
            
            if existing_id:
                logger.info(f"[OK] Registro encontrado em '{table}' com ID: {existing_id} - usando como referência")
                # Retorna o ID existente sem tentar inserir ou atualizar
                # Operação 'reference' indica que é apenas uma referência
                if use_orientdb and self.orient_client:
                    orient_start = time.time()
                    existing_rid = self.orient_client.send_to_dynamic_database(
                        existing_id,
                        raw_data_id,
                        table,
                        values,
                        data_source)
                    orient_time += (time.time() - orient_start)
                    logger.info(f"Enviado para o Orient (existente) -> id={existing_id}, raw={raw_data_id}, table={table}")
                return existing_id, existing_rid, 'reference', None, pg_time, orient_time
            else:
                logger.warning(f"[AVISO] ID {values[pk_column]} fornecido para '{table}' mas registro não existe no banco")
                # Remove o ID dos valores para permitir inserção normal com auto-increment
                values = values.copy()
                values.pop(pk_column)

        pg_start = time.time()
        if table == "dynamic":
            table = "processo_licitatorio"
            existing_id = self.registro_existe(cursor, table, values, identificadores, id_postgres=values["id_processo_licitatorio"])
        else:
            existing_id = self.registro_existe(cursor, table, values, identificadores)
        pg_time += (time.time() - pg_start)

        if existing_id:
            # Para tabelas de relacionamento, apenas skip (não faz update)
            if is_relationship:
                logger.info(f"[OK] Relacionamento já existe na tabela '{table}': {existing_id}")
                return existing_id, '', 'skip', None, pg_time, orient_time

            if raw_data_id:
                logger.info(f"[OK] Registro já existente na tabela '{table}' com ID: {existing_id}")

                # Completar campos NULL com novos valores
                pg_start = time.time()
                update_info = self.completar_registro(cursor, table, existing_id, values)
                pg_time += (time.time() - pg_start)

                if self.orient_client:
                    orient_start = time.time()
                    existing_rid = self.orient_client.send_to_dynamic_database(
                        existing_id,
                        raw_data_id,
                        table,
                        values,
                        data_source)
                    orient_time += (time.time() - orient_start)
                    logger.info(f"Enviado para o Orient (existente) -> id={existing_id}, raw={raw_data_id}, table={table}")
                return existing_id, existing_rid, 'update', update_info, pg_time, orient_time
            logger.info(f"[OK] Registro já existente na tabela '{table}' com ID: {existing_id}")

            # Completar campos NULL com novos valores
            pg_start = time.time()
            update_info = self.completar_registro(cursor, table, existing_id, values)
            pg_time += (time.time() - pg_start)

            if use_orientdb and self.orient_client:
                orient_start = time.time()
                existing_rid = self.orient_client.send_to_dynamic_database(
                    existing_id,
                    raw_data_id,
                    table,
                    values,
                    data_source)
                orient_time += (time.time() - orient_start)
                logger.info(f"Enviado para o Orient (existente) -> id={existing_id}, raw={raw_data_id}, table={table}")
            return existing_id, existing_rid, 'update', update_info, pg_time, orient_time

        logger.info("\n----> Checagem dos campos")
        logger.info(f"--> Campos passados: {list(values.keys())}")
        pg_start = time.time()
        columns = self.get_postgres_columns(values.keys(), table, cursor)
        pg_time += (time.time() - pg_start)
        
        # Excluir a chave primária auto-incrementada (id_*) do INSERT
        # PKs naturais (cnpj, cpf, etc) devem ser incluídas
        columns_to_insert = [col for col in columns if not (col == pk_column and col.startswith("id_"))]
        
        postgres_columns = ", ".join(columns_to_insert) # Retorna as colunas no postgres
        logger.info(f"--> Campos a serem adicionados no postgres: {postgres_columns}")
        values_postgres = []
        for key, value in values.items():
            if key in columns_to_insert:
                values_postgres.append(value)
        placeholders = ", ".join(["%s"] * len(values_postgres))

        # Tabelas de relacionamento não têm coluna id, não usam RETURNING
        if is_relationship:
            sql_insert = f"INSERT INTO {table} ({postgres_columns}) VALUES ({placeholders})"
            logger.info("\n[POSTGRES] Comando SQL: ")
            logger.info(f"{sql_insert}{list(values_postgres)}")
            pg_start = time.time()
            cursor.execute(sql_insert, values_postgres)
            pg_time += (time.time() - pg_start)
            # Retorna dict com as chaves compostas
            composite_keys = self.get_composite_keys(table)
            new_id = {k: values[k] for k in composite_keys if k in values}
            logger.info(f"[OK] Relacionamento inserido: {new_id}")
            return new_id, '', 'insert', None, pg_time, orient_time

        sql_insert = f"INSERT INTO {table} ({postgres_columns}) VALUES ({placeholders}) RETURNING {pk_column}"
        logger.info("\n[POSTGRES] Comando SQL: ")
        logger.info(f"{sql_insert}{list(values_postgres)}")
        pg_start = time.time()
        cursor.execute(sql_insert, values_postgres)
        new_id = cursor.fetchone()[pk_column]
        pg_time += (time.time() - pg_start)
        
        if use_orientdb and self.orient_client and not is_relationship:
            orient_start = time.time()
            new_rid = self.orient_client.send_to_dynamic_database(
                new_id, raw_data_id, table, values, data_source
            )
            orient_time += (time.time() - orient_start)
            if new_rid:
                logger.info(f"\n[OrientDB] Enviado para o Orient (novo) -> id={new_id}, raw={raw_data_id}, table={table}")
        return new_id, new_rid, 'insert', None, pg_time, orient_time

    def process_nested_children(self, cursor, parent_table, parent_id, nested_children, 
                                fk_map, table_insert_order, identificadores, 
                                raw_data_id, data_source, inserted_ids, inserted_rids, 
                                inserts, updates, depth=0, ancestor_context=None):
                                
        postgres_time = 0.0
        orientdb_time = 0.0
        indent = "  " * depth  # Indentação para logs baseada na profundidade
        
        # Inicializa o contexto de ancestrais se não foi fornecido
        if ancestor_context is None:
            ancestor_context = {}
        
        # Adiciona o pai atual ao contexto de ancestrais
        current_context = ancestor_context.copy()
        current_context[parent_table] = parent_id
        
        for child_table, child_data in nested_children.items():
            logger.info(f"{indent}[NÍVEL {depth}] Processando filho aninhado '{child_table}' de '{parent_table}'")
            
            if not isinstance(child_data, list):
                child_data = [child_data]
            
            # Busca TODAS as FKs que o filho pode ter com tabelas no contexto de ancestrais
            child_fk_map = fk_map.get(child_table, {})
            fks_to_assign = {}
            
            logger.info(f"{indent}  - Contexto atual: {current_context}")
            logger.info(f"{indent}  - FKs de '{child_table}': {child_fk_map}")
            
            # Para cada FK do filho, verifica se a tabela referenciada está no contexto
            for fk_col, (ref_table, ref_pk) in child_fk_map.items():
                if ref_table in current_context:
                    fks_to_assign[fk_col] = current_context[ref_table]
                    logger.info(f"{indent}  - FK '{fk_col}' será atribuída de '{ref_table}': {current_context[ref_table]}")
                #else:
                    #logger.warning(f"{indent}  - FK '{fk_col}' referencia '{ref_table}' que NÃO está no contexto")
            
            # Se não há FKs para atribuir, a tabela pode ser independente (ex: pessoa)
            # Neste caso, insere normalmente sem FKs de ancestrais
            if not fks_to_assign and child_fk_map:
                logger.warning(f"{indent}Aviso: Tabela '{child_table}' tem FKs configuradas mas nenhuma referencia ancestrais no contexto.")
                logger.warning(f"{indent}  - Contexto disponível: {list(current_context.keys())}")
                logger.warning(f"{indent}  - FKs configuradas: {list(child_fk_map.keys())}")
                logger.info(f"{indent}  - Tabela será inserida sem FKs de ancestrais (pode ser tabela independente).")
            
            for child_values in child_data:
                child_values = child_values.copy()
                
                # Atribui TODAS as FKs necessárias dos ancestrais
                for fk_col, fk_value in fks_to_assign.items():
                    child_values[fk_col] = fk_value
                    logger.info(f"{indent}  - Atribuindo FK '{fk_col}'='{fk_value}' para '{child_table}'.")
                
                # VERIFICAÇÃO ESPECIAL PARA PESSOA: Verifica se já existe através do CNPJ/CPF
                # ANTES de remover os filhos aninhados, para ter acesso aos dados completos
                existing_pessoa_id = None
                if child_table == 'pessoa':
                    existing_pessoa_id = self.check_pessoa_exists_by_document(cursor, child_values)
                    
                    if existing_pessoa_id:
                        logger.info(f"{indent}  - Pessoa já existe (ID={existing_pessoa_id}), reutilizando ao invés de inserir")
                        child_id = existing_pessoa_id
                        child_rid = ''
                        child_operation = 'reference'
                        child_update_info = None
                        child_pg_time = 0.0
                        child_orient_time = 0.0
                        
                        # Ainda precisa processar os filhos aninhados (pessoa_pessoa_juridica, cotacao, etc)
                        # mas usando o id_pessoa existente
                        child_nested_children = {}
                        for key, value in list(child_values.items()):
                            if key in table_insert_order and (isinstance(value, dict) or isinstance(value, list)):
                                child_nested_children[key] = child_values.pop(key)
                                logger.info(f"{indent}  - Encontrado neto aninhado '{key}' dentro de '{child_table}', será processado com id_pessoa existente.")
                
                # Se pessoa não existe, continua o fluxo normal
                if child_table != 'pessoa' or existing_pessoa_id is None:
                    # Detecta e remove filhos aninhados do filho atual (recursão)
                    child_nested_children = {}
                    for key, value in list(child_values.items()):
                        if key in table_insert_order and (isinstance(value, dict) or isinstance(value, list)):
                            child_nested_children[key] = child_values.pop(key)
                            logger.info(f"{indent}  - Encontrado neto aninhado '{key}' dentro de '{child_table}', removido para inserção separada.")
                    
                    # VERIFICAÇÃO ESPECIAL PARA pessoa_pessoa_juridica: 
                    # Garante que pessoa_juridica existe antes de inserir o relacionamento
                    if child_table == 'pessoa_pessoa_juridica' and 'cnpj' in child_values:
                        cnpj = child_values['cnpj']
                        logger.info(f"{indent}  - Verificando se pessoa_juridica existe para CNPJ: {cnpj}")
                        
                        # Verifica se pessoa_juridica já existe
                        check_query = sql.SQL("SELECT cnpj FROM pessoa_juridica WHERE cnpj = %s LIMIT 1")
                        cursor.execute(check_query, [cnpj])
                        pj_exists = cursor.fetchone()
                        
                        if not pj_exists:
                            # Precisa do id_pessoa do contexto de ancestrais
                            id_pessoa = current_context.get('pessoa')
                            if id_pessoa:
                                logger.info(f"{indent}  - pessoa_juridica não existe, criando registro com CNPJ: {cnpj} e id_pessoa: {id_pessoa}")
                                insert_pj = sql.SQL("INSERT INTO pessoa_juridica (cnpj, id_pessoa) VALUES (%s, %s)")
                                cursor.execute(insert_pj, [cnpj, id_pessoa])
                                logger.info(f"{indent}  - pessoa_juridica criada com sucesso para CNPJ: {cnpj}")
                            # else:
                            #     logger.warning(f"{indent}  - pessoa_juridica não pode ser criada: id_pessoa não está no contexto")
                        else:
                            logger.info(f"{indent}  - pessoa_juridica já existe para CNPJ: {cnpj}")
                    
                    # Insere o filho
                    child_pk = self.get_primary_key(child_table, fk_map)
                    child_id, child_rid, child_operation, child_update_info, child_pg_time, child_orient_time = self.insert_table(
                        cursor, child_table, child_values, child_pk,
                        identificadores, raw_data_id, data_source
                    )
                
                postgres_time += child_pg_time
                orientdb_time += child_orient_time
                
                # Atualiza registros de IDs inseridos
                inserted_ids[child_table].append(child_id)
                inserted_rids[child_table].append(child_rid)
                
                # Rastrear operação filho
                if child_operation == 'insert':
                    inserts[child_table] = child_id
                elif child_operation == 'update' and child_update_info:
                    updates[child_table] = child_update_info
                
                logger.info(f"{indent}  - ID Filho inserido: {child_id} ({child_table})")
                
                # RECURSÃO: Processa os filhos do filho (netos)
                # Passa o contexto atualizado com o filho atual
                if child_nested_children:
                    logger.info(f"{indent}  - Processando {len(child_nested_children)} neto(s) de '{child_table}'")
                    nested_pg_time, nested_orient_time = self.process_nested_children(
                        cursor, child_table, child_id, child_nested_children,
                        fk_map, table_insert_order, identificadores,
                        raw_data_id, data_source, inserted_ids, inserted_rids,
                        inserts, updates, depth + 1, current_context
                    )
                    postgres_time += nested_pg_time
                    orientdb_time += nested_orient_time
        
        # APÓS processar todos os filhos, verifica se algum deles é FK de algum ancestral
        # e atualiza os ancestrais com os IDs gerados (propaga netos para avôs)
        for ancestor_table, ancestor_id in ancestor_context.items():
            ancestor_fk_map = fk_map.get(ancestor_table, {})
            fks_to_update = {}
            
            # Para cada FK do ancestral, verifica se algum filho processado corresponde
            for fk_col, (ref_table, ref_pk) in ancestor_fk_map.items():
                # Se o filho aninhado foi processado e é uma FK do ancestral
                if ref_table in nested_children and ref_table in inserted_ids and inserted_ids[ref_table]:
                    # Pega o último ID inserido desse filho
                    child_id = inserted_ids[ref_table][-1]
                    fks_to_update[fk_col] = child_id
                    logger.info(f"{indent}  - FK '{fk_col}' do ancestral '{ancestor_table}' será atualizada com ID de '{ref_table}': {child_id}")
            
            # Se há FKs para atualizar no ancestral, faz UPDATE
            if fks_to_update:
                update_parts = []
                update_values = []
                for fk_col, fk_value in fks_to_update.items():
                    update_parts.append(sql.SQL("{} = %s").format(sql.Identifier(fk_col)))
                    update_values.append(fk_value)
                
                ancestor_pk = self.get_primary_key(ancestor_table, fk_map)
                update_values.append(ancestor_id)  # WHERE id = ancestor_id
                
                update_query = sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                    sql.Identifier(ancestor_table),
                    sql.SQL(", ").join(update_parts),
                    sql.Identifier(ancestor_pk)
                )
                
                logger.info(f"{indent}[PROPAGAÇÃO] Atualizando ancestral '{ancestor_table}' (ID={ancestor_id}) com FKs de netos: {fks_to_update}")
                cursor.execute(update_query, update_values)
                logger.info(f"{indent}[PROPAGAÇÃO] Ancestral '{ancestor_table}' atualizado com sucesso")
        
        return postgres_time, orientdb_time

    def auto_create_relationships(self, cursor, inserted_ids, data, identificadores, raw_data_id, data_source, inserts):
        """
        Cria automaticamente entradas em tabelas de relacionamento quando ambas as tabelas pai foram inseridas.
        Exemplo: Se execucao_metodo e objeto_analise foram inseridos, cria execucao_metodo_objeto_analise.
        """
        pg_time = 0.0
        orient_time = 0.0
        for rel_table, config in self.relationship_tables.items():
            if not config.get("auto_create", False):
                continue

            # Se a tabela de relacionamento já foi fornecida nos dados, pula
            if rel_table in data:
                logger.info(f"[AUTO-CREATE] Tabela '{rel_table}' já fornecida nos dados, pulando auto-create.")
                continue

            parent_tables = config.get("parent_tables", [])
            if not parent_tables:
                continue

            # Verifica se todas as tabelas pai foram inseridas
            all_parents_present = all(
                parent in inserted_ids and inserted_ids[parent]
                for parent in parent_tables
            )

            if not all_parents_present:
                continue

            # Monta os valores para a tabela de relacionamento usando fk_map
            rel_values = {}
            fk_mapping = self.fk_map.get(rel_table, {})

            for fk_col, (ref_table, ref_pk) in fk_mapping.items():
                if ref_table in parent_tables and ref_table in inserted_ids:
                    # Pega o último ID inserido para essa tabela
                    parent_ids = inserted_ids[ref_table]
                    if isinstance(parent_ids, list) and parent_ids:
                        rel_values[fk_col] = parent_ids[-1]
                    elif parent_ids:
                        rel_values[fk_col] = parent_ids

            # Verifica se temos todos os valores necessários
            composite_keys = config.get("composite_keys", [])
            if not all(k in rel_values for k in composite_keys):
                logger.warning(f"[AUTO-CREATE] Não foi possível obter todos os valores para '{rel_table}': {rel_values}")
                continue

            logger.info(f"[AUTO-CREATE] Criando relacionamento em '{rel_table}': {rel_values}")

            pk_column = self.get_primary_key(rel_table, self.fk_map)
            new_id, new_rid, operation, update_info, rel_pg_time, rel_orient_time = self.insert_table(
                cursor, rel_table, rel_values, pk_column,
                identificadores, raw_data_id, data_source
            )
            pg_time += rel_pg_time
            orient_time += rel_orient_time

            if rel_table not in inserted_ids:
                inserted_ids[rel_table] = []
            if isinstance(inserted_ids[rel_table], list):
                inserted_ids[rel_table].append(new_id)
            else:
                inserted_ids[rel_table] = [inserted_ids[rel_table], new_id]

            if operation == 'insert':
                inserts[rel_table] = new_id
                logger.info(f"[AUTO-CREATE] Relacionamento criado com sucesso: {new_id}")
            elif operation == 'skip':
                logger.info(f"[AUTO-CREATE] Relacionamento já existia: {new_id}")
        
        return pg_time, orient_time

    def insert_data(self, data, fk_map, table_insert_order, identificadores):
        inserted_rids = {t: [] for t in table_insert_order}
        inserted_ids = {t: [] for t in table_insert_order}
        inserts = {}  # Rastreia inserções: {tabela: id}
        updates = {}  # Rastreia atualizações: {tabela: {id: ..., campos...}}
        
        # Métricas de tempo
        postgres_time = 0.0
        orientdb_time = 0.0
        
        # Reseta métricas de conexão do OrientDB no início
        if self.orient_client:
            self.orient_client.reset_connection_metrics()

        raw_data_id = None
        data_source = None

        if 'alerta' not in data:
            raw_data_id = data.get("raw_data_id")
            data_source = data.get("data_source")

        if not self.db_manager.is_connected():
            logger.warning("Conexão com banco perdida. Tentando reconectar...")
            try:
                self.db_manager.close_connection() 
                self.db_manager = RelationalStorageManagerFactory.get_relational_storage_manager()
            except Exception as e:
                logger.error(f"Falha ao tentar reconectar: {e}")

        if not self.db_manager.is_connected():
            logger.error("Não foi possível conectar ao banco de dados. Abortando processamento desta mensagem.")
            raise ConnectionError("Falha crítica de conexão com o Banco de Dados")


        try:
            with self.db_manager.get_cursor(cursor_factory=RealDictCursor) as cursor:
                for table in table_insert_order:
                    if table not in data:
                        continue

                    table_data = data[table]

                    if not isinstance(table_data, list):
                        table_data = [table_data]

                    for values in table_data:
                        values = values.copy()

                        if all(v is None for v in values.values()):
                            continue

                        nested_children = {}

                        for key, value in list(values.items()):
                            if key in table_insert_order and (isinstance(value, dict) or isinstance(value, list)):
                                nested_children[key] = values.pop(key)
                                logger.info(f"    - Encontrado filho aninhado '{key}', removido para inserção separada.")


                        for fk_col, (ref_table, ref_pk) in fk_map.get(table, {}).items():
                            if ref_table in inserted_ids and inserted_ids[ref_table]:
                                values[fk_col] = inserted_ids[ref_table][-1]
                                logger.info(f"    - FK sequencial '{fk_col}' atribuída de '{ref_table}': {values[fk_col]}")

                        pk_column = self.get_primary_key(table, fk_map)
                        
                        # Medir tempo de inserção (PostgreSQL + OrientDB)
                        start_time = time.time()
                        new_id, new_rid, operation, update_info, pg_time, orient_time = self.insert_table(
                            cursor, table, values, pk_column,
                            identificadores, raw_data_id, data_source
                        )
                        postgres_time += pg_time
                        orientdb_time += orient_time
                        
                        inserted_ids[table].append(new_id)
                        inserted_rids[table].append(new_rid)

                        # Rastrear operação
                        if operation == 'insert':
                            inserts[table] = new_id
                        elif operation == 'update' and update_info:
                            updates[table] = update_info
                        # 'reference' e 'skip' não são rastreados no output

                        logger.info(f"    - ID Pai inserido: {new_id} ({table})")

                        # Processa filhos aninhados recursivamente (suporta múltiplos níveis)
                        if nested_children:
                            logger.info(f"    - Processando {len(nested_children)} filho(s) aninhado(s) de '{table}'")
                            # Inicializa o contexto de ancestrais vazio para o primeiro nível
                            nested_pg_time, nested_orient_time = self.process_nested_children(
                                cursor, table, new_id, nested_children,
                                fk_map, table_insert_order, identificadores,
                                raw_data_id, data_source, inserted_ids, inserted_rids,
                                inserts, updates, depth=1, ancestor_context={}
                            )
                            postgres_time += nested_pg_time
                            orientdb_time += nested_orient_time
                            
                            # Após processar filhos aninhados, verifica se algum deles é FK do pai
                            # e atualiza o registro pai com os IDs gerados
                            fks_to_update = {}
                            parent_fk_map = fk_map.get(table, {})
                            
                            for fk_col, (ref_table, ref_pk) in parent_fk_map.items():
                                # Se o filho aninhado foi processado e é uma FK do pai
                                if ref_table in nested_children and ref_table in inserted_ids and inserted_ids[ref_table]:
                                    # Pega o último ID inserido desse filho
                                    child_id = inserted_ids[ref_table][-1]
                                    fks_to_update[fk_col] = child_id
                                    logger.info(f"    - FK '{fk_col}' do pai '{table}' será atualizada com ID de '{ref_table}': {child_id}")
                            
                            # Se há FKs para atualizar, faz UPDATE no registro pai
                            if fks_to_update:
                                update_parts = []
                                update_values = []
                                for fk_col, fk_value in fks_to_update.items():
                                    update_parts.append(sql.SQL("{} = %s").format(sql.Identifier(fk_col)))
                                    update_values.append(fk_value)
                                
                                update_values.append(new_id)  # WHERE id = new_id
                                
                                update_query = sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
                                    sql.Identifier(table),
                                    sql.SQL(", ").join(update_parts),
                                    sql.Identifier(pk_column)
                                )
                                
                                logger.info(f"    - Atualizando '{table}' (ID={new_id}) com FKs de filhos aninhados: {fks_to_update}")
                                cursor.execute(update_query, update_values)
                                logger.info(f"    - '{table}' atualizado com sucesso")

                        if table == 'processo_licitatorio':
                            if 'dynamic' in data.keys():
                                table_data = data['dynamic']
                                table_data['id_processo_licitatorio'] = new_id
                                _, _, _, _, dyn_pg_time, dyn_orient_time = self.insert_table(
                                cursor, 'dynamic', table_data, pk_column,
                                identificadores, raw_data_id, data_source
                                )
                                postgres_time += dyn_pg_time
                                orientdb_time += dyn_orient_time

                # Auto-criar relacionamentos quando tabelas pai foram inseridas
                auto_rel_pg_time, auto_rel_orient_time = self.auto_create_relationships(
                    cursor, inserted_ids, data, identificadores,
                    raw_data_id, data_source, inserts
                )
                postgres_time += auto_rel_pg_time
                orientdb_time += auto_rel_orient_time

                # Medir tempo de commit
                commit_start = time.time()
                self.db_manager.commit()
                postgres_time += (time.time() - commit_start)
                
        except Exception as e:
            logger.error(f"Erro durante inserção de dados: {e}")
            
            # Tenta fazer rollback apenas se a conexão ainda estiver ativa
            try:
                self.db_manager.rollback()
            except Exception as rollback_error:
                logger.warning(f"Não foi possível fazer rollback: {rollback_error}")
            
            # Se a conexão caiu, tenta reconectar para próximas mensagens
            if not self.db_manager.is_connected():
                logger.warning("Conexão com PostgreSQL perdida. Tentando reconectar...")
                try:
                    self.db_manager.connect()
                    logger.info("Reconexão com PostgreSQL bem-sucedida")
                except Exception as reconnect_error:
                    logger.error(f"Falha ao reconectar com PostgreSQL: {reconnect_error}")
            
            raise

        # Retorna dados do PostgreSQL e inserted_rids separadamente (para uso interno do OrientDB)
        return {
            "data": {
                "insert": inserts,
                "update": updates
            },
            "inserted_ids": {
                t: ids[0] if len(ids) == 1 else ids
                for t, ids in inserted_ids.items()
                if ids and any(i is not None for i in ids)
            },
            "_internal_rids": {
                t: rids[0] if len(rids) == 1 else rids
                for t, rids in inserted_rids.items()
                if rids and any(r is not None for r in rids)
            },
            "_timing": {
                "postgres_time_seconds": round(postgres_time, 3),
                "orientdb_time_seconds": round(orientdb_time, 3),
                "total_time_seconds": round(postgres_time + orientdb_time, 3)
            }
        }

    def publish_to_log_queue(self, log_data: dict):
        """
        Publica logs de mensagens processadas em uma fila dedicada para auditoria.
        
        Args:
            log_data: Dicionário contendo informações do processamento
        """
        try:
            channel = self.queue_manager.channel
            log_queue_name = 'inserter_updater_logs'
            
            # Declara a fila de logs (durável para persistência)
            channel.queue_declare(queue=log_queue_name, durable=True)
            
            # Publica na fila de logs
            channel.basic_publish(
                exchange='',
                routing_key=log_queue_name,
                body=json.dumps(log_data, ensure_ascii=False, indent=2),
                properties=self.queue_manager.get_persistent_properties()
            )
            
            # Log formatado no console (JSON estruturado)
            status = log_data.get('status', 'unknown')
            log_type = "SUCCESS" if status == 'success' else "ERROR"
            
            # Formata o JSON com indentação
            log_json = json.dumps(log_data, ensure_ascii=False, indent=2)
            
            # Adiciona cabeçalho visual
            separator = "=" * 80
            header = f"[LOG QUEUE] Mensagem processada - {log_type}"
            
            log_output = f"\n{separator}\n{header}\n{separator}\n{log_json}\n{separator}"
            
            if status == 'success':
                logger.info(log_output)
            else:
                logger.error(log_output)
                
        except Exception as e:
            logger.error(f"[LOG QUEUE] Erro ao publicar log: {e}")

    ##def topic_exchange(self, operation: str, table_name: str, body: dict):
    ##    """
    ##    Publica mensagem no tópico db_events para notificar outros serviços.
    ##    Usado pelo cross-reference-noticias para vincular notícias a processos licitatórios.
    ##    """
    ##    routing_key = f"{operation}.{table_name}"
    ##    logger.info(f"Publicando mensagem no tópico db_events com routing_key: {routing_key}")
    ##    
    ##    # Publica diretamente no tópico usando o queue_manager
    ##    try:
    ##        self.queue_manager.publish_to_exchange(
    ##            exchange_name=self.output_topic,
    ##            routing_key=routing_key,
    ##            message=body
    ##        )
    ##        logger.info(f"Mensagem publicada com sucesso no tópico '{self.output_topic}' com routing_key '{routing_key}'")
    ##    except Exception as e:
    ##        logger.error(f"Erro ao publicar no tópico db_events: {e}")
    ##        raise

    def process_message(self, message):

        message_original = json.loads(json.dumps(message))
        message_convertida = self.converter_datas(message)

        data_source = message_convertida.get("data_source") or ""
        data_source = data_source.lower() if data_source else "unknown"

        # Inicializa corpo_notificacao com estrutura padrão
        corpo_notificacao = {
            "routing_key": "error.unknown",
            "ids_gerados_db": {}
        }

        try:
            # Só inicializa OrientDB se não for NFE
            # if data_source != "nfe" and data_source != "classificacao_produto_servico" and data_source != "unknown" and not self.orient_client:
            #     self.orient_client = CeosOrientDBClient(
            #         host=os.getenv("HOST_ORIENT"),
            #         port=os.getenv("PORT_ORIENT"),
            #         username=os.getenv("USERNAME_ORIENT"),
            #         password=os.getenv("SENHA_ORIENT"),
            #         graph_name=os.getenv("DATABASE_ORIENT")
            #     )
            ids_gerados = self.insert_data(
                message_convertida, self.fk_map, self.table_insert_order, self.table_identifiers
            )

            # Extrai _internal_rids e timing para uso do OrientDB antes de remover
            internal_rids = ids_gerados.pop('_internal_rids', {})
            timing_info = ids_gerados.pop('_timing', {})

            if ids_gerados:
                tabela_principal = None
                for tabela in self.table_insert_order:
                    if tabela in message_original:
                        tabela_principal = tabela
                        break

                if tabela_principal:
                    operation = "insert"
                    routing_key = f"{operation}.{data_source}"

                    corpo_notificacao["routing_key"] = routing_key
                    corpo_notificacao["ids_gerados_db"] = ids_gerados
                    
                    # Publica no tópico db_events para notificar serviços downstream
                    #self.topic_exchange(operation, data_source, corpo_notificacao)

            # Só define edges no OrientDB se não for NFE
            if data_source != "nfe" and data_source != "classificacao_produto_servico" and data_source != "unknown" and self.orient_client:
                orient_edge_start = time.time()
                self.define_graph_edges(internal_rids, data_source)
                orient_edge_time = time.time() - orient_edge_start
                # Adiciona tempo de criação de edges ao timing do OrientDB
                if timing_info:
                    timing_info['orientdb_time_seconds'] = round(timing_info.get('orientdb_time_seconds', 0) + orient_edge_time, 3)
                    timing_info['total_time_seconds'] = round(timing_info.get('total_time_seconds', 0) + orient_edge_time, 3)

            # Publica log da mensagem processada na fila de logs (sucesso)
            inserted_ids = corpo_notificacao.get("ids_gerados_db", {}).get("inserted_ids", {})
            data_info = corpo_notificacao.get("ids_gerados_db", {}).get("data", {})
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "data_source": data_source,
                "routing_key": corpo_notificacao.get("routing_key"),
                "raw_data_id": message_convertida.get("raw_data_id"),
                
                # Informações de processamento
                "processing": {
                    "tables_processed": list(inserted_ids.keys()),
                    "total_tables": len(inserted_ids),
                    "inserts_count": len(data_info.get("insert", {})),
                    "updates_count": len(data_info.get("update", {})),
                },
                
                # IDs gerados
                "ids_generated": inserted_ids,
                
                # Detalhes de operações
                "operations": {
                    "inserts": data_info.get("insert", {}),
                    "updates": data_info.get("update", {})
                },
                
                # Métricas de performance
                "performance": {
                    "postgres_seconds": timing_info.get("postgres_time_seconds", 0),
                    "orientdb_seconds": timing_info.get("orientdb_time_seconds", 0),
                    "total_seconds": timing_info.get("total_time_seconds", 0),
                    "postgres_percentage": round((timing_info.get("postgres_time_seconds", 0) / timing_info.get("total_time_seconds", 1)) * 100, 1) if timing_info.get("total_time_seconds", 0) > 0 else 0,
                    "orientdb_percentage": round((timing_info.get("orientdb_time_seconds", 0) / timing_info.get("total_time_seconds", 1)) * 100, 1) if timing_info.get("total_time_seconds", 0) > 0 else 0,
                    "orientdb_connection_metrics": self.orient_client.get_connection_metrics() if self.orient_client else None,
                },
                
                # Dados originais (para referência)
                "message_info": {
                    "entity_type": message_convertida.get("entity_type"),
                    "collect_id": message_convertida.get("collect_id"),
                    "raw_data_collection": message_convertida.get("raw_data_collection"),
                }
            }
            self.publish_to_log_queue(log_entry)

        except Exception as e:
            import traceback
            
            # Extrai detalhes completos do erro (especialmente para erros do PostgreSQL)
            error_details = self.extract_postgres_error_details(e)
            error_details["traceback"] = traceback.format_exc()
            
            # Publica log de erro na fila de logs
            error_log_entry = {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "data_source": data_source,
                "routing_key": corpo_notificacao.get("routing_key"),
                "raw_data_id": message_convertida.get("raw_data_id"),
                
                # Informações do erro (com detalhes completos do PostgreSQL se aplicável)
                "error": error_details,
                
                # Dados da mensagem (para debug)
                "message_info": {
                    "entity_type": message_convertida.get("entity_type"),
                    "collect_id": message_convertida.get("collect_id"),
                    "raw_data_collection": message_convertida.get("raw_data_collection"),
                    "tables_in_message": list(message_convertida.keys())
                }
            }
            self.publish_to_log_queue(error_log_entry)
            # Re-lança a exceção para manter o comportamento original
            raise

        # Retorna apenas dados do PostgreSQL (insert/update)
        return corpo_notificacao

if __name__ == "__main__":
    # Configura o logger para exibir no console ao rodar o script diretamente
    logger = Logger(log_to_console=True)
    
    processor = InserterUpdater()
    try:
        if processor.db_manager.is_connected():
            logger.info("Iniciando o serviço InserterUpdater...")
            processor.start()
        else:
            logger.critical("Não foi possível iniciar o serviço devido a falhas de conexão na inicialização.")
    except KeyboardInterrupt:
        logger.info("Serviço interrompido pelo usuário.")
    finally:
        processor.shutdown()
import os
import traceback
import datetime
import json # Import json para usar json.dumps
from sqlalchemy import create_engine, text
from service_essentials.utils.logger import Logger
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService


class NfeClassifier(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        logger.info(f"Iniciando Classificador NFE (modo item)") 

        logger.info(f"Configurando conexão com o banco de dados Novo CEOS")
        self.db_engine_novo_ceos = self._setup_database_connection("novo_ceos")

        if not self.db_engine_novo_ceos:
            logger.error("Falha ao inicializar conexão do banco")

    def process_message(self, record):

        logger.info(f"Mensagem recebida: {record}")
        ids = record.get("ids_gerados_db")
        if not ids:
            logger.warning(f"Mensagem recebida sem 'ids_gerados_db': {record}")
            return None # ACK e descarta

        inserted_ids = ids.get("inserted_ids", {})
        if isinstance(inserted_ids, dict) and "item_nfe" in inserted_ids:
            ids_itens_raw = inserted_ids.get("item_nfe")
        else:
            ids_itens_raw = ids.get("item_nfe", [])

        if ids_itens_raw is None:
             ids_itens_raw = []

        if not isinstance(ids_itens_raw, list):
             ids_itens = [ids_itens_raw] 
        else:
             ids_itens = ids_itens_raw

        for item_id in ids_itens:

            item_query_result = self.query_nfe_item(item_id)
            if not item_query_result:
                 logger.warning(f"Item {item_id} não encontrado no banco. Pulando.")
                 continue 

            item_formatted_payload = self._formatar_single_item(item_query_result)
            if not item_formatted_payload:
                 logger.error(f"Falha ao formatar dados básicos do item {item_id}. Pulando.")
                 continue
                 
            item_dict = item_formatted_payload.get("item_nfe", {})
            if not item_dict: 
                logger.error(f"Dicionário 'item_nfe' vazio após formatação para {item_id}. Pulando.")
                continue

            # Verifica anti-loop 
            if item_dict.get("id_grupo_bp") is not None:
                grupo_existente = item_dict.get("id_grupo_bp")
                logger.warning(f"Item {item_id} já processado (id_grupo_bp={grupo_existente}). Pulando item.")
                continue 

            # Classifica o item
            ncm = item_dict.get("ncm_produto")
            classificacao = "Outro" # Padrão
            if ncm and isinstance(ncm, str) and len(ncm) >= 4:
                try:
                    prefixo = int(ncm[:4])
                    if prefixo == 3004:
                        classificacao = "Medicamento"
                except ValueError:
                    pass 

            logger.info(f"Item {item_id} classificado como '{classificacao}'.")

            mensagem_final_dict = self._formatar_mensagem_saida(item_dict, classificacao, item_id)
            
            if not mensagem_final_dict:
                logger.error(f"Falha ao criar mensagem final para item {item_id}. Pulando.")
                continue

            try:
                mensagem_final_str = json.dumps(mensagem_final_dict, ensure_ascii=False)
                self.queue_manager.publish_message(self.output_queue, mensagem_final_str)
                logger.info(f"Mensagem para item {item_id} publicada na fila '{self.output_queue}'.")
            except Exception as e:
                logger.error(f"Erro ao publicar mensagem para item {item_id}: {e}")

        # Retorna None para indicar à classe base que já publicamos
        return None 
    
    def _setup_database_connection(self, db_name: str):
        # (Função igual, usando logger global)
        try:
            db_user = os.getenv('USERNAME_PG')
            db_password = os.getenv('SENHA_PG')
            db_host = os.getenv('HOST_PG')
            db_port = os.getenv('PORT_PG')

            if not all([db_user, db_password, db_host, db_port, db_name]):
                logger.error(f"Uma ou mais variáveis de ambiente para a conexão com o banco '{db_name}' não estão definidas.")
                return None

            logger.info(f"Estabelecendo conexão com o banco: {db_name}...")
            db_connection_str = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
            engine = create_engine(db_connection_str, pool_size=5, max_overflow=10)
            with engine.connect() as connection:
                 connection.execute(text("SELECT 1"))
            logger.info(f"Conexão com o banco '{db_name}' estabelecida com sucesso!")
            return engine
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Erro durante a conexão com o banco '{db_name}': {e}\nTRACEBACK:\n{tb_str}")
            return None

    def query_nfe_item(self, id_item_nfe):
        if not self.db_engine_novo_ceos:
            logger.error("Conexão com o banco não está disponível.")
            return None
        if id_item_nfe is None:
            logger.error("id_item_nfe não fornecido para query_nfe_item.")
            return None

        query_sql = text("SELECT * FROM public.item_nfe WHERE id_item_nfe = :item_param LIMIT 1;") 

        try: 
            with self.db_engine_novo_ceos.connect() as connection:
                result_proxy = connection.execute(query_sql, {"item_param": id_item_nfe})
                result = result_proxy.fetchone()
                if result:
                    return result 
                else:
                    logger.warning(f"Nenhum item encontrado para id_item_nfe: {id_item_nfe}")
                    return None
        except Exception as e:
            logger.error(f"Erro ao consultar item {id_item_nfe}: {e}")
            return None 

    def _formatar_single_item(self, item_row):
        if not item_row: 
            return None
        item_data = item_row._asdict()  
        
        for key, value in item_data.items():
            if isinstance(value, datetime.datetime):
                item_data[key] = value.date().isoformat()
            elif isinstance(value, datetime.date):
                item_data[key] = value.isoformat()
        
        return {"item_nfe": item_data}

    def _formatar_mensagem_saida(self, item_dict, classificacao, item_id): 
        """
        Cria a estrutura final para o Inserter.
        Estratégia: Envia a Classificação (Top Level) e a Tabela de Ligação (Top Level),
        evitando o erro de aninhamento incorreto.
        """
        if not item_dict:
            return None

        # 1. Objeto da Classificação (Será inserido/consultado primeiro)
        classificacao_obj = { 
            "id_classificacao_produto_servico_pai" : None, 
            "descricao" : classificacao,
            "identificador_para_codigo": classificacao
        }

        # 2. Objeto da Tabela de Ligação (item_nfe_classificacao_produto_servico)
        # O Inserter resolverá o 'id_classificacao_produto_servico' automaticamente
        # porque 'classificacao_produto_servico' será processado antes no insert_order.
        # O 'id_item_nfe' nós passamos explicitamente pois o item já existe.
        bridge_obj = {
            "id_item_nfe": item_id
            # id_classificacao_produto_servico será preenchido pelo Inserter (fk resolution)
        }

        # Montamos o payload plano (Top Level)
        # IMPORTANTE: A ordem de processamento no Inserter deve ser:
        # 1. classificacao_produto_servico
        # 2. item_nfe_classificacao_produto_servico
        payload = {
            "data_source": "classificacao_produto_servico",
            "classificacao_produto_servico": [classificacao_obj],
            "item_nfe_classificacao_produto_servico": [bridge_obj]
        }
            
        return payload

if __name__ == '__main__':
    logger = Logger(log_to_console=True) 

    classifier = NfeClassifier()
    classifier.start() 

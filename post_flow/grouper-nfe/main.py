import os
import json
import time
import importlib
import traceback
import datetime
from sqlalchemy import create_engine, text
from service_essentials.utils.logger import Logger
from groupers.base_grouper import BaseGrouper
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService

logger = Logger()

class NfeGrouper(BasicProducerConsumerService):

    def __init__(self):
        super().__init__()
        logger.info("Iniciando Agrupador NFe Service...")

        logger.info(f"Configurando conexão com o banco de dados Novo CEOS")
        self.db_engine_novo_ceos = self._setup_database_connection("novo_ceos")
        if not self.db_engine_novo_ceos:
            logger.error("Falha ao inicializar conexão do banco. Serviço pode não funcionar.")

        logger.info("Carregando módulos de groupers...")
        self.groupers = self.load_groupers()
        logger.info(f"Groupers carregados: {list(self.groupers.keys())}")


    def process_message(self, record):
        logger.info(f"\nMensagem recebida! {record}")

        ids_gerados = record.get("ids_gerados_db", {})
        inserted_ids = ids_gerados.get("inserted_ids", {})
        
        # --- LÓGICA DE RECUPERAÇÃO DO ID DO ITEM ---
        id_item_nfe = None

        # 1. Tenta pegar ID direto (caso venha de um insert de item_nfe)
        if isinstance(inserted_ids, dict) and "item_nfe" in inserted_ids:
            id_item_nfe = inserted_ids.get("item_nfe")
        elif "item_nfe" in ids_gerados:
            id_item_nfe = ids_gerados.get("item_nfe")

        # 2. Se não achou, tenta resolver via tabela de ligação (caso venha do classifier)
        if not id_item_nfe:
            bridge_id = None
            if isinstance(inserted_ids, dict) and "item_nfe_classificacao_produto_servico" in inserted_ids:
                bridge_id = inserted_ids.get("item_nfe_classificacao_produto_servico")
            
            if bridge_id:
                id_item_nfe = self._resolve_item_id_from_bridge(bridge_id)
                if id_item_nfe:
                    logger.info(f"ID do Item {id_item_nfe} recuperado via tabela de ligação (ID {bridge_id}).")

        # Normalização: Se vier como lista, pega o primeiro elemento
        if isinstance(id_item_nfe, list):
            if len(id_item_nfe) > 0:
                id_item_nfe = id_item_nfe[0]
            else:
                id_item_nfe = None
        # -------------------------------------------

        # Preservar dados de rastreamento se existirem
        raw_data_id = record.get("raw_data_id")

        if id_item_nfe is None:
            logger.warning(f"Mensagem recebida sem ID de item válido ou recuperável: {record}")
            return None # Descarta mensagem

        item_row = self._query_item_and_classification(id_item_nfe)

        if not item_row:
            logger.warning(f"Item {id_item_nfe} não encontrado ou sem classificação no banco.")
            return None # Descarta mensagem

        item_dict, classificacao = self._format_item_data(item_row)
        if not item_dict: 
             logger.error(f"Falha ao formatar dados do item {id_item_nfe}.")
             return None

        grupo_final = None
        
        # --- Lógica Principal ---
        if classificacao == "Medicamento":
            logger.info(f"Item ID {id_item_nfe} classificado como 'Medicamento'.")
            
            # 1. PARALELISMO: Envia para o NOVO microserviço
            # try:
            #     msg = json.dumps(item_dict, default=str)
            #     self.queue_manager.publish_message("grouper-medicamentos", msg)
            #     logger.info(f"Item enviado para fila 'grouper-medicamentos' para processamento paralelo.")
            # except Exception as e:
            #     logger.error(f"Erro ao publicar no grouper-medicamentos: {e}")

            # 2. PROCESSAMENTO LOCAL (Código Antigo)
            grouper = self.groupers.get("medicamentos")

            if not grouper:
                logger.error("Grouper 'medicamentos' local não carregado!")
            else:
                try:
                    resultado_grouper = grouper.group(item_dict) 
                    if resultado_grouper is not None:
                        grupo_final = resultado_grouper
                        logger.info(f"Item ID {id_item_nfe} agrupado localmente: {grupo_final}")
                    else:
                        logger.info(f"Grouper 'medicamentos' local não encontrou grupo específico para Item ID {id_item_nfe}.")
                except Exception as e:
                    logger.error(f"Erro ao agrupar item de medicamento ID {id_item_nfe} localmente: {e}")
            
            # O código CONTINUA aqui para formatar e enviar o resultado local para o Inserter
        else:
            logger.info(f"Item ID {id_item_nfe} classificado como '{classificacao}' não possui serviço de agrupamento")
            return

        # 3. Formata e envia a mensagem com o resultado local para o fluxo padrão (Inserter)
        mensagem_final_dict = self._format_output_message(item_dict, grupo_final, raw_data_id)

        if not mensagem_final_dict:
             logger.error(f"Falha ao formatar mensagem de saída para item {id_item_nfe}.")
             return None 

        try:
            mensagem_final_str = json.dumps(mensagem_final_dict, ensure_ascii=False, default=str)
            self.publish_output(mensagem_final_str)
            logger.info(f"Mensagem agrupada (Local) para item {id_item_nfe} publicada para o Inserter.")
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem para item {id_item_nfe}: {e}")
            return None

        logger.info("Processamento de agrupamento finalizado para o item.")
        return None

    def _setup_database_connection(self, db_name: str):
        """Cria e testa uma conexão com um banco de dados específico (SQLAlchemy engine)."""
        try:
            db_user = os.getenv('USERNAME_PG')
            db_password = os.getenv('SENHA_PG')
            db_host = os.getenv('HOST_PG')
            db_port = os.getenv('PORT_PG')

            if not all([db_user, db_password, db_host, db_port, db_name]):
                logger.error(f"Variáveis de ambiente do banco '{db_name}' não definidas.")
                return None

            logger.info(f"Estabelecendo conexão com o banco: {db_name}...")
            db_connection_str = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
            
            # --- MUDANÇA PRINCIPAL AQUI ---
            engine = create_engine(
                db_connection_str, 
                pool_size=5, 
                max_overflow=10,
                
                # 1. Verifica se a conexão está viva antes de rodar a query.
                # Se caiu, ele abre uma nova transparentemente.
                pool_pre_ping=True,  
                
                # 2. Fecha e recria conexões a cada 5 minutos (300s)
                # para evitar que fiquem velhas e sejam cortadas por firewall.
                pool_recycle=300,    
                
                # 3. Configurações de TCP Keepalive (nível de rede)
                # Envia pacotes vazios a cada 30s para manter o canal aberto.
                connect_args={
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 5
                }
            )
            # ------------------------------

            with engine.connect() as connection:
                 connection.execute(text("SELECT 1"))
            logger.info(f"Conexão com o banco '{db_name}' estabelecida com sucesso!")
            return engine
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Erro durante a conexão com o banco '{db_name}': {e}\nTRACEBACK:\n{tb_str}")
            return None

    def _resolve_item_id_from_bridge(self, bridge_id):
        """
        Recupera o id_item_nfe a partir do id da tabela de ligação (ponte).
        """
        if not self.db_engine_novo_ceos:
            return None
        
        # Se vier lista, pega o primeiro
        if isinstance(bridge_id, list):
            if len(bridge_id) > 0:
                bridge_id = bridge_id[0]
            else:
                return None

        query_sql = text("SELECT id_item_nfe FROM public.item_nfe_classificacao_produto_servico WHERE id_item_nfe_classificacao_produto_servico = :id LIMIT 1;")
        
        try:
            with self.db_engine_novo_ceos.connect() as connection:
                result = connection.execute(query_sql, {"id": bridge_id}).fetchone()
                if result:
                    return result[0] # Retorna o valor da primeira coluna
        except Exception as e:
            logger.error(f"Erro ao resolver item_nfe pela tabela ponte {bridge_id}: {e}")
        
        return None

    def _query_item_and_classification(self, id_item_nfe):
        """
        Busca TODOS os dados de um item e sua classificação associada (descricao).
        """
        if not self.db_engine_novo_ceos:
            logger.error("Conexão com o banco (novo_ceos) não está disponível.")
            return None
        if id_item_nfe is None:
            logger.error("id_item_nfe não fornecido para _query_item_and_classification.")
            return None

        query_sql = text("""
            SELECT
                i.*,
                cps.descricao AS classificacao_descricao
            FROM
                public.item_nfe AS i
            LEFT JOIN
                public.item_nfe_classificacao_produto_servico AS icps
                ON i.id_item_nfe = icps.id_item_nfe
            LEFT JOIN
                public.classificacao_produto_servico AS cps
                ON icps.id_classificacao_produto_servico = cps.id_classificacao_produto_servico
            WHERE
                i.id_item_nfe = :item_param
            LIMIT 1;
        """)

        try:
            with self.db_engine_novo_ceos.connect() as connection:
                result_proxy = connection.execute(query_sql, {"item_param": id_item_nfe})
                result_row = result_proxy.fetchone() 
                if result_row:
                    return result_row 
                else:
                    logger.warning(f"Nenhum item ou classificação encontrado para id_item_nfe: {id_item_nfe}")
                    return None
        except Exception as e:
            logger.error(f"Erro ao consultar item e classificação {id_item_nfe}: {e}")
            return None

    def _format_item_data(self, item_row):
        """
        Formata um item_nfe (RowProxy) em um dicionário Python.
        """
        if not item_row:
            return None, None

        try:
            item_data = item_row._asdict()
            classificacao = item_data.pop('classificacao_descricao', None)

            for key, value in item_data.items():
                if isinstance(value, datetime.datetime):
                    item_data[key] = value.date().isoformat()
                elif isinstance(value, datetime.date):
                    item_data[key] = value.isoformat()

            return item_data, classificacao 
        except Exception as e:
             logger.error(f"Erro ao formatar dados do item_row: {e}")
             return None, None

    def _format_output_message(self, item_dict, grupo_final, raw_data_id=None):
        """
        Formata a mensagem para o Inserter com as tabelas grupo_bp e item_nfe_grupo_bp.
        """
        if not item_dict:
             return None
        
        id_item_nfe = item_dict.get("id_item_nfe")
        
        # Converte "0" ou string vazia para None, garante int se válido
        if grupo_final == "0" or grupo_final == "" or grupo_final is None:
            grupo_final = None
        else:
            try:
                grupo_final = int(grupo_final)
            except (ValueError, TypeError):
                logger.warning(f"Grupo final inválido: {grupo_final}. Convertendo para None.")
                grupo_final = None
        
        # Monta o payload conforme a nova estrutura exigida pelo Inserter
        payload = {
            "grupo_bp": {
                "nome": None,               # Conforme solicitado
                "numero_grupo": grupo_final, # Resultado do agrupamento local
                "id_metodo_de_agrupamento_bp": 2 # Método 2 para fluxo local
            },
            "item_nfe_grupo_bp": {
                "id_item_nfe": id_item_nfe
            },
            "data_source": "nfe"
        }
        
        if raw_data_id:
            payload["raw_data_id"] = raw_data_id

        return payload

    def load_groupers(self):
        path = "groupers"
        groupers = {}
        for file in os.listdir(path):
            if file.endswith(".py") and file != "__init__.py" and file != "base_grouper.py":
                try:
                    module_name = f"{path.replace('/','.')}.{file[:-3]}"
                    module = importlib.import_module(module_name)
                    for attr in dir(module):
                        cls = getattr(module, attr)
                        if isinstance(cls, type) and issubclass(cls, BaseGrouper) and cls is not BaseGrouper:
                            groupers[cls.grouper_name] = cls(logger)
                except Exception as e:
                     logger.error(f"Erro ao carregar grouper do arquivo {file}: {e}")
        return groupers

    def shutdown(self):
        logger.info("Iniciando shutdown do NfeGrouper...")
        for grouper_name, grouper_instance in self.groupers.items():
            if hasattr(grouper_instance, 'shutdown'):
                try:
                    logger.info(f"Desligando grouper: {grouper_name}")
                    grouper_instance.shutdown()
                except Exception as e:
                     logger.error(f"Erro ao desligar grouper {grouper_name}: {e}")
        if self.db_engine_novo_ceos:
            logger.info("Desligando pool de conexões com novo_ceos...")
            try:
                self.db_engine_novo_ceos.dispose()
            except Exception as e:
                 logger.error(f"Erro ao desligar pool de conexões: {e}")
        logger.info("Shutdown do NfeGrouper concluído.")

if __name__ == '__main__':
    logger = Logger(log_to_console=True)
    grouper_nfe = NfeGrouper()
    try:
        grouper_nfe.start()
    except KeyboardInterrupt:
        logger.info("Interrupção manual detectada.")
    finally:
        grouper_nfe.shutdown()
import os
import traceback
import datetime
from sqlalchemy import create_engine, text
from service_essentials.utils.logger import Logger
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
import pandas as pd

class NfeLicitacaoLinker(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        logger.info(f"Iniciando NfeLicitacaoLinker (NFE -> Licitação)")

        logger.info(f"Configurando conexão com o banco de dados Novo CEOS")
        self.db_engine_novo_ceos = self._setup_database_connection("novo_ceos")

        if not self.db_engine_novo_ceos:
            logger.error("Falha ao inicializar conexão do banco Novo CEOS")

    def _setup_database_connection(self, db_name: str):
        try:
            db_user = os.getenv('USERNAME_PG')
            db_password = os.getenv('SENHA_PG')
            db_host = os.getenv('HOST_PG')
            db_port = os.getenv('PORT_PG')

            if not all([db_user, db_password, db_host, db_port, db_name]):
                logger.error(f"Variáveis de ambiente faltando para o banco '{db_name}'.")
                return None

            db_connection_str = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
            engine = create_engine(db_connection_str)
            engine.connect().close()
            logger.info(f"Conexão com o banco '{db_name}' estabelecida com sucesso!")
            return engine
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Erro durante a conexão com o banco '{db_name}': {e}\nTRACEBACK:\n{tb_str}")
            return None

    def process_message(self, record):
        logger.info(f"Mensagem recebida para linkar NFe-Licitacao: {record}")
        ids = record.get("ids_gerados_db")
        if not ids or "nfe" not in ids:
            logger.warning("Mensagem recebida sem 'ids_gerados_db' ou 'id_nfe'. Descartando.")
            return None

        id_nfe = ids["nfe"]

        nfe_header = self.query_nfe_header_for_linking(id_nfe)
        if not nfe_header:
            logger.error(f"NFe {id_nfe} não encontrada no banco.")
            return None 

        if nfe_header._asdict().get("id_processo_licitatorio") is not None:
            id_proc = nfe_header._asdict().get("id_processo_licitatorio")
            logger.warning(f"NFe {id_nfe} já processada (id_processo_licitatorio={id_proc}). Descartando para evitar loop.")
            return None 

        nfe_items = self.query_nfe_items(id_nfe)
        nfe_data = pd.DataFrame([nfe_header._asdict()])
        items_data = pd.DataFrame(nfe_items)
        
        data_emissao_nfe = nfe_header._asdict().get("data_emissao")

        try:
            nfe_com_pessoa = self.find_pessoa(nfe_data)
            
            empenhos_filtrados = self.find_empenhos(nfe_com_pessoa, data_emissao_nfe)
            
            liquidacoes_filtradas = self.find_liquidacoes(empenhos_filtrados, data_emissao_nfe)
            
            id_processo_encontrado = self.find_match_by_value(liquidacoes_filtradas, empenhos_filtrados, items_data)

        except Exception as e:
            logger.error(f"Erro no processo de match para NFe {id_nfe}: {e}")
            return

        if id_processo_encontrado is None:
            logger.info(f"Match não encontrado para NFe {id_nfe}")
            return

        logger.info(f"Match encontrado para NFe {id_nfe}: id_processo_licitatorio={id_processo_encontrado}.")
        response = {
            "nfe": {
                "id_nfe": id_nfe,
                "id_processo_licitatorio": id_processo_encontrado
            }
        }

        logger.info(f"Retorno final: {response}")
        return response



    def query_nfe_header_for_linking(self, id_nfe):
        query_sql = text("""
            SELECT 
                id_nfe, data_emissao, data_saida, cnpj_emitente,
                cpf_emitente,id_processo_licitatorio
            FROM public.nfe 
            WHERE id_nfe = :id_nfe
            LIMIT 1;
        """)
        try:
            with self.db_engine_novo_ceos.connect() as conn:
                result = conn.execute(query_sql, {"id_nfe": id_nfe}).fetchone()
                return result
        except Exception as e:
            logger.error(f"Erro ao consultar cabeçalho NFe {id_nfe}: {e}")
            return None

    def query_nfe_items(self, id_nfe):
        query_sql = text("""
            SELECT id_nfe, id_item, descricao_produto, valor_total_comercial, valor_total_liquido
            FROM public.item_nfe
            WHERE id_nfe = :id_nfe;
        """)
        try:
            with self.db_engine_novo_ceos.connect() as conn:
                result = conn.execute(query_sql, {"id_nfe": id_nfe}).fetchall()
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Erro ao consultar itens da NFe {id_nfe}: {e}")
            return []

    def find_pessoa(self, nfe_df):
        cpf = nfe_df.iloc[0].get("cpf_emitente")
        cnpj = nfe_df.iloc[0].get("cnpj_emitente")

        query_sql = text("""
            SELECT id_pessoa, cpf, NULL as cnpj FROM pessoa_fisica WHERE cpf = :cpf
            UNION
            SELECT id_pessoa, NULL as cpf, cnpj FROM pessoa_juridica WHERE cnpj = :cnpj;
        """)
        try:
            with self.db_engine_novo_ceos.connect() as conn:
                result = conn.execute(query_sql, {"cpf": cpf, "cnpj": cnpj}).fetchall()
                if not result:
                    return pd.DataFrame()
                return pd.DataFrame([dict(row._mapping) for row in result])
        except Exception as e:
            logger.error(f"Erro ao buscar pessoa para CNPJ {cnpj} / CPF {cpf}: {e}")
            return pd.DataFrame()

    def find_empenhos(self, pessoa_df, data_emissao_nfe): # Adicionado data_emissao_nfe
        if pessoa_df.empty:
            return pd.DataFrame()
        
        # Se a data de emissão não existir, não aplica o filtro de data
        filtro_data_sql = ""
        params = {}
        if data_emissao_nfe:
            filtro_data_sql = "AND data_empenho <= :data_emissao_param"
            params["data_emissao_param"] = data_emissao_nfe

        id_pessoas = tuple(pessoa_df["id_pessoa"].tolist())
        params["id_pessoas"] = id_pessoas

        query_sql = text(f"""
            SELECT 
                id_empenho, valor_empenho, data_empenho, 
                id_processo_licitatorio, id_pessoa
            FROM public.empenho
            WHERE id_pessoa IN :id_pessoas
              AND id_processo_licitatorio IS NOT NULL
              {filtro_data_sql};
        """)
        try:
            with self.db_engine_novo_ceos.connect() as conn:
                result = conn.execute(query_sql, params).fetchall()
                return pd.DataFrame([dict(row._mapping) for row in result])
        except Exception as e:
            logger.error(f"Erro ao buscar empenhos: {e}")
            return pd.DataFrame()

    def find_liquidacoes(self, empenhos_df, data_emissao_nfe): # Adicionado data_emissao_nfe
        if empenhos_df.empty:
            return pd.DataFrame()

        # Se a data de emissão não existir, não aplica o filtro de data
        filtro_data_sql = ""
        params = {}
        if data_emissao_nfe:
            filtro_data_sql = "AND data_liquidacao >= :data_emissao_param"
            params["data_emissao_param"] = data_emissao_nfe

        id_empenhos = tuple(empenhos_df["id_empenho"].tolist())
        params["id_empenhos"] = id_empenhos

        query_sql = text(f"""
            SELECT id_liquidacao, id_empenho, data_liquidacao, valor_liquidacao
            FROM public.liquidacao
            WHERE id_empenho IN :id_empenhos
              {filtro_data_sql};
        """)
        try:
            with self.db_engine_novo_ceos.connect() as conn:
                result = conn.execute(query_sql, params).fetchall()
                return pd.DataFrame([dict(row._mapping) for row in result])
        except Exception as e:
            logger.error(f"Erro ao buscar liquidações: {e}")
            return pd.DataFrame()


    def find_match_by_value(self, liquidacoes_df, empenhos_df, itens_df):
        if empenhos_df.empty or itens_df.empty:
            return None

        valor_total_nfe = itens_df["valor_total_liquido"].sum()
        
        # 1. Agrupa as liquidações por empenho e SOMA seus valores
        #    Se liquidacoes_df estiver vazio, isso cria um DF vazio (sem problemas).
        liquidacoes_agrupadas_df = liquidacoes_df.groupby('id_empenho')['valor_liquidacao'].sum().reset_index()
        liquidacoes_agrupadas_df = liquidacoes_agrupadas_df.rename(
            columns={'valor_liquidacao': 'valor_liquidacao_soma'}
        )
        
        df_merged = pd.merge(
            empenhos_df,
            liquidacoes_agrupadas_df,
            on='id_empenho',
            how='left'
        )

        try:
            match = df_merged[
                (df_merged['valor_empenho'] == valor_total_nfe) |
                (df_merged['valor_liquidacao_soma'] == valor_total_nfe)
            ]

            if not match.empty:
                return int(match.iloc[0]['id_processo_licitatorio'])

        except Exception as e:
            logger.error(f"Erro ao realizar matching de valores (pandas merge/groupby): {e}")

        return None



if __name__ == '__main__':
    logger = Logger(log_to_console=True)
    linker = NfeLicitacaoLinker()
    linker.start()

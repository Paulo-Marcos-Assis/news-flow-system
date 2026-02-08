import os
import traceback
from groupers.base_grouper import BaseGrouper
from sqlalchemy import create_engine, text


class Medicamentos(BaseGrouper):

    grouper_name = "medicamentos"

    def __init__(self, logger):
        """
        Inicializa o grouper, passa o logger para a classe base
        e estabelece as conexões com o banco.
        """
        super().__init__(logger) # Passa o logger para a classe base
        self.logger.info("MedicamentosGrouper: Inicializando e conectando ao BD...")
        
        self._Connect_bd()

    def _Connect_bd(self):

        self.logger.info("Configurando conexão com o banco de dados de leitura (Homologação)...")
        self.db_engine_homologacao = self._setup_database_connection("homologacao")
        
        if not self.db_engine_homologacao:
            self.logger.error("Falha ao inicializar uma ou mais conexões com o banco.")

    def _setup_database_connection(self, db_name: str):
        """Cria e testa uma conexão com um banco de dados específico."""
        try:
            db_user = os.getenv('USERNAME_PG')
            db_password = os.getenv('SENHA_PG')
            db_host = os.getenv('HOST_PG')
            db_port = os.getenv('PORT_PG')

            if not all([db_user, db_password, db_host, db_port, db_name]):
                self.logger.error(f"Uma ou mais variáveis de ambiente para a conexão com o banco '{db_name}' não estão definidas.")
                return None

            self.logger.info(f"Estabelecendo conexão com o banco: {db_name}...")
            db_connection_str = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
            engine = create_engine(db_connection_str)
            engine.connect().close()
            self.logger.info(f"Conexão com o banco '{db_name}' estabelecida com sucesso!")
            return engine
        except Exception as e:
            tb_str = traceback.format_exc()
            self.logger.error(f"Erro durante a conexão com o banco '{db_name}': {e}\nTRACEBACK:\n{tb_str}")
            return None

    def _get_grupo_por_gtin(self, gtin: any):
        """Consulta o banco 'homologacao' para encontrar o ID do grupo de um GTIN."""

        if not self.db_engine_homologacao or gtin is None:
            return None
        
        gtin_limpo = ""
        try:
            gtin_limpo = str(int(float(gtin)))
        except (ValueError, TypeError):
            gtin_limpo = str(gtin).strip()
        
        self.logger.info(f"  -> Consultando GTIN limpo: '{gtin_limpo}'")

        query = text("SELECT id_grupo FROM validacao.gvh_101025_agrupamento_ean_grupos WHERE codigo = :codigo_param LIMIT 1;")
        
        grupo_encontrado = None
        try:
            with self.db_engine_homologacao.connect() as connection:
                result = connection.execute(query, {"codigo_param": gtin_limpo})
                grupo_encontrado = result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Erro ao consultar o GTIN {gtin_limpo} no banco de homologação: {e}")
        
        if grupo_encontrado is not None:
            self.logger.info(f"  -> SUCESSO na consulta: Para o GTIN '{gtin_limpo}', o grupo encontrado foi: ID '{grupo_encontrado}'")
        else:
            self.logger.info(f"  -> INFO: Para o GTIN '{gtin_limpo}', nenhum grupo foi encontrado na view.")

        return grupo_encontrado


    def group(self, item):

        if not self.db_engine_homologacao:
            self.logger.error("Uma ou mais conexões com o banco de dados estão indisponíveis. Descartando mensagem.")
            return

        gtin = item.get("gtin_produto")
        ncm = item.get("ncm_produto")
        grupo_encontrado = None

        if gtin:
            self.logger.info(f"Processando item: {item} com GTIN: '{gtin}' e NCM: '{ncm}'...")
            grupo_encontrado = self._get_grupo_por_gtin(gtin)
        else:
            self.logger.info(f"Processando item: {item} sem GTIN (NCM: '{ncm}'). Grupo será NULL.")
        
        
        self.logger.info("Processamento da mensagem finalizado.")

        return grupo_encontrado


    def shutdown(self):
        """Fecha todas as conexões de forma limpa ao desligar."""
        if self.db_engine_homologacao:
            self.logger.info("Desligando o pool de conexões com 'homologacao'...")
            self.db_engine_homologacao.dispose()

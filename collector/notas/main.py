import os
import io
import json
import pandas as pd
from decimal import Decimal
from datetime import date, datetime
import boto3
from botocore.client import Config
import traceback
import hashlib
from decimal import Decimal, ROUND_HALF_UP

from service_essentials.utils.logger import Logger
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.object_storage_manager.minio_manager import MinIOManager
from service_essentials.basic_service.cached_collector_service import CachedCollectorService


class CollectorNotas(CachedCollectorService):
    def __init__(self):
        super().__init__(data_source="nfe")
        # Inicializa o gerenciador do MinIO para poder usá-lo no process_message
        self.object_storage_manager = MinIOManager()

    def collect_data(self, message):
        nome_arquivo_json = None  # Inicializa para o bloco 'finally'
        try:
            # 1. Extração de Parâmetros
            url = message["url_s3"]
            bucket = message["bucket"]
            prefix = message["prefix"]
            cabecalho = message["cabecalho"]
            itens = message["itens"]
            format = message["format"]
            target_date_str = message["date"]
            logger.info(f"Iniciando coleta de notas para a data específica: {target_date_str}")

            target_date = pd.to_datetime(target_date_str)
            year_month_for_filename = target_date.strftime('%Y%m')

            # 2. Busca e Carregamento dos Arquivos do MÊS
            s3 = self.criar_cliente(url)
            arquivos_parquet = self.buscar_arquivos_nfe(s3, bucket, prefix, cabecalho, itens, format, year_month_for_filename)
            
            if not arquivos_parquet['Cabecalho'] or not arquivos_parquet['Itens']:
                logger.warning(f"Arquivos Parquet do mês {year_month_for_filename} não encontrados.")
                return None

            df_cabecalho = self.carregar_parquet(s3, bucket, arquivos_parquet['Cabecalho'])
            df_itens = self.carregar_parquet(s3, bucket, arquivos_parquet['Itens'])

            if df_cabecalho.empty or df_itens.empty:
                logger.error("DataFrames de cabeçalho ou itens estão vazios.")
                return None

            df_cabecalho_com_itens = self.juntar_df_exlcuir_colunas_repetidas(df_cabecalho, df_itens)

            # 3. Filtragem pelo dia alvo
            logger.info(f"Filtrando o DataFrame do mês para manter apenas os dados do dia: {target_date.date()}")
            if 'DATA_EMISSAO' not in df_cabecalho_com_itens.columns:
                 logger.error("Coluna 'DATA_EMISSAO' não encontrada para realizar o filtro por dia.")
                 return None
            df_cabecalho_com_itens['DATA_EMISSAO'] = pd.to_datetime(df_cabecalho_com_itens['DATA_EMISSAO'], errors='coerce')
            
            df_do_dia = df_cabecalho_com_itens[df_cabecalho_com_itens['DATA_EMISSAO'].dt.date == target_date.date()]

            if df_do_dia.empty:
                logger.warning(f"Nenhum registro encontrado para a data {target_date.date()} no arquivo do mês.")
                return None
            
            logger.info(f"Encontradas {len(df_do_dia)} linhas para o dia {target_date.date()}.")

            # 4. Conversão para JSON, Upload no MinIO e Publicação do "Claim Check"
            lista_de_notas_do_dia = self.dataframe_para_lista_dict(df_do_dia)
            
            if not lista_de_notas_do_dia:
                logger.warning(f"A conversão para JSON não gerou notas para o dia {target_date_str}.")
                return None

            return lista_de_notas_do_dia

            # timestamp = int(datetime.now().timestamp())
            # nome_arquivo_json = f"notas_{target_date_str}_{timestamp}.json"
            
            # with open(nome_arquivo_json, 'w', encoding='utf-8') as f:
            #     json.dump(lista_de_notas_do_dia, f, ensure_ascii=False)

            # bucket_name = os.getenv("BUCKET_NOTAS", "notas-fiscais-diarias")
            # logger.info(f"Fazendo upload do arquivo '{nome_arquivo_json}' para o bucket '{bucket_name}'...")
            # self.object_storage_manager.upload_file(bucket_name, nome_arquivo_json, nome_arquivo_json)
            # logger.info("Upload bem-sucedido.")

            # claim_check_message = {
            #     "source": "NFE_Collector",
            #     "date": target_date_str,
            #     "bucket": bucket_name,
            #     "data_file": nome_arquivo_json
            # }

            # # A classe base publicará esta mensagem pequena.
            # return claim_check_message
            
        except Exception as e:
            # Logger corrigido para não usar 'exc_info'
            tb_str = traceback.format_exc()
            logger.error(f"Erro inesperado no processamento do CollectorNotas: {e}\nTRACEBACK:\n{tb_str}")
            return None
        finally:
            # Garante que o arquivo temporário local seja sempre apagado
            if nome_arquivo_json and os.path.exists(nome_arquivo_json):
                os.remove(nome_arquivo_json)

    def criar_cliente(self, url):
        try:
            access_key = "HxZMHfYDNSNABmCN4Wcu"
            secret_key = "kkS7wuKGkOt3qWtTVUb11czmI4FPVvW2YmytnJ7N"
            endpoint = url
            s3 = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=Config(signature_version='s3v4'),
                region_name='us-east-1'
            )
            return s3
        except Exception as e:
            logger.error(f"Erro ao criar cliente S3: {e}")
            raise

    def buscar_arquivos_nfe(self, s3, bucket, prefix, cabecalho, itens, format, date):
        arquivo_cabecalho = f"{prefix}{cabecalho}{date}{format}"
        arquivo_itens = f"{prefix}{itens}{date}{format}"
        arquivos_encontrados = {'Cabecalho': None, 'Itens': None}
        try:
            response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    if key == arquivo_cabecalho:
                        arquivos_encontrados['Cabecalho'] = key
                    elif key == arquivo_itens:
                        arquivos_encontrados['Itens'] = key
            else:
                logger.warning(f"Nenhum conteúdo encontrado no bucket {bucket} com prefixo {prefix}")
        except Exception as e:
            logger.error(f"Erro ao listar objetos do bucket {bucket}: {e}")
        return arquivos_encontrados

    def carregar_parquet(self, s3, bucket, key):
        try:
            logger.info(f"Carregando arquivo: {key}")
            response = s3.get_object(Bucket=bucket, Key=key)
            body = response['Body'].read()
            buffer = io.BytesIO(body)
            df = pd.read_parquet(buffer)
            logger.info(f"Arquivo {key} carregado com {len(df)} linhas.")

            # Corrige valores monetários
            colunas_monetarias = [
                'VALOR_UNITARIO_COMERCIAL',
                'VALOR_DESCONTO',
                'VALOR_FRETE',
                'VALOR_SEGURO',
                'VALOR_OUTRAS_DESPESAS',
                'Valor_Total_Comercial',
                'Valor_Total_Liquido',
                'Valor_Unitario_Liquido'
            ]
            for col in colunas_monetarias:
                if col in df.columns:
                    df[col] = df[col].apply(
                        lambda x: Decimal(str(x)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if pd.notna(x) else x
                    )

            return df
        except s3.exceptions.NoSuchKey:
            logger.error(f"Arquivo {key} não encontrado no bucket {bucket}.")
        except Exception as e:
            logger.error(f"Erro ao carregar o arquivo Parquet {key}: {e}")
        return pd.DataFrame()


    def juntar_df_exlcuir_colunas_repetidas(self, df_cabecalho, df_itens):
        try:
            df_join = pd.merge(df_cabecalho, df_itens, on='NFE_ID', how='inner')
            colunas_a_remover = ['AnoMes_y', 'AnoMes_x']
            colunas_existentes_para_remover = [col for col in colunas_a_remover if col in df_join.columns]
            df_join = df_join.drop(columns=colunas_existentes_para_remover)
            return df_join
        except Exception as e:
            logger.error(f"Erro ao juntar DataFrames: {e}")
            return pd.DataFrame()


    def processar_valor(self, valor):
        if pd.isna(valor) or (isinstance(valor, str) and valor.strip() == ''):
            return None
        if isinstance(valor, (date, datetime)):
            return valor.isoformat()
        if isinstance(valor, (int, float, Decimal)):
            if isinstance(valor, Decimal):
                valor = float(valor)
            if isinstance(valor, float) and valor.is_integer():
                return int(valor)
            return valor
        return valor


    def dataframe_para_lista_dict(self, df):
        try:
            colunas_item = [
                'ITEM_ID', 'CFOP_PRODUTO', 'NCM_PRODUTO', 'GTIN_PRODUTO', 
                'DESCRICAO_PRODUTO', 'QUANTIDADE_COMERCIAL', 'UNIDADE_COMERCIAL', 
                'VALOR_UNITARIO_COMERCIAL', 'VALOR_DESCONTO', 'VALOR_FRETE', 
                'VALOR_SEGURO', 'VALOR_OUTRAS_DESPESAS', 'Valor_Total_Comercial', 
                'Valor_Total_Liquido', 'Valor_Unitario_Liquido', 'SITUACAO', 'DATA_EMISSAO_NOTA', 
                'COD_MUNICIPIO_ORIGEM', 'COD_MUNICIPIO_DESTINO']
            
            colunas_existentes_item = [col for col in colunas_item if col in df.columns]
            # A lógica de exclusão volta a funcionar, pois não mexemos mais nos nomes das colunas
            colunas_nota = [col for col in df.columns if col not in colunas_existentes_item]
            
            notas = []
            # O groupby volta a usar a chave em maiúsculas 'NFE_ID'
            for nfe_id, grupo in df.groupby('NFE_ID'):
                dados_nota_raw = grupo.iloc[0][colunas_nota].to_dict()
                dados_nota = {k: self.processar_valor(v) for k, v in dados_nota_raw.items()}

                itens_raw = grupo[colunas_existentes_item].to_dict(orient='records')
                itens = [{k: self.processar_valor(v) for k, v in item.items()} for item in itens_raw]
                
                # A chave de saída continua sendo 'item_nfe', pois é o nosso padrão
                dados_nota['item_nfe'] = itens
                notas.append(dados_nota)
                
            return notas
        except Exception as e:
            # A correção do logger permanece
            tb_str = traceback.format_exc()
            logger.error(f"Erro ao converter DataFrame para lista de dicionários: {e}\nTRACEBACK:\n{tb_str}")
            return []

if __name__ == '__main__':
    logger = Logger(log_to_console=True)
    processor = CollectorNotas()
    processor.start()
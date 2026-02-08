"""S3 Client for Esfinge Collector - handles S3 file operations."""

import io
import logging
import os
from typing import Optional, Dict, Any

import boto3
import pandas as pd
from botocore.client import Config

from service_essentials.exceptions.Error_Flow_exception import InvalidMessageFormatError


class S3Client:
    """Handles S3 file operations for the Esfinge collector."""

    # File naming mappings - main data files with year suffix
    MAIN_FILES = {
        'processo_licitatorio': 'ProcessoLicitatorio',
        'item_licitacao': 'ItemLicitacao',
        'participante_licitacao': 'ParticipanteLicitacao',
        'convidado_licitacao': 'ConvidadoLicitacao',
        'contrato': 'Contrato',
        'empenho': 'Empenho',
        'liquidacao': 'Liquidacao',
        'pagamento_empenho': 'PagamentoEmpenho',
        'cotacao': 'cotacao',
    }

    # Auxiliary files in /aux folder without year suffix
    AUX_FILES = {
        'unidade_gestora': 'UnidadeGestora',
        'tipo_licitacao': 'TipoLicitacao',
        'modalidade_licitacao': 'ModalidadeLicitacao',
        'tipo_objeto_licitacao': 'TipoObjetoLicitacao',
        'situacao_processo_licitatorio': 'SituacaoProcessoLicitatorio',
        'tipo_cotacao': 'TipoCotacao',
        'categoria_economica_despesa': 'CategoriaEconomicaDespesa',
        'detalhamento_elemento_despesa': 'DetalhamentoElementoDespesa',
        'elemento_despesa': 'ElementoDespesa',
        'ente': 'Ente',
        'funcao': 'Funcao',
        'poder_orgao': 'PoderOrgao',
        'programa': 'Programa',
        'projeto_atividade': 'ProjetoAtividade',
        'remessa_unidade_gestora': 'RemessaUnidadeGestora',
        'situacao_remessa': 'SituacaoRemessa',
        'sub_funcao': 'SubFuncao',
        'tipo_esfera': 'TipoEsfera',
        'tipo_unidade': 'TipoUnidade',
        'unidade_orcamentaria': 'UnidadeOrcamentaria',
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.s3_client = None
        self.url_s3 = None
        self.bucket = None
        self.data_path = None
        self.year = None

    def configure(self, message: Dict[str, Any]) -> None:
        """Load S3 configuration from message and create client."""
        self._load_config(message)
        self._create_client()

    def _load_config(self, message: Dict[str, Any]) -> None:
        """Extract and validate S3 configuration from message."""
        self.url_s3 = message.get("url_s3")
        self.bucket = message.get("bucket")
        self.data_path = message.get("data_path", message.get("prefix", ""))
        self.year = str(message.get("year", "")).strip("[]\"'")

        if not all([self.url_s3, self.bucket, self.year]):
            raise InvalidMessageFormatError(
                message, 
                "Missing required config: url_s3, bucket, and year are required"
            )

    def _create_client(self) -> None:
        """Create boto3 S3 client."""
        access_key = os.getenv("ESFINGE_COLLECT_OBJECT_STORAGE_ACCESS_KEY")
        secret_key = os.getenv("ESFINGE_COLLECT_OBJECT_STORAGE_SECRET_KEY")
        secure = os.getenv("ESFINGE_COLLECT_MINIO_SECURE", "true").lower() == "true"

        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.url_s3,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',
            verify=secure
        )
        self.logger.info(f"S3 client configured for bucket: {self.bucket}")

    def _get_file_path(self, entity: str) -> str:
        """Build the S3 file path for an entity."""
        # Check if it's an auxiliary file (no year suffix, in /aux folder)
        if entity in self.AUX_FILES:
            file_name = self.AUX_FILES[entity]
            return f"{self.data_path}/aux/{file_name}.csv"

        # Check if it's a main file (with year suffix)
        if entity in self.MAIN_FILES:
            file_name = self.MAIN_FILES[entity]
            return f"{self.data_path}/{file_name}_{self.year}.csv"

        # Fallback: capitalize each part of snake_case name
        file_name = ''.join(part.capitalize() for part in entity.split('_'))
        return f"{self.data_path}/{file_name}_{self.year}.csv"

    def _file_exists(self, file_path: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=file_path)
            return True
        except self.s3_client.exceptions.ClientError:
            return False

    def load_csv(self, entity: str) -> Optional[pd.DataFrame]:
        """
        Load a CSV file from S3 for the given entity.
        
        Args:
            entity: Entity name (e.g., 'contrato', 'empenho')
            
        Returns:
            DataFrame with CSV data or None if not found
        """
        if not self.s3_client:
            raise RuntimeError("S3 client not configured. Call configure() first.")

        file_path = self._get_file_path(entity)

        if not self._file_exists(file_path):
            self.logger.debug(f"File not found: {file_path}")
            return None

        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
            df = pd.read_csv(io.BytesIO(response['Body'].read()))
            self.logger.info(f"Loaded {entity}: {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            self.logger.error(f"Error loading {entity}: {e}")
            return None

    # Backward compatibility aliases
    def set_s3_client(self, message: Dict[str, Any]) -> None:
        """Alias for configure() - backward compatibility."""
        self.configure(message)

    def get_s3_file(self, entity: str, message: Optional[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
        """Alias for load_csv() - backward compatibility."""
        if message:
            self._load_config(message)
        return self.load_csv(entity)

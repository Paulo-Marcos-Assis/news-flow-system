import hashlib
import json
import os
import shutil
import logging
import time
from datetime import datetime
from typing import Any, Optional, Union, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from service_essentials.basic_service.cached_collector_service import CachedCollectorService

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CollectorPNCP(CachedCollectorService):
    """
    A service to collect public procurement data from the PNCP API.
    It inherits from CachedCollectorService to automatically handle caching and
    publishing of individual records.
    """

    def __init__(self):
        """
        Initializes the CollectorPNCP service, setting up a session with retry logic.
        """
        super().__init__(data_source="pncp")
        self.session = self._create_retry_session()

    def _create_retry_session(self) -> requests.Session:
        """
        Creates a requests Session with a retry mechanism.
        """
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get_page_limit(self, api_url: str, params: dict, headers: dict) -> Optional[int]:
        """
        Gets the total number of pages for the given query.
        Returns:
            Optional[int]: The total number of pages, or None if no content.
        """
        try:
            response = self.session.get(api_url, params=params, headers=headers)
            logger.info(f"Requesting {params.get('dataInicial')}: {response}")
            response.raise_for_status()
            if response.status_code == 204:
                logger.info(f"No content found for {params.get('dataInicial')}. Status code: 204")
                return None
            response_data = response.json()
            limit = response_data.get('totalPaginas', 0)
            logger.info(f"Pages for {params.get('dataInicial')}: {limit}")
            return limit
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get page limit for {params.get('dataInicial')} after multiple retries: {e}")
            return None

    def _process_and_attach_arquivos(self, doc: dict, arquivos: list) -> None:
        """Attaches the original document list to the main document."""
        doc['documentos'] = arquivos

    def get_arquivos_for_contratacao(self, contratacao: dict[str, Any], headers: dict) -> list[dict[str, Any]]:
        """
        Fetches associated documents for a given contratacao.
        """
        logger.info(f"Searching docs for contratacão: {contratacao.get('numeroControlePncp')} ")
        orgao_entidade = contratacao.get('orgaoEntidade') or {}
        cnpj = orgao_entidade.get('cnpj')
        ano_compra = contratacao.get('anoCompra')
        sequencial_compra = contratacao.get('sequencialCompra')

        if not all([cnpj, ano_compra, sequencial_compra]):
            logger.warning(f"Missing required fields for fetching documents for contratacao: {contratacao.get('numeroControlePncp')}")
            return []

        arquivos_url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/{ano_compra}/{sequencial_compra}/arquivos"

        try:
            response = self.session.get(arquivos_url, headers=headers)
            if response.status_code == 404:
                logger.info(f"No documents found for contratacao {cnpj}/{ano_compra}/{sequencial_compra} (404)")
                return []
            response.raise_for_status()
            if response.status_code == 204:
                logger.info(f"No content for documents for contratacao {cnpj}/{ano_compra}/{sequencial_compra} (204)")
                return []
            logger.info(f"Docs collected: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get documents for contratacao {cnpj}/{ano_compra}/{sequencial_compra}: {e}")
            return []

    def get_arquivos_for_contrato(self, contrato: dict[str, Any], headers: dict) -> list[dict[str, Any]]:
        """
        Fetches associated documents for a given contrato.
        """
        logger.info(f"Searching docs for contrato: {contrato.get('numeroControlePNCP')}")
        orgao_entidade = contrato.get('orgaoEntidade') or {}
        cnpj = orgao_entidade.get('cnpj')
        ano_contrato = contrato.get('anoContrato')
        sequencial_contrato = contrato.get('sequencialContrato')

        if not all([cnpj, ano_contrato, sequencial_contrato]):
            logger.warning(f"Missing required fields for fetching documents for contrato: {contrato.get('numeroControlePNCP')}")
            return []

        arquivos_url = f"https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/contratos/{ano_contrato}/{sequencial_contrato}/arquivos"

        try:
            response = self.session.get(arquivos_url, headers=headers)
            if response.status_code == 404:
                logger.info(f"No documents found for contrato {cnpj}/{ano_contrato}/{sequencial_contrato} (404)")
                return []
            response.raise_for_status()
            if response.status_code == 204:
                logger.info(f"No content for documents for contrato {cnpj}/{ano_contrato}/{sequencial_contrato} (204)")
                return []
            logger.info(f"Docs collected for contrato: {response.json()}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get documents for contrato {cnpj}/{ano_contrato}/{sequencial_contrato}: {e}")
            return []

    def get_documents(self, api_url: str, params: dict, headers: dict, limit: int) -> list[dict[str, Any]]:
        """
        Fetches all documents (bids or contracts) from all pages.
        """
        all_documents = []
        for page in range(1, limit + 1):
            try:
                params['pagina'] = page
                response = self.session.get(api_url, params=params, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                documents = response_data.get('data', [])
                all_documents.extend(documents)
                logger.info(f"Successfully fetched page {page}/{limit} for day {params.get('dataInicial')}.")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to process page {page}/{limit} for day {params.get('dataInicial')}. Skipping this page. Error: {e}")
                continue
        return all_documents

    def collect_data(self, message: dict[str, Any]) -> List[dict[str, Any]]:
        """
        Processes a message to collect data from the PNCP API.
        This method is called by CachedCollectorService on a cache miss.
        """
        api_url: str = message["api_url"]
        modality = message.get("modalidade")
        start_date: str = message["data_inicial"]
        end_date: str = message["data_final"]
        
        headers: dict[str, str] = {'accept': '*/*'}
        params: dict[str, Any] = {
            'dataInicial': start_date,
            'dataFinal': end_date,
            'pagina': 1,
        }

        entity_type = "contrato"
        if "contratacoes/publicacao" in api_url:
            entity_type = "contratacao"
            if not modality:
                logger.error(f"Message for 'contratacoes' is missing 'modalidade': {message}")
                return []
            params['codigoModalidadeContratacao'] = modality
            params['uf'] = 'sc'
        elif "contratos" in api_url:
            entity_type = "contrato"
        elif "instrumentoscobranca/inclusao" in api_url:
            entity_type = "instrumento_cobranca"
        else:
            logger.error(f"Received a message with an unknown api_url: {api_url}")
            return []

        limit = self.get_page_limit(api_url, params, headers)
        if not limit:
            return []

        documents = self.get_documents(api_url, params, headers, limit)
        if not documents:
            logger.warning(f"No documents found for {start_date} after processing all pages.")
            return []

        # --- Document ('arquivos') fetching and filtering logic ---
        if entity_type == "contratacao":
            for doc in documents:
                arquivos = self.get_arquivos_for_contratacao(doc, headers)
                self._process_and_attach_arquivos(doc, arquivos)
        
        elif entity_type == "contrato":
            filtered_documents = [doc for doc in documents if doc.get("unidadeOrgao", {}).get("ufSigla") == "SC"]
            if not filtered_documents:
                logger.warning(f"No SC contracts found for {start_date} after filtering.")
                return []
            for doc in filtered_documents:
                arquivos = self.get_arquivos_for_contrato(doc, headers)
                self._process_and_attach_arquivos(doc, arquivos)
            documents = filtered_documents
        
        elif entity_type == "instrumento_cobranca":
            filtered_documents = [doc for doc in documents if doc.get("recuperarContratoDTO", {}).get("unidadeOrgao", {}).get("ufSigla") == "SC"]
            if not filtered_documents:
                logger.warning(f"No SC instrumentos_cobranca found for {start_date} after filtering.")
                return []
            documents = filtered_documents

        # Add entity_type to each record before returning
        for doc in documents:
            doc['entity_type'] = entity_type
            
        return documents


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("################## PNCP Collector Started ###############")
    sentry_URL = os.getenv("URL_SENTRY")
    if sentry_URL:
        import sentry_sdk
        sentry_sdk.init(sentry_URL)
    processor = CollectorPNCP()
    processor.start()
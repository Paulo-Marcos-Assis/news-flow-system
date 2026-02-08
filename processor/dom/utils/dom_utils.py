
import os
import hashlib
import tempfile
import requests
import shutil
import datetime

class DomUtils:

    @staticmethod
    def get_doc_table_fields(document):
        doc_table_fields = {
            'Aviso de Licitação': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Retificação de Aviso de Licitação': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Extrato de Contrato': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Termo Aditivo': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Termo de Ratificação': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Retificação de Edital': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Retificação de Homologação': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Retificação de Termo Aditivo': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Termo de Referência': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Termo de Anulação': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Termo de Adjudicação': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Ata de Licitação Fracassada': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Ata de Registro de Preços': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Ata de Sessão Pública': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Ata de Solicitações': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Retificação de Termo de Formalização': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Termo de Credenciamento': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Termo de Formalização': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Retificação de Contratação Direta': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Ato de Contratação Direta': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Termo de Formalização': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            "Aviso de Dispensa": {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            "Aviso de Inexigibilidade": {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            "Termo de Homologação e Adjudicação": {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            "Termo de Homologação": {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Dispensa de Licitação': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Inexigibilidade de Licitação': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            },
            'Edital': {
                'processo_licitatorio': ['codigo_sfinge', 'data_inicio_propostas', 'numero_edital', 'numero_processo', 'objeto', 'data_limite_propostas', 'data_abertura_propostas'],
                'ente': ['ente'],
                'unidade_gestora': ['nome_ug'],
                'modalidade_licitacao': ['descricao']
            }
        }

        return doc_table_fields.get(document)

    @staticmethod
    def get_table_fields(table):
        table_fields = {
            'documento': ['codigo_dom', 'titulo_dom', 'data_publicacao_dom', 'url_pdf_dom', 'url_dom'],
            'tipo_documento': ['tipo_documento']
        }

        return table_fields.get(table)

    @staticmethod
    def download_and_store(url: str, bucket_name: str, object_name: str, storage_manager: any, logger: any):
        """
        Downloads a document from a URL, uploads it to object storage (MinIO).
        """
        
        temp_file_path = None
        try:
            logger.info(f"Downloading document for object storage from: {url}")
            response = requests.Session().get(url, stream=True)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response.raw, tmp_file)
                temp_file_path = tmp_file.name

            logger.info(f"Uploading document from {url} to object storage at path: {object_name}")
            storage_manager.upload_file(bucket_name, object_name, temp_file_path)
            logger.info(f"Successfully uploaded document from {url} to {object_name}")
            return object_name
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download document from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to upload document from {url} to object storage: {e}")
            return None
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

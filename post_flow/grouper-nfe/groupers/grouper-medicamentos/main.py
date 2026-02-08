import logging
import os
import json
import re
import csv
import time
from langchain_ollama import ChatOllama

from src.utils.get_config import get_raw_config, get_param, get_ollama_host
from src.data_processing.data_cleaning import clean_description
from src.NER.ner import NerProcessor
from src.data_processing.text_preprocessor import preprocess_candidates
from src.heuristics.match_2_numbers import apply_number_heuristic
from src.heuristics.structured_data import DrugDataProcessor
from src.llm_linking.inference import get_llm_link

from service_essentials.utils.logger import Logger
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService


class GrouperMedicamentos(BasicProducerConsumerService):    
    """
    Orquestra o pipeline de inferência completo para processar uma única descrição de produto.
    """
    def __init__(self):
        super().__init__()  
        """
        Inicializa o pipeline, carregando configurações e preparando todos os componentes necessários.
        """
        logging.info("--- Inicializando o Pipeline de Inferência ---")

        # 1. Carregar configurações
        try:
            self.solr_url = get_raw_config('solr', 'solr_url')
            self.db_connection_string = get_raw_config('postgres', 'db_connection_string')
            self.score_threshold = get_param('score_threshold')
            
            ollama_host = get_ollama_host()
            os.environ["OLLAMA_HOST"] = ollama_host
            model_name = get_param('model')
            temperature = get_param('temperature')
            
            # Carrega o template de prompt
            script_dir = os.path.dirname(__file__)
            prompt_template_path = os.path.abspath(os.path.join(script_dir, 'prompt-templates', 'prompt.txt'))
            with open(prompt_template_path, 'r', encoding='utf-8') as f:
                self.prompt_template = f.read()

        except Exception as e:
            logging.error(f"Falha ao carregar configurações. Erro: {e}")
            raise

        # 2. Inicializar componentes
        logging.info("Inicializando componentes do pipeline...")
        self.ner_processor = NerProcessor(self.solr_url, self.db_connection_string, self.score_threshold)
        self.drug_data_processor = DrugDataProcessor()
        self.llm = ChatOllama(model=model_name, temperature=temperature)
        logging.info("--- Pipeline Inicializado com Sucesso ---")

    def process_description(self, description: str) -> dict:
        """
        Processa uma única string de descrição através de todas as etapas do pipeline.
        
        Args:
            description: A string de descrição do produto a ser processada.
            
        Returns:
            Um dicionário contendo o resultado final, a explicabilidade e as métricas.
        """
        logging.info(f"--- Iniciando processamento para a descrição: '{description}' ---")
        
        # Etapa 1: Limpeza da descrição
        cleaned_description = clean_description(description)
        if not cleaned_description:
            logging.warning("A descrição está vazia após a limpeza. Abortando.")
            return {"error": "Descrição vazia"}, description, []

        # Etapa 2: NER - Geração de Candidatos
        ner_candidates = self.ner_processor.process_description(cleaned_description)
        if not ner_candidates:
            logging.warning("O NER não retornou candidatos. Retornando resposta nula.")
            return 
        
        # Etapa 3: Pré-processamento dos candidatos
        preprocessed_candidates = preprocess_candidates(ner_candidates)

        # Etapa 4: Heurística de Números
        heuristic_candidates = apply_number_heuristic(cleaned_description, preprocessed_candidates)

        # Etapa 5: Estruturação dos Dados
        # O processador espera um dicionário no formato {descrição: candidatos}
        structured_candidates_dict = self.drug_data_processor.run_pipeline({cleaned_description: heuristic_candidates})
        structured_candidates = structured_candidates_dict.get(cleaned_description, []) # Ensure it's a list

        # Renomeia e reordena os campos dos candidatos para corresponder ao prompt
        pruned_candidates = []
        key_mapping = {
            'principio_ativo': 'active_ingredient',
            'concentracao': 'concentration',
            'forma_farmaceutica': 'dosage_form',
            'qtde_dosage_form': 'quantity',
            'nome_med': 'drug_name',
            'manufacturer': 'manufacturer',
            'packaging': 'packaging',
            'id_grupo': 'id_grupo',
            'registro': 'registro'
        }
        desired_order = [
            'active_ingredient', 'concentration', 'dosage_form', 'quantity',
            'drug_name', 'manufacturer', 'packaging', 'id_grupo', 'registro'
        ]

        for candidate in structured_candidates:
            new_candidate = {}
            # Adiciona os campos na ordem desejada
            for new_key in desired_order:
                old_key = next((k for k, v in key_mapping.items() if v == new_key), None)
                if old_key and old_key in candidate:
                    new_candidate[new_key] = candidate[old_key]
            pruned_candidates.append(new_candidate)

        # Save final candidates to a file (optional, but good for debugging)
        # sanitized_description = re.sub(r'[\W_]+', '_', cleaned_description)
        # file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', f"final_candidates_{sanitized_description}.json")
        # with open(file_path, 'w', encoding='utf-8') as f:
        #     json.dump(pruned_candidates, f, ensure_ascii=False, indent=4) # Save pruned candidates
        # logging.info(f"Candidatos finais (pruned) salvos em: {file_path}")
        
        if not pruned_candidates: # Check pruned_candidates
            logging.warning("Nenhum candidato restou após as heurísticas e poda. Retornando resposta nula.")
            result = {"input_description": description, "answer": "0", "explicability": "Nenhum candidato sobreviveu às heurísticas e poda."}
            return result, cleaned_description, []

        # Etapa 6: Linking com LLM
        final_answer, think_string, metrics = get_llm_link(
            cleaned_description,
            pruned_candidates, # Pass the pruned candidates
            self.llm,
            self.prompt_template
        )

        # Encontrar o registro de apresentação correspondente ao id_grupo retornado
        apresentacao_registro = "N/A"
        descricao_medicamentos = None

        if final_answer != "0":
            for candidate in pruned_candidates:
                id_grupo = candidate.get('id_grupo')
                if isinstance(id_grupo, list):
                    id_grupo = id_grupo[0] if id_grupo else None
                
                if str(id_grupo) == final_answer:
                    apresentacao_registro = candidate.get('registro', "N/A")
                    
                    campos_para_concatenar = []
                    keys_to_extract = ['active_ingredient', 'concentration', 'dosage_form', 'quantity']

                    for key in keys_to_extract:
                        valor = candidate.get(key)
                        
                        # Pula se for None ou vazio
                        if not valor:
                            continue
                        
                        # Se for uma lista (ex: ['PREDNISONA']), junta os itens ou pega o primeiro
                        if isinstance(valor, list):
                            valor_limpo = " ".join([str(v) for v in valor])
                        else:
                            valor_limpo = str(valor)
                        
                        campos_para_concatenar.append(valor_limpo)
                    
                    # Filtra valores nulos ou vazios e junta com um espaço
                    # str(c) garante que números virem texto
                    descricao_medicamentos = " ".join([str(c) for c in campos_para_concatenar if c])
                    # --------------------------------------------------------
                    break

        result = {
            "input_description": description,
            "answer": final_answer,
            "apresentacao_registro": apresentacao_registro,
            "descricao_medicamentos": descricao_medicamentos,
            "explicability": think_string,
            "metrics": metrics
        }
        
        logging.info(f"--- Processamento finalizado. Resposta Final: {final_answer} ---")
        return result, cleaned_description, pruned_candidates


    def process_message(self, message):
        """
        Função principal para executar o pipeline de inferência em um conjunto de descrições.
        """
        try:
            description = message.get("descricao_produto")

            result = self.process_description(description)

            # Verificação de segurança
            if not result or not isinstance(result, tuple) or len(result) != 3:
                self.logger.warning(f"Resultado inesperado de process_description: {result}")
                return None

            result_dict, cleaned_description, pruned_candidates = result

            if not isinstance(result_dict, dict):
                self.logger.warning(f"Primeiro elemento retornado não é dict: {result_dict}")
                return None

            grupo_classificado = result_dict.get("answer")
            apresentacao_registro = result_dict.get("apresentacao_registro")
            descricao_medicamentos = result_dict.get("descricao_medicamentos")

            # Converte "0" ou string vazia para None, e valores válidos para inteiro
            if grupo_classificado == "0" or grupo_classificado == "" or grupo_classificado is None:
                grupo_classificado = None
            else:
                try:
                    grupo_classificado = int(grupo_classificado)
                except (ValueError, TypeError):
                    self.logger.warning(f"grupo_classificado inválido: {grupo_classificado}. Definindo como None.")
                    grupo_classificado = None
            
            self.logger.info(f"grupo_classificado: {grupo_classificado}")

            id_item_nfe = message.get("id_item_nfe")
            self.logger.info(f"id_item_nfe: {id_item_nfe}")
            
            # Extrai o id_nfe da mensagem (necessário para a constraint de chave estrangeira)
            id_nfe = message.get("id_nfe")
            self.logger.info(f"id_nfe: {id_nfe}")
            
            # Extrai o id_item da mensagem (necessário como identificador de negócio)
            id_item = message.get("id_item")
            self.logger.info(f"id_item: {id_item}")

            # Monta o JSON desejado com todos os campos necessários
            item_dict = {

                "grupo_bp":{
                    "nome": descricao_medicamentos,
                    "numero_grupo": grupo_classificado,
                    "id_metodo_de_agrupamento_bp": 1
                },
                "item_nfe_grupo_bp":{
                    "id_item_nfe": id_item_nfe
                },
            }
            

            self.logger.info("JSON final: {item_dict}")
            
            return item_dict
        
        except Exception as e:
            self.logger.error(f"Ocorreu um erro crítico durante a execução do pipeline: {e}")
            raise

    def shutdown(self):
        """Fecha todas as conexões de forma limpa ao desligar."""
        self.logger.info("Iniciando shutdown do GrouperMedicamentos...")
        
        # Fecha conexões do NER processor se existir
        if hasattr(self, 'ner_processor') and hasattr(self.ner_processor, 'db_engine'):
            try:
                self.logger.info("Desligando o pool de conexões do NER processor...")
                self.ner_processor.db_engine.dispose()
            except Exception as e:
                self.logger.error(f"Erro ao desligar pool de conexões do NER: {e}")
        
        # Fecha conexões da fila
        try:
            if hasattr(self, 'queue_manager'):
                self.queue_manager.close_connection()
        except Exception as e:
            self.logger.error(f"Erro ao fechar conexões da fila: {e}")
        
        self.logger.info("Shutdown do GrouperMedicamentos concluído.")

if __name__ == '__main__':
    grouper_medicamentos = GrouperMedicamentos()
    grouper_medicamentos.start()
    grouper_medicamentos.shutdown()

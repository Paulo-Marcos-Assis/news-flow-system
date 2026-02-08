import sys
import os
from urllib.parse import urlparse  # <--- NOVA IMPORTAÇÃO NECESSÁRIA

# Import the team's base class
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.exceptions.fail_queue_exception import FailQueueException

# Import your AI modules
from classifier.classifier import FraudClassifier
from extractor.feature_extractor import FeatureExtractor

class ProcessorNoticias(BasicProducerConsumerService):
    
    def __init__(self):
        """
        This runs ONCE when the container starts.
        """
        super().__init__()
        self.logger.info("--- STARTING NEWS PROCESSOR ---")
        
        self.logger.info("Loading Classifier (BERT + SVM)...")
        self.classifier = FraudClassifier()
        
        self.logger.info("Loading Feature Extractor (LLM)...")
        self.extractor = FeatureExtractor()
        
        self.logger.info("All AI Models loaded successfully. Waiting for news...")

    def process_message(self, record):
        """
        Runs for every news article.
        """
        
        # 1. Get the text
        news_text = record.get("text") or record.get("conteudo") or record.get("body")
        
        if not news_text:
            raise FailQueueException("O registro não possui campo de texto válido para análise.")

        # 2. Step 1: CLASSIFICATION
        try:
            prediction = self.classifier.predict(news_text)
        except Exception as e:
            self.logger.error(f"Erro durante a classificação: {e}")
            raise FailQueueException(f"Erro interno no classificador: {e}")

        # 3. Decision Logic (Filter Irrelevant News)
        if prediction == 0:
            self.logger.info(f"ID {record.get('_id', 'unknown')}: Classificado como irrelevante. Ignorando.")
            return None 
        
        # 4. Step 2: EXTRACTION (Only happens if Fraud == 1)
        self.logger.info("Possível fraude detectada! Iniciando extração de entidades com LLM...")
        
        try:
            extracted_data = self.extractor.extract(news_text)
        except Exception as e:
             self.logger.error(f"Erro durante a extração com LLM: {e}")
             raise FailQueueException(f"Erro na extração de features: {e}")

        # 5. Prepare the Output (SEPARATED ENTITIES + CONDITIONAL KEYS)

        # --- A. Parse Values from Extractor ---
        raw_municipio = extracted_data.get('municipio', [])
        city_name = raw_municipio[0] if raw_municipio and isinstance(raw_municipio, list) else None
        
        raw_modalidade = extracted_data.get('modalidade', [])
        modality_name = raw_modalidade[0] if raw_modalidade and isinstance(raw_modalidade, list) else None
        
        raw_edital = extracted_data.get('edital', [])
        edital_val = raw_edital[0] if raw_edital and isinstance(raw_edital, list) else None
        
        raw_objeto = extracted_data.get('objeto', [])
        objeto_val = raw_objeto[0] if raw_objeto and isinstance(raw_objeto, list) else None

        # --- B. PORTAL NAME LOGIC (GENERIC FALLBACK) ---
        # Tenta pegar o portal que veio do Collector
        portal_name = record.get('portal') or record.get('nome_portal')

        # Se não veio o nome (caso dos JSONs antigos), extrai automaticamente da URL
        if not portal_name and record.get('url'):
            try:
                # Extrai o domínio (ex: www.nsctotal.com.br)
                domain = urlparse(record.get('url')).netloc  
                
                # Remove o 'www.' se existir
                if domain.startswith('www.'):
                    domain = domain[4:] 
                
                # Pega a primeira parte antes do ponto (ex: 'nsctotal')
                # Isso funciona para 'g1.globo.com' -> 'g1', 'ndmais.com.br' -> 'ndmais'
                portal_name = domain.split('.')[0] 
            except Exception:
                portal_name = None # Se falhar, deixa None (o DB aceita ou coloca null)

        # --- C. Build the 'noticia' Dictionary (Core Table Data) ---
        noticia_data = {
            "link": record.get('url'),
            "titulo": record.get('title'),
            "data_publicacao": record.get('date_publication'),
            
            "nome_portal": portal_name,  # <--- CAMPO CORRIGIDO COM A LÓGICA
            
            "numero_edital": edital_val,
            "objeto": objeto_val,
            
            "texto": news_text,
            
            # Prioridade: Chamada real (Collector) -> Backup: Primeiros 200 chars
            "chamada": record.get('chamada') or (news_text[:200] if news_text else None)
        }

        # --- D. Build the Root Result (The Envelope) ---
        result = {
            "raw_data_id": record.get("raw_data_id") or record.get("_id"),
            "data_source": "noticias",
            "noticia": noticia_data
        }

        # --- E. Conditional Foreign Keys ---
        if city_name:
            result['municipio'] = {
                "nome_municipio": city_name,
                "sigla_uf": "SC",
                "nome_uf": "Santa Catarina"
            }

        if modality_name:
            result['modalidade_licitacao'] = {
                "descricao": modality_name
            }

        self.logger.info("Processamento finalizado. Objeto estruturado criado.")
        return result

if __name__ == '__main__':
    processor = ProcessorNoticias()
    processor.start()
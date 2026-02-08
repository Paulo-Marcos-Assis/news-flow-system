import importlib
import os
from service_essentials.utils.logger import Logger
from extractors.base_extractor import BaseExtractor
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService

class ProcessorNotas(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        # 1. Otimização: Carrega os extratores UMA VEZ na inicialização
        logger.info("Carregando extratores...")
        self.extractors_nfe, self.extractors_item = self.load_extractors()
        logger.info(f"Carregados {len(self.extractors_nfe)} extratores de NFE.")
        logger.info(f"Carregados {len(self.extractors_item)} extratores de Item.")
        
    def process_message(self, record):
        # Os extratores já estão carregados em 'self.'
        structured_nfe = {}
        structured_items = []

        itens = record.get("item_nfe", [])
        itens = record.get("item_nfe", [])
        structured_items = [{} for _ in itens]

        raw_data_id = record["raw_data_id"]
        data_source = record["data_source"]

        ncm_valid = False

        # 2. Mudança de segurança: Usar .pop() é mais seguro que 'del'
        # Isso evita que o código quebre se a chave já foi removida.
        record.pop("NFE_ID", None) 

        # 3. Loop separado para extratores de NFE (Cabeçalho)
        for field_name, extractor in self.extractors_nfe.items():
            try:
                # Não precisamos mais verificar o 'scope'
                structured_nfe[field_name] = to_lower_if_str(extractor.extract(record))
            except Exception as e:
                logger.error(f"Erro ao extrair {field_name} (NFE): {e}")
                structured_nfe[field_name] = ""

        # 4. Loop separado para extratores de ITEM
        for field_name, extractor in self.extractors_item.items():
            try:
                # Não precisamos mais verificar o 'scope'
                for idx, item in enumerate(itens):
                    # Filtrando apenas medicamentos nesse momento
                    if field_name.lower() == "ncm_produto" and (item.get("NCM_PRODUTO", "").startswith("3003") or item.get("NCM_PRODUTO", "").startswith("3004") or item.get("NCM_PRODUTO", "").startswith("3005")):
                        ncm_valid = True  # Set the flag to True if a valid NCM is found

                    if field_name != "descricao_produto":
                        structured_items[idx][field_name] = to_lower_if_str(extractor.extract(item))
                    else:
                        structured_items[idx][field_name] = extractor.extract(item)    
            except Exception as e:
                logger.error(f"Erro ao extrair {field_name} (Item): {e}")
                for idx in range(len(structured_items)):
                    structured_items[idx][field_name] = ""
        if not ncm_valid:
            #logger.warning("Nenhum item com NCM iniciado por '3004' encontrado. A nota será descartada.")
            return None

        return {
            "nfe": structured_nfe,
            "item_nfe": structured_items,
            "raw_data_id": raw_data_id,
            "data_source": data_source
        }


    def load_extractors(self):
        base_path = "extractors"
        # 5. Define as subpastas que queremos ler
        subdirs = ["nfe", "item_nfe"] 
        
        all_extractors = {
            "nfe": {},
            "item_nfe": {}
        }

        for subdir in subdirs:
            path = os.path.join(base_path, subdir)
            
            if not os.path.isdir(path):
                logger.warning(f"Diretório de extratores não encontrado: {path}")
                continue # Pula para a próxima subpasta

            for file in os.listdir(path):
                if file.endswith(".py") and file != "__init__.py":
    
                    module_name = f"extractors.{subdir}.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                    except ImportError as e:
                        logger.error(f"Falha ao importar o módulo {module_name}: {e}")
                        continue # Pula este arquivo

                    for attr in dir(module):
                        cls = getattr(module, attr)
                        if isinstance(cls, type) and issubclass(cls, BaseExtractor) and cls is not BaseExtractor:
                            # 7. Adiciona o extrator ao dicionário correto ('nfe' ou 'item_nfe')
                            all_extractors[subdir][cls.field_name] = cls(logger)
                            
        # 8. Retorna os dois dicionários separados
        return all_extractors["nfe"], all_extractors["item_nfe"]
        
def to_lower_if_str(value):
    return value.lower() if isinstance(value, str) else value
    
if __name__ == '__main__':
    logger = Logger(log_to_console=True)
    
    processor = ProcessorNotas()
    processor.start()
import importlib
import os

from service_essentials.utils.logger import Logger
from service_essentials.exceptions.fail_queue_exception import FailQueueException
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from verifiers.base_verifier import BaseVerifier


class VerifierNotas(BasicProducerConsumerService):
    def __init__(self):
        super().__init__() 
        # 1. Otimização: Carrega os verifiers UMA VEZ na inicialização
        logger.info("Carregando verifiers...")
        self.verifiers_nfe, self.verifiers_item = self.load_verifiers()
        logger.info(f"Carregados {len(self.verifiers_nfe)} verifiers de NFE.")
        logger.info(f"Carregados {len(self.verifiers_item)} verifiers de Item.")

    def process_message(self, record):
        failures = {}
        nfe_data = record.get("nfe", {})
        item_data = record.get("item_nfe", [])

        # 3. Loop separado para verifiers de NFE (Cabeçalho)
        for field_name, verifier in self.verifiers_nfe.items():
            try:
                # Não precisamos mais verificar o 'scope'
                value = nfe_data.get(field_name, None)
                verified, msg = verifier.verify(value)
                if not verified:
                    logger.warning(f"Falha ao verificar NFE {field_name}: {msg}")
                    failures[field_name] = msg
            except Exception as e:
                # Captura erro no próprio verifier
                logger.error(f"Erro ao executar verifier NFE {field_name}: {e}")
                failures[field_name] = f"Erro interno de verificação: {e}"

        # 4. Loop separado para verifiers de ITEM
        for field_name, verifier in self.verifiers_item.items():
            try:
                # Não precisamos mais verificar o 'scope'
                for idx, item in enumerate(item_data):
                    value = item.get(field_name, None)
                    verified, msg = verifier.verify(value)
                    if not verified:
                        logger.warning(f"Falha ao verificar {field_name} no item {idx}: {msg}")
                        failures[f"item_{idx}_{field_name}"] = msg
            except Exception as e:
                # Captura erro no próprio verifier
                logger.error(f"Erro ao executar verifier ITEM {field_name}: {e}")
                # Adiciona uma falha genérica para este campo de item
                failures[f"item_all_{field_name}"] = f"Erro interno de verificação em item: {e}"

        if failures:
            # qualquer falha → manda pra fila de erro
            logger.error(f"Registro falhou na verificação. Falhas: {failures}")
            raise FailQueueException(failures)

        logger.info("Verificação concluída com sucesso!")
        return record
    

    def load_verifiers(self):
        # 2. Reescrito para ler as subpastas 'nfe' e 'item_nfe'
        base_path = "verifiers"
        subdirs = ["nfe", "item_nfe"]
        
        all_verifiers = {
            "nfe": {},
            "item_nfe": {}
        }

        for subdir in subdirs:
            path = os.path.join(base_path, subdir)
            
            if not os.path.isdir(path):
                logger.warning(f"Diretório de verifiers não encontrado: {path}")
                continue

            for file in os.listdir(path):
                if file.endswith(".py") and file != "__init__.py":
                    # Monta o nome do módulo (ex: 'verifiers.nfe.meu_verifier')
                    module_name = f"verifiers.{subdir}.{file[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                    except ImportError as e:
                        # Adicionado para capturar o erro de import do BaseVerifier
                        logger.error(f"Falha ao importar o módulo {module_name}: {e}")
                        continue 

                    for attr in dir(module):
                        cls = getattr(module, attr)
                        if isinstance(cls, type) and issubclass(cls, BaseVerifier) and cls is not BaseVerifier:
                            # Adiciona o verifier ao dicionário correto
                            all_verifiers[subdir][cls.field_name] = cls(logger)
                            
        return all_verifiers["nfe"], all_verifiers["item_nfe"]
        

if __name__ == '__main__':
    logger = Logger(log_to_console=True)

    processor = VerifierNotas()
    processor.start()
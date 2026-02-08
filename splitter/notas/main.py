import json
import os
from service_essentials.utils.logger import Logger

from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.mongodb_ingestor.mongo_ingestor import MongoDBIngestor

class SplitterNotas(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        self.mongo = MongoDBIngestor("notas")
        # Assumindo que o object_storage_manager está disponível na classe base

    def process_message(self, message):
        """
        Espera receber uma mensagem "claim check" do MinIO.
        Baixa o arquivo JSON, itera sobre a lista de notas dentro dele,
        e envia cada nota individualmente para a próxima fila.
        """
        local_filename = None
        try:
            # 1. Extrai as informações da mensagem "claim check"
            bucket = message["bucket"]
            data_file = message["data_file"]
            local_filename = data_file # O nome do arquivo local será o mesmo do remoto
            
            logger.info(f"Recebido 'claim check'. Baixando arquivo '{data_file}' do bucket '{bucket}'...")

            # 2. Baixa o arquivo do MinIO
            self.object_storage_manager.download_file(bucket, data_file, local_filename)
            logger.info("Download concluído.")

            # 3. Abre o arquivo JSON baixado e processa o conteúdo
            with open(local_filename, 'r', encoding='utf-8') as f:
                lista_de_notas = json.load(f)

                if not isinstance(lista_de_notas, list):
                    logger.error(f"Arquivo '{local_filename}' não contém uma lista de notas.")
                    return None

                logger.info(f"Processando e dividindo {len(lista_de_notas)} notas do arquivo.")
                for idx, nota_dict in enumerate(lista_de_notas):
                    universal_id = self.mongo.ingest_json(nota_dict)
                    nota_dict["raw_data_id"] = str(universal_id)
                    nota_dict["data_source"] = "NFE"
                    nota_json = json.dumps(nota_dict, ensure_ascii=False)
                    self.queue_manager.publish_message(self.output_queue, nota_json)
            
            logger.info("Todas as notas do arquivo foram publicadas individualmente.")

        except Exception as e:
            logger.error(f"Erro inesperado no SplitterNotas: {e}", exc_info=True)
        finally:
            # 4. Bloco de limpeza: garante que os arquivos temporários sejam apagados
            if local_filename and os.path.exists(local_filename):
                logger.info(f"Apagando arquivo local temporário: {local_filename}")
                os.remove(local_filename)
            # Opcional: apagar o arquivo do MinIO depois de processado
            if 'bucket' in locals() and 'data_file' in locals():
                 logger.info(f"Apagando arquivo '{data_file}' do bucket '{bucket}' no MinIO.")
                 self.object_storage_manager.delete_file(bucket, data_file)

        return None # Retorna None pois a publicação é explícita

if __name__ == '__main__':
    logger = Logger(log_to_console=True)
    processor = SplitterNotas()
    processor.start()


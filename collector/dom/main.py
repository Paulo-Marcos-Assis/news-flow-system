import os
import requests
import json
import zipfile
import shutil
import time
from datetime import datetime


from service_essentials.basic_service.cached_collector_service import CachedCollectorService


class CollectorDom(CachedCollectorService):
    def __init__(self):
        super().__init__(data_source="dom")

    def collect_data(self, message):
        """
        Collect DOM licitações data based on the incoming message.
        
        Args:
            message: Message containing api_url, date, and package_name
        
        Returns:
            List of licitações records
        """
        api_url = message["api_url"]
        date = message["date"]
        package_name = message["package_name"]
        
        dados_base = self.realizar_requisicao_base(api_url + package_name)
        registros_data_especifica = self.filtrar_registros_para_data(dados_base, date)
        arquivos_baixados = self.realizar_download_arquivos_zip(registros_data_especifica)
        diretorio_temp = self.extrair_arquivos_zip(arquivos_baixados)
        registros = self.ler_jsons_e_listar_licitacoes(diretorio_temp)
        
        # Clean up temporary files
        self.apagar_arquivos_temp(arquivos_baixados)
        self.apagar_diretorio_temp(diretorio_temp)
        
        return registros

    def realizar_requisicao_base(self, url):
        retry_time = 10
        data = None
        for i in range(10):
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                if not data.get("success"):
                    raise ValueError("API retornou sucesso = false")
                break
            except Exception as e:
                self.logger.error(f"Erro ao tentar acessar url ({url}): {str(e)}")
                self.logger.error(f"Tentando novamente em {retry_time} segundos - #{i}")
                time.sleep(retry_time)
        
        if data is None:
            raise RuntimeError(f"Failed to fetch data from {url} after 10 retries")
        
        return data["result"]

    def filtrar_registros_para_data(self, data, date):
        date_str = datetime.strptime(date, "%d/%m/%Y").strftime("%d/%m/%Y")
        self.logger.info(f"Processando todas as publicações de {date}...")
        resources = data.get("resources", [])
        return [
            resource for resource in resources
            if resource.get("format") == "ZIP" and date_str in resource.get("name", "")
        ]

    def realizar_download_arquivos_zip(self, registros):
        os.makedirs("downloads", exist_ok=True)
        arquivos_baixados = []
        for registro in registros:
            file_url = registro.get("url")
            file_name = os.path.basename(file_url)
            file_path = os.path.join("downloads", file_name)
            response = requests.get(file_url)
            response.raise_for_status()
            with open(file_path, "wb") as file:
                file.write(response.content)
            arquivos_baixados.append(file_path)
        return arquivos_baixados

    def extrair_arquivos_zip(self, arquivos_baixados):
        temp_dir = "temp_extracted"
        os.makedirs(temp_dir, exist_ok=True)
        for arquivo in arquivos_baixados:
            with zipfile.ZipFile(arquivo, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        return temp_dir

    def ler_jsons_e_listar_licitacoes(self, diretorio_temp):
        licitacoes = []
        for root, _, files in os.walk(diretorio_temp):
            for file in files:
                if file.endswith(".json"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as json_file:
                        try:
                            data = json.load(json_file)
                            if isinstance(data, dict) and "autopublicacoes" in data:
                                autopublicacoes = data["autopublicacoes"]
                                if isinstance(autopublicacoes, list):
                                    licitacoes.extend(
                                        item for item in autopublicacoes if isinstance(item, dict) and item.get("categoria") == "Licitações"
                                    )
                        except json.JSONDecodeError as e:
                            print(f"Erro ao decodificar JSON em {file}: {e}")
        return licitacoes

    def apagar_arquivos_temp(self, arquivos):
        if isinstance(arquivos, str):
            arquivos = [arquivos]
        for arquivo in arquivos:
            os.remove(arquivo)

    def apagar_diretorio_temp(self, diretorio_temp):
        if os.path.exists(diretorio_temp):
            shutil.rmtree(diretorio_temp)


if __name__ == '__main__':
    processor = CollectorDom()
    processor.start()
    

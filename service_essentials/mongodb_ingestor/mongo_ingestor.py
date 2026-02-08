from venv import logger
from pymongo import MongoClient
import os

from service_essentials.utils.logger import Logger

entidades_dict = {
    "dom_dict": {
        "attribute": "categoria",
        "Licitações": ".licitacoes",
        "Edital": ".edital"
    },
    "notas_dict": {
        "attribute": None
    },
    "ESFINGE_dict": {
        "attribute": None
    },
    "pncp_dict": {
        "attribute": "entity_type",
        "contratacao": ".contratacao",
        "contrato": ".contrato",
        "instrumento_cobranca": ".instrumento_cobranca"
    },
    "EPUBLICA_dict":{
        "attribute": None
    }

}

class MongoDBIngestor:
    def __init__(self, font):
        self.logger = Logger(None, log_to_console=True)
        self.__username = os.getenv("USERNAME_MONGODB")
        self.__password = os.getenv("SENHA_MONGODB")
        self.__authdb = os.getenv("DATABASE_AUTENTICACAO_MONGODB")
        self.__host = os.getenv("HOST_MONGODB")
        self.__port = os.getenv("PORT_MONGODB")
        self.__database = os.getenv("DATABASE_MONGODB")
        self.__uri = f"mongodb://{self.__username}:{self.__password}@{self.__host}:{self.__port}/?authSource={self.__authdb}"
        self.__client = MongoClient(self.__uri)
        self.__db = self.__client[self.__database]
        self.__font = font

    def check_entity(self, json_data):
        font_dict = entidades_dict[self.__font + "_dict"]
        attribute = font_dict["attribute"] #gets the font's specific identifying attribute (DOM -> categoria)

        if attribute: #if identifying attribute exists
            entity = json_data[attribute] #saves the value of attribute (categoria -> Licitações)
            if entity in font_dict:
                return self.__font + font_dict[entity] #gets the value of entity in the font's dict (Licitações -> .licitacoes)
            
        return self.__font

    def ingest_json(self, json_data):
        if os.getenv("USE_MONGODB", "off").lower() == "on":
            collection_name = self.check_entity(json_data)

            self.__collection = self.__db[collection_name]
            try:
                copied_json_data = json_data.copy() #needed because insert_one adds ObjectID to json_data & messes up other processes
                self.__collection.insert_one(copied_json_data)
                universal_id = str(copied_json_data["_id"])
                json_data["universal_id"] = universal_id
                return universal_id
            except Exception as e:
                self.logger.error(f"MongoDB exception: {e}")
        else:
            return -1
            self.logger.info("MongoDB is not being used")
import os
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
from bson import ObjectId
from service_essentials.document_storage_manager.document_storage_manager import DocumentStorageManager
from service_essentials.utils.logger import Logger


class MongoDBManager(DocumentStorageManager):
    """
    Implementation of the Document Storage Manager for MongoDB.
    """
    def __init__(self):
        self.client = None
        self.db = None
        self.logger = Logger(None, log_to_console=True)
        self.connect()

    def connect(self, host: str = None, port: int = None, username: str = None, 
                password: str = None, database: str = None, **kwargs):
        """
        Connect to MongoDB server using environment variables or provided parameters.
        """
        try:
            # Retrieve connection parameters from environment variables or use provided values
            username = os.getenv("USERNAME_MONGODB", "admin")
            password = os.getenv("SENHA_MONGODB", "admin")
            host = os.getenv("HOST_MONGODB", "localhost")
            port = int(os.getenv("PORT_MONGODB", "27017"))
            database = os.getenv("DATABASE_MONGODB", "local")
            auth_db = os.getenv("DATABASE_AUTENTICACAO_MONGODB", "admin")

            # Build MongoDB URI
            uri = f"mongodb://{username}:{password}@{host}:{port}/?authSource={auth_db}"
            
            self.client = MongoClient(uri)
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[database]
        except ConnectionFailure as e:
            self.logger.error(f"Falha crítica ao conectar com MongoDB em {host}:{port}: {e}")
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao conectar com MongoDB: {e}")
            raise ConnectionError(f"Unexpected error connecting to MongoDB: {e}")

    def insert_document(self, collection: str, document: Dict[str, Any]) -> str:
        """
        Insert a document into a collection.
        """
        try:
            coll = self.db[collection]
            result = coll.insert_one(document)
            return str(result.inserted_id)
        except PyMongoError as e:
            self.logger.error(f"Erro ao inserir documento na coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to insert document: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao inserir documento no MongoDB: {e}")
            raise

    def insert_many_documents(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents into a collection.
        """
        try:
            coll = self.db[collection]
            result = coll.insert_many(documents)
            inserted_ids = [str(id) for id in result.inserted_ids]
            return inserted_ids
        except PyMongoError as e:
            self.logger.error(f"Erro ao inserir {len(documents)} documentos na coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to insert documents: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao inserir documentos em lote no MongoDB: {e}")
            raise

    def find_document(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document in a collection.
        """
        try:
            coll = self.db[collection]
            # Convert string _id to ObjectId if present
            if '_id' in query and isinstance(query['_id'], str):
                try:
                    query = query.copy()
                    query['_id'] = ObjectId(query['_id'])
                except Exception as e:
                    self.logger.warning(f"Invalid ObjectId format: {query['_id']}, error: {e}")
                    return None
            
            document = coll.find_one(query)
            if document:
                # Convert ObjectId to string for JSON serialization
                document['_id'] = str(document['_id'])
            return document
        except PyMongoError as e:
            self.logger.error(f"Erro ao buscar documento na coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to find document: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao buscar documento no MongoDB: {e}")
            raise

    def find_documents(self, collection: str, query: Dict[str, Any], limit: int = 0) -> List[Dict[str, Any]]:
        """
        Find multiple documents in a collection.
        """
        try:
            coll = self.db[collection]
            # Convert string _id to ObjectId if present
            if '_id' in query and isinstance(query['_id'], str):
                try:
                    query = query.copy()
                    query['_id'] = ObjectId(query['_id'])
                except Exception as e:
                    self.logger.warning(f"Invalid ObjectId format: {query['_id']}, error: {e}")
                    return []
            
            cursor = coll.find(query)
            if limit > 0:
                cursor = cursor.limit(limit)
            
            documents = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                documents.append(doc)
            
            return documents
        except PyMongoError as e:
            self.logger.error(f"Erro ao buscar documentos na coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to find documents: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao buscar documentos no MongoDB: {e}")
            raise

    def update_document(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        Update a single document in a collection.
        """
        try:
            coll = self.db[collection]
            # Convert string _id to ObjectId if present in query
            if '_id' in query and isinstance(query['_id'], str):
                try:
                    query = query.copy()
                    query['_id'] = ObjectId(query['_id'])
                except Exception as e:
                    self.logger.warning(f"Invalid ObjectId format: {query['_id']}, error: {e}")
                    return 0
            
            # Ensure update operations use proper MongoDB operators
            if not any(key.startswith('$') for key in update.keys()):
                update = {"$set": update}
            
            result = coll.update_one(query, update)
            if result.matched_count == 0:
                self.logger.warning(f"Nenhum documento encontrado para atualizar na coleção '{collection}' com query: {query}")
            return result.modified_count
        except PyMongoError as e:
            self.logger.error(f"Erro ao atualizar documento na coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to update document: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao atualizar documento no MongoDB: {e}")
            raise

    def update_many_documents(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        Update multiple documents in a collection.
        """
        try:
            coll = self.db[collection]
            # Convert string _id to ObjectId if present in query
            if '_id' in query and isinstance(query['_id'], str):
                try:
                    query = query.copy()
                    query['_id'] = ObjectId(query['_id'])
                except Exception as e:
                    self.logger.warning(f"Invalid ObjectId format: {query['_id']}, error: {e}")
                    return 0
            
            # Ensure update operations use proper MongoDB operators
            if not any(key.startswith('$') for key in update.keys()):
                update = {"$set": update}
            
            result = coll.update_many(query, update)
            if result.matched_count == 0:
                self.logger.warning(f"Nenhum documento encontrado para atualizar na coleção '{collection}' com query: {query}")
            return result.modified_count
        except PyMongoError as e:
            self.logger.error(f"Erro ao atualizar documentos na coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to update documents: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao atualizar documentos no MongoDB: {e}")
            raise

    def delete_document(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Delete a single document from a collection.
        """
        try:
            coll = self.db[collection]
            # Convert string _id to ObjectId if present
            if '_id' in query and isinstance(query['_id'], str):
                try:
                    query = query.copy()
                    query['_id'] = ObjectId(query['_id'])
                except Exception as e:
                    self.logger.warning(f"Invalid ObjectId format: {query['_id']}, error: {e}")
                    return 0
            
            result = coll.delete_one(query)
            if result.deleted_count == 0:
                self.logger.warning(f"Nenhum documento encontrado para deletar na coleção '{collection}' com query: {query}")
            return result.deleted_count
        except PyMongoError as e:
            self.logger.error(f"Erro ao deletar documento da coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to delete document: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao deletar documento no MongoDB: {e}")
            raise

    def delete_many_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents from a collection.
        """
        try:
            coll = self.db[collection]
            # Convert string _id to ObjectId if present
            if '_id' in query and isinstance(query['_id'], str):
                try:
                    query = query.copy()
                    query['_id'] = ObjectId(query['_id'])
                except Exception as e:
                    self.logger.warning(f"Invalid ObjectId format: {query['_id']}, error: {e}")
                    return 0
            
            result = coll.delete_many(query)
            if result.deleted_count == 0:
                self.logger.warning(f"Nenhum documento encontrado para deletar na coleção '{collection}' com query: {query}")
            return result.deleted_count
        except PyMongoError as e:
            self.logger.error(f"Erro ao deletar documentos da coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to delete documents: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao deletar documentos no MongoDB: {e}")
            raise

    def count_documents(self, collection: str, query: Dict[str, Any] = None) -> int:
        """
        Count documents in a collection.
        """
        try:
            coll = self.db[collection]
            query = query or {}
            count = coll.count_documents(query)
            return count
        except PyMongoError as e:
            self.logger.error(f"Erro ao contar documentos na coleção '{collection}' do MongoDB: {e}")
            raise RuntimeError(f"Failed to count documents: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao contar documentos no MongoDB: {e}")
            raise

    def collection_exists(self, collection: str) -> bool:
        """
        Check if a collection exists.
        """
        try:
            collection_names = self.db.list_collection_names()
            exists = collection in collection_names
            return exists
        except PyMongoError as e:
            self.logger.error(f"Erro ao verificar existência da coleção '{collection}' no MongoDB: {e}")
            raise RuntimeError(f"Failed to check collection existence: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao verificar existência de coleção no MongoDB: {e}")
            raise

    def list_collections(self) -> List[str]:
        """
        List all collection names in the database.
        """
        try:
            collection_names = self.db.list_collection_names()
            return collection_names
        except PyMongoError as e:
            self.logger.error(f"Erro ao listar coleções do MongoDB: {e}")
            raise RuntimeError(f"Failed to list collections: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao listar coleções no MongoDB: {e}")
            raise

    def create_index(self, collection: str, keys: List[tuple], unique: bool = False, name: str = None) -> str:
        """
        Create an index on a collection.
        """
        try:
            coll = self.db[collection]
            index_name = coll.create_index(keys, unique=unique, name=name)
            self.logger.info(f"Created index '{index_name}' on collection '{collection}' with keys: {keys}")
            return index_name
        except PyMongoError as e:
            self.logger.error(f"Erro ao criar índice na coleção '{collection}': {e}")
            raise RuntimeError(f"Failed to create index: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao criar índice: {e}")
            raise

    def ensure_indexes(self, collection: str, indexes: List[Dict[str, Any]]) -> List[str]:
        """
        Ensure multiple indexes exist on a collection (creates if missing).
        """
        try:
            coll = self.db[collection]
            created_indexes = []
            
            for index_spec in indexes:
                keys = index_spec.get('keys', [])
                unique = index_spec.get('unique', False)
                name = index_spec.get('name', None)
                
                if not keys:
                    self.logger.warning(f"Skipping index with no keys in collection '{collection}'")
                    continue
                
                try:
                    index_name = coll.create_index(keys, unique=unique, name=name, background=True)
                    created_indexes.append(index_name)
                    self.logger.info(f"Ensured index '{index_name}' on '{collection}'")
                except PyMongoError as e:
                    # Index might already exist, which is fine
                    if "already exists" in str(e).lower() or "index with name" in str(e).lower():
                        self.logger.debug(f"Index already exists on '{collection}': {keys}")
                    else:
                        self.logger.warning(f"Could not create index on '{collection}': {e}")
            
            return created_indexes
        except PyMongoError as e:
            self.logger.error(f"Erro ao garantir índices na coleção '{collection}': {e}")
            raise RuntimeError(f"Failed to ensure indexes: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao garantir índices: {e}")
            raise

    def close_connection(self):
        """
        Close the connection to MongoDB.
        """
        if self.client:
            self.client.close()

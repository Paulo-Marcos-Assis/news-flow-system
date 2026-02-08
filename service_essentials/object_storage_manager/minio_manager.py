import os
from minio import Minio
from minio.error import S3Error
from service_essentials.object_storage_manager.object_storage_manager import ObjectStorageManager
from service_essentials.utils.logger import Logger 


class MinIOManager(ObjectStorageManager):
    """
    Implementation of the Object Storage Manager for MinIO.
    Supports both private and public MinIO instances with separate environment variables.
    """
    def __init__(self, storage_type: str = "private"):
        """
        Initialize MinIO Manager with specified storage type.
        
        :param storage_type: Type of storage - "private" or "public" (default: "private")
        """
        self.client = None
        self.storage_type = storage_type.lower()
        self.logger = Logger(None, log_to_console=True)
        
        if self.storage_type not in ["private", "public"]:
            raise ValueError(f"Invalid storage_type: {storage_type}. Must be 'private' or 'public'")
        
        self.connect()

    def connect(self, endpoint: str = None, access_key: str = None, secret_key: str = None, secure: bool = None):
        try:
            # Determine environment variable prefix based on storage type
            prefix = "PUBLIC_" if self.storage_type == "public" else "PRIVATE_"
            
            # Retrieve address and port from environment variables or use defaults
            address = os.getenv(f"{prefix}OBJECT_STORAGE_ADDRESS", "localhost")
            port = os.getenv(f"{prefix}OBJECT_STORAGE_PORT", "9000")

            endpoint = endpoint or f"{address}:{port}"

            access_key = access_key or os.getenv(f"{prefix}OBJECT_STORAGE_ACCESS_KEY", "minioadmin")
            secret_key = secret_key or os.getenv(f"{prefix}OBJECT_STORAGE_SECRET_KEY", "minioadmin")
            
            # Secure defaults to False for private, True for public
            default_secure = "true" if self.storage_type == "public" else "false"
            secure = secure if secure is not None else os.getenv(f"{prefix}MINIO_SECURE", default_secure).lower() == "true"

            self.client = Minio(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
            self.logger.info(f"Conectado ao MinIO {self.storage_type} em {endpoint}")
        except Exception as e:
            self.logger.error(f"Falha crítica ao conectar com MinIO {self.storage_type} em {endpoint}: {e}")
            raise ConnectionError(f"Failed to connect to MinIO {self.storage_type}: {e}")

    def bucket_exists(self, bucket_name):
        buckets = self.client.list_buckets()
        return any(b.name == bucket_name for b in buckets)

    def upload_file(self, bucket_name: str, object_name: str, file_path: str):
        try:
            # Check if the bucket exists, and create it if not
            if not self.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name=bucket_name)
                #print(f"Bucket {bucket_name} created.")

            self.client.fput_object(bucket_name=bucket_name, object_name=object_name, file_path=file_path)
            self.logger.info(f"File {file_path} uploaded to bucket {bucket_name} as {object_name}.")
        except S3Error as e:
            self.logger.error(f"Erro ao fazer upload do arquivo '{file_path}' para MinIO bucket '{bucket_name}' como '{object_name}': {e}")
            raise RuntimeError(f"Failed to upload file to MinIO: {e}")
        except FileNotFoundError as e:
            self.logger.error(f"Arquivo '{file_path}' não encontrado para upload no MinIO: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro inesperado ao fazer upload para MinIO: {e}")
            raise

    def download_file(self, bucket_name: str, object_name: str, file_path: str):
        try:
            # CORREÇÃO: Adicionado nomes aos argumentos
            self.client.fget_object(
                bucket_name=bucket_name, 
                object_name=object_name, 
                file_path=file_path
            )
            self.logger.info(f"File {object_name} downloaded from bucket {bucket_name} to {file_path}.")
        except S3Error as e:
            if e.code == 'NoSuchKey':
                self.logger.error(f"Arquivo '{object_name}' não encontrado no bucket '{bucket_name}' do MinIO")
            elif e.code == 'NoSuchBucket':
                self.logger.error(f"Bucket '{bucket_name}' não existe no MinIO")
            else:
                self.logger.error(f"Erro ao fazer download do arquivo '{object_name}' do bucket '{bucket_name}' para '{file_path}': {e}")
            raise RuntimeError(f"Failed to download file from MinIO: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao fazer download do MinIO: {e}")
            raise

    def list_files(self, bucket_name: str):
        try:
            objects = self.client.list_objects(bucket_name=bucket_name)
            return objects
        except S3Error as e:
            if e.code == 'NoSuchBucket':
                self.logger.error(f"Bucket '{bucket_name}' não existe no MinIO")
            else:
                self.logger.error(f"Erro ao listar arquivos no bucket '{bucket_name}': {e}")
            raise RuntimeError(f"Failed to list files in bucket {bucket_name}: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao listar arquivos no MinIO: {e}")
            raise

    def delete_file(self, bucket_name: str, object_name: str):
        try:
            # CORREÇÃO: Adicionado nomes aos argumentos
            self.client.remove_object(
                bucket_name=bucket_name, 
                object_name=object_name
            )
            #print(f"File {object_name} deleted from bucket {bucket_name}.")
        except S3Error as e:
            if e.code == 'NoSuchKey':
                self.logger.warning(f"Tentativa de deletar arquivo '{object_name}' que não existe no bucket '{bucket_name}'")
            elif e.code == 'NoSuchBucket':
                self.logger.error(f"Bucket '{bucket_name}' não existe no MinIO")
            else:
                self.logger.error(f"Erro ao deletar arquivo '{object_name}' do bucket '{bucket_name}': {e}")
            raise RuntimeError(f"Failed to delete file from MinIO: {e}")
        except Exception as e:
            self.logger.error(f"Erro inesperado ao deletar arquivo do MinIO: {e}")
            raise


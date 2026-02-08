from abc import ABC, abstractmethod

class ObjectStorageManager(ABC):
    """
    Abstract class for a bucket file system.
    """

    @abstractmethod
    def connect(self, endpoint: str, access_key: str, secret_key: str, secure: bool = True):
        """
        Connect to the bucket file system server.

        :param endpoint: The server endpoint.
        :param access_key: Access key for authentication.
        :param secret_key: Secret key for authentication.
        :param secure: Use secure connection (HTTPS) if True.
        """
        pass

    @abstractmethod
    def upload_file(self, bucket_name: str, object_name: str, file_path: str):
        """
        Upload a file to the bucket.

        :param bucket_name: The name of the bucket.
        :param object_name: The object name in the bucket.
        :param file_path: Path to the file to upload.
        """
        pass

    @abstractmethod
    def download_file(self, bucket_name: str, object_name: str, file_path: str):
        """
        Download a file from the bucket.

        :param bucket_name: The name of the bucket.
        :param object_name: The object name in the bucket.
        :param file_path: Path to save the downloaded file.
        """
        pass

    @abstractmethod
    def list_files(self, bucket_name: str):
        """
        List files in a bucket.

        :param bucket_name: The name of the bucket.
        """
        pass

    @abstractmethod
    def delete_file(self, bucket_name: str, object_name: str):
        """
        Delete a file from the bucket.

        :param bucket_name: The name of the bucket.
        :param object_name: The object name to delete.
        """
        pass
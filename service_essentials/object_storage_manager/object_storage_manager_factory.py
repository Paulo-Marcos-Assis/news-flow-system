class ObjectStoreManagerFactory:
    """
    Factory class to instantiate the appropriate ObjectStoreManager based on environment variable.
    Supports private and public MinIO instances.
    """
    @staticmethod
    def get_object_store_manager(storage_type: str = "private"):
        """
        Get an object store manager instance.
        
        :param storage_type: Type of storage - "private" or "public" (default: "private")
        :return: ObjectStorageManager instance
        """
        import os
        object_store_manager_type = os.getenv("OBJECT_STORE_MANAGER", "minio").lower()
        if object_store_manager_type == "minio":
            from service_essentials.object_storage_manager.minio_manager import MinIOManager
            return MinIOManager(storage_type=storage_type)
        else:
            raise ValueError(f"Unsupported Object Store Manager: {object_store_manager_type}")
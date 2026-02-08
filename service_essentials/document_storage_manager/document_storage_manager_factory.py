class DocumentStorageManagerFactory:
    """
    Factory class to instantiate the appropriate DocumentStorageManager based on environment variable.
    """
    @staticmethod
    def get_document_storage_manager():
        import os
        document_storage_type = os.getenv("DOCUMENT_STORAGE_MANAGER", "mongodb").lower()
        
        if document_storage_type == "mongodb":
            from service_essentials.document_storage_manager.mongodb_manager import MongoDBManager
            return MongoDBManager()
        else:
            raise ValueError(f"Unsupported Document Storage Manager: {document_storage_type}")

class RelationalStorageManagerFactory:
    """
    Factory class to instantiate the appropriate RelationalStorageManager based on environment variable.
    """
    @staticmethod
    def get_relational_storage_manager():
        import os
        relational_storage_type = os.getenv("RELATIONAL_STORAGE", "postgresql").lower()
        if relational_storage_type == "postgresql":
            from service_essentials.relational_storage.postgresql_manager import PostgreSQLManager
            return PostgreSQLManager()
        else:
            raise ValueError(f"Unsupported Relational Storage Manager: {relational_storage_type}")

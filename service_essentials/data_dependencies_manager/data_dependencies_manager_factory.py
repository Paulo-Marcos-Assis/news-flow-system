class DataDependenciesManagerFactory:
    """
    Factory class to instantiate the appropriate DataDependenciesManager based on environment variable.
    """
    @staticmethod
    def get_data_dependencies_manager():
        import os
        dependencies_manager_type = os.getenv("DATA_DEPENDENCIES_MANAGER", "json").lower()
        
        if dependencies_manager_type == "json":
            from service_essentials.data_dependencies_manager.json_dependencies_manager import JsonDependenciesManager
            base_path = os.getenv("DATA_DEPENDENCIES_PATH", "data_dependencies")
            return JsonDependenciesManager(base_path=base_path)
        else:
            raise ValueError(f"Unsupported Data Dependencies Manager: {dependencies_manager_type}")

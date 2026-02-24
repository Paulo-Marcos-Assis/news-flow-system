# collector/exceptions.py

class FlowError(Exception):
    """Exceção base para todos os erros do Collector."""
    pass


class NoMatchingCSVFilesError(FlowError):
    """Nenhum arquivo CSV correspondente encontrado para os anos e diretório informados."""

    def __init__(self, years, data_path):
        self.years = years
        self.data_path = data_path
        super().__init__(
            f"No matching CSV files found for years {years} in '{data_path}'."
        )

class PathNotFoundError(FlowError):
    """Nenhum diretorio correspondente encotrado."""

    def __init__(self, data_path):
        self.data_path = data_path
        super().__init__(
            f"Path: '{data_path}' not found."
        )

class InvalidMessageFormatError(FlowError):
    """Formato de mensagem inválido recebido pelo coletor."""

    def __init__(self, message, error):
        self.error = error
        self.message = message
        super().__init__(
            f"Invalid message format: {message} Error: {error}"
        )

class UnexpectedReadError(FlowError):
    """Falha ao ler todos os arquivos CSV."""

    def __init__(self, message, files):
        self.files = files
        self.message = message
        super().__init__(
            f"Unexpected Read Error in files: {files} Message: '{message}'."
        )




class DatabaseConnectionError(FlowError):
    """Erro ao conectar ao banco de dados."""

    def __init__(self, db_url):
        self.db_url = db_url
        super().__init__(f"Failed to connect to database at {db_url}")


class ProcessingError(FlowError):
    """Erro genérico durante o processamento de mensagens/dados."""

    def __init__(self, detail: str):
        super().__init__(f"Processing error: {detail}")

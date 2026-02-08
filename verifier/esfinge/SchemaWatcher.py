import logging
import json
import yaml
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SchemaWatcher:
    def __init__(self, schema_file: str):
        self.schema_file = schema_file
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Carrega schema de referência a partir de arquivo externo."""
        try:
            with open(self.schema_file, "r", encoding="utf-8") as f:
                if self.schema_file.endswith(".yaml") or self.schema_file.endswith(".yml"):
                    return yaml.safe_load(f)
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Schema file not found: {self.schema_file}. Using empty schema.")
            return {}

    def check_record(self, record: Dict[str, Any]) -> None:
        """Compara registro recebido com schema e gera alertas de divergência."""
        for table, fields in record.items():
            if table not in self.schema:
                logger.info(f"Tabela inesperada detectada: {table}")
                continue

            expected_fields = self.schema[table]

            for field, value in fields.items():
                if field not in expected_fields:
                    logger.info(f"[{table}] Campo inesperado: {field}")
                    continue

                expected_type = expected_fields[field]
                if not self._validate_type(value, expected_type):
                    logger.warning(
                        f"[{table}.{field}] Tipo divergente. Esperado: {expected_type}, "
                        f"Recebido: {type(value).__name__}"
                    )

            # Verifica se há campos esperados que estão ausentes
            for expected_field in expected_fields:
                if expected_field not in fields:
                    logger.warning(f"[{table}] Campo ausente: {expected_field}")

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Valida se o valor corresponde ao tipo esperado no schema."""
        if value is None:
            return True  # aceitar nulos

        type_map = {
            "int": int,
            "string": str,
            "decimal": (float, int),
            "bool": bool,
        }

        expected_class = type_map.get(expected_type, str)
        return isinstance(value, expected_class)

    def learn_from_record(self, record: Dict[str, Any]) -> None:
        """
        Atualiza o schema externo com novos campos/tabelas detectados.
        Gera backup e persiste alterações.
        """
        updated = False

        for table, fields in record.items():
            if table not in self.schema:
                self.schema[table] = {}
                logger.info(f"[AUTO-LEARN] Nova tabela adicionada: {table}")
                updated = True

            for field, value in fields.items():
                if field not in self.schema[table]:
                    inferred_type = self._infer_type(value)
                    self.schema[table][field] = inferred_type
                    logger.info(
                        f"[AUTO-LEARN] Novo campo em {table}: {field} -> {inferred_type}"
                    )
                    updated = True

        if updated:
            self._persist_schema()

    def _persist_schema(self):
        """Salva o schema atualizado em disco (com backup)."""
        import shutil, os, datetime

        # backup
        if os.path.exists(self.schema_file):
            backup_file = f"{self.schema_file}.bak_{datetime.datetime.now().isoformat()}"
            shutil.copy2(self.schema_file, backup_file)

        # salvar
        if self.schema_file.endswith(".yaml") or self.schema_file.endswith(".yml"):
            with open(self.schema_file, "w", encoding="utf-8") as f:
                yaml.safe_dump(self.schema, f, allow_unicode=True)
        else:
            with open(self.schema_file, "w", encoding="utf-8") as f:
                json.dump(self.schema, f, indent=2, ensure_ascii=False)

    def _infer_type(self, value: Any) -> str:
        """Inferência simples de tipo para auto-learning."""
        if value is None:
            return "string|null"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "decimal"
        if isinstance(value, bool):
            return "bool"
        return "string"

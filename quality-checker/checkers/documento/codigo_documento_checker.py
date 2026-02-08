from checkers.base_quali_checker import BaseQualiChecker


class CodigoDocumentoChecker(BaseQualiChecker):
    check_name = "codigo_documento"
    table_name = "documento"

    def check(self, record):
        if "documento" in record:
            docs_to_check = record["documento"]
            if not isinstance(docs_to_check, list):
                docs_to_check = [docs_to_check]

            for doc in docs_to_check:
                if isinstance(doc, dict) and doc.get("codigo_documento") not in ("indefinido", "null", None):
                    cod_str = str(doc["codigo_documento"])
                    if not cod_str.isdigit():
                        return False, f"Código do documento ({record['documento']['codigo_documento']}) não contém apenas dígitos."
        return True, None

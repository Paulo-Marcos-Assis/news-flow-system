from utils.date_checker import DateChecker


class DocumentoDataEmissaoChecker(DateChecker):
    check_name = "data_emissao"
    table_name = "documento"

    def check(self, record):
        if "documento" not in record:
            return True, None

        docs_to_check = record["documento"]
        if not isinstance(docs_to_check, list):
            docs_to_check = [docs_to_check]

        for doc in docs_to_check:
            if isinstance(doc, dict) and 'data_emissao' in doc and doc.get("data_emissao") not in ("indefinido", "null", None):
                date = doc["data_emissao"]
                if not self.is_valid_date(date):
                    return False, f"('documento') Data emissão ({doc['data_emissao']}) inválida."
                doc['data_emissao'] = self.return_str_date(date, "timestamp")
        
        return True, None


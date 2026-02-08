from utils.cnpj_checker import CnpjChecker


class CnpjConsorcioChecker(CnpjChecker):
    check_name = "cnpj_consorcio"
    table_name = "processo_licitatorio_pessoa"

    def check(self, record):
        if "processo_licitatorio_pessoa" in record and record['processo_licitatorio_pessoa'].get("cnpj_consorcio") not in ("indefinido", "null", None):
            cnpj_consorcio = record['processo_licitatorio_pessoa']["cnpj_consorcio"]
            # Remove field if it is 0
            if str(cnpj_consorcio).strip() in ('0', '0.0'):
                del record['processo_licitatorio_pessoa']["cnpj_consorcio"]
                return True, None
            # Validate CNPJ
            checked_cnpj = self.cnpj_check(cnpj_consorcio)
            if checked_cnpj is None:
                return False, f"('processo_licitatorio_pessoa') CNPJ consórcio ({cnpj_consorcio}) inválido."
            record['processo_licitatorio_pessoa']["cnpj_consorcio"] = int(checked_cnpj)

        return True, None

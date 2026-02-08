from utils.cep_checker import  CepChecker

class CepEmitenteChecker(CepChecker):
    check_name = "cep_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cep_emitente" in record['nfe'].keys() and record['nfe']["cep_emitente"] not in ("indefinido","null",None,""): 
            # Checa CEP e retira '-' caso tenha
            checked_cep = self.cep_check(record['nfe']['cep_emitente'])
            if checked_cep is None:
                return False, f"Cep emitente({record['nfe']['cep_emitente']}) inválido."
            record['nfe']["cep_emitente"] = checked_cep
        return True,None
        
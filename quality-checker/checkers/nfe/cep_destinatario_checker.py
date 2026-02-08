from utils.cep_checker import  CepChecker

class CepDestinarioChecker(CepChecker):
    check_name = "cep_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cep_destinatario" in record['nfe'].keys() and record['nfe']["cep_destinatario"] not in ("indefinido","null",None,""): 
            # Checa CEP e retira '-' caso tenha
            checked_cep = self.cep_check(record['nfe']['cep_destinatario'])
            if checked_cep is None:
                return False, f"Cep destinatario({record['nfe']['cep_destinatario']}) inválido."
            record['nfe']["cep_destinatario"] = checked_cep
        return True,None
        
from utils.cpf_checker import CpfChecker

class CpfEmitenteChecker(CpfChecker):
    check_name = "cpf_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cpf_emitente" in record['nfe'].keys() and record['nfe']["cpf_emitente"] not in ("indefinido","null",None,""):
            # Checa CPF e remove símbolos, caso tenha
            checked_cpf = self.cpf_check(record['nfe']['cpf_emitente'])
            if (checked_cpf is None):
                return False, f"CPF emitente ({record['nfe']['cpf_emitente']}) inválido"
            record['nfe']['cpf_emitente'] = checked_cpf
            
        return True,None
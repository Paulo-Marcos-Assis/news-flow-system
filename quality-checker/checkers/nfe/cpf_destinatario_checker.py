from utils.cpf_checker import CpfChecker


class CpfDestinatarioChecker(CpfChecker):
    check_name = "cpf_destinatario"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cpf_destinatario" in record['nfe'].keys() and record['nfe'][
            "cpf_destinatario"] not in ("indefinido", "null", None, ""):
            # Checa CPF e remove símbolos, caso tenha
            checked_cpf = self.cpf_check(record['nfe']['cpf_destinatario'])
            if (checked_cpf is None):
                return False, f"CPF destinatário ({record['nfe']['cpf_destinatario']}) inválido"
            record['nfe']['cpf_destinatario'] = checked_cpf

        return True, None

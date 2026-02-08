from utils.cpf_checker import CpfChecker


class PessoaFisicaCpf(CpfChecker):
    check_name = "cpf"
    table_name = "pessoa_fisica"

    def check(self, record):
        if "pessoa_fisica" in record and record['pessoa_fisica'].get("cpf") not in ("indefinido", "null", None):
            checked_cpf = self.cpf_check(record['pessoa_fisica']['cpf'])
            if checked_cpf is None:
                return False, f"('pessoa_fisica') CPF ({record['pessoa_fisica']['cpf']}) inválido."
            if not self.is_varchar(checked_cpf, 20):
                return False, f"('pessoa_fisica') CPF ({checked_cpf}) fora do limite (varchar 20)."
            record['pessoa_fisica']['cpf'] = checked_cpf
        return True, None
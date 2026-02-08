from utils.cep_checker import CepChecker


class UnidadeGestoraCepChecker(CepChecker):
    check_name = "cep"
    table_name = "unidade_gestora"

    def check(self, record):
        if "unidade_gestora" in record:
            ugs_to_check = record['unidade_gestora']
            if not isinstance(ugs_to_check, list):
                ugs_to_check = [ugs_to_check]

            for ug in ugs_to_check:
                if isinstance(ug, dict) and ug.get('cep') not in ("indefinido", "null", None):
                    # Remove CEP if it is 0
                    if str(ug['cep']).strip() == '0':
                        del ug['cep']
                        continue
                    # Checa CEP e retira '-' caso tenha
                    checked_cep = self.cep_check(ug['cep'])
                    if checked_cep is None or not self.is_varchar(checked_cep, 20):
                        # Remove invalid CEP from message
                        del ug['cep']
                        continue
                    ug["cep"] = checked_cep
        return True, None


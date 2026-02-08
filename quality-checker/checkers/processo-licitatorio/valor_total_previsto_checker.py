from utils.value_checker import ValueChecker

class ValorTotalPrevistoChecker(ValueChecker):
    check_name = "valor_total_previsto"
    table_name = "processo_licitatorio"

    def check(self, record):
        if "processo_licitatorio" in record.keys() and "valor_total_previsto" in record['processo_licitatorio'].keys() and record['processo_licitatorio']['valor_total_previsto'] not in ("indefinido","null",None,""):
            if not self.value_check(record['processo_licitatorio']["valor_total_previsto"]):
                return False, f"Valor total previsto ({record['processo_licitatorio']['valor_total_previsto']}) inválido."
            # Normalize comma to dot in the output
            record['processo_licitatorio']['valor_total_previsto'] = self.normalize_value(record['processo_licitatorio']['valor_total_previsto'])
        return True,None
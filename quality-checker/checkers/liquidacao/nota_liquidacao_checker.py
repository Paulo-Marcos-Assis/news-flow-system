from checkers.base_quali_checker import BaseQualiChecker


class NotaLiquidacaoChecker(BaseQualiChecker):
    check_name = "nota_liquidacao"
    table_name = "liquidacao"

    def check(self, record):
        if "liquidacao" in record and record["liquidacao"].get("nota_liquidacao") not in ("indefinido", "null", None):
            nota_liquidacao = record["liquidacao"]["nota_liquidacao"]
            if not isinstance(nota_liquidacao, str):
                nota_liquidacao = str(nota_liquidacao)

            if not nota_liquidacao.replace(' ', '').isdigit():
                return False, f"('liquidacao') Nota de liquidação ({nota_liquidacao}) inválida (deve conter apenas dígitos)."
            
            # Remove value if it's 0
            if nota_liquidacao.replace(' ', '') in ['0', '0.0']:
                del record["liquidacao"]["nota_liquidacao"]
            else:
                record["liquidacao"]["nota_liquidacao"] = nota_liquidacao

        return True, None
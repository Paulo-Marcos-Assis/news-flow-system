from checkers.base_nested_checker import BaseNestedChecker


class PagamentoEmpenhoNestedChecker(BaseNestedChecker):
    check_name = "pagamento_empenho"
    table_name = "liquidacao"
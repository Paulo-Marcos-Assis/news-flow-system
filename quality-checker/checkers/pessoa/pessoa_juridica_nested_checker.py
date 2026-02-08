from checkers.base_nested_checker import BaseNestedChecker


class PessoaJuridicaNestedChecker(BaseNestedChecker):
    check_name = "pessoa_juridica"
    table_name = "pessoa"
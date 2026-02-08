from checkers.base_nested_checker import BaseNestedChecker


class PessoaPessoaJuridicaNestedChecker(BaseNestedChecker):
    check_name = "pessoa_pessoa_juridica"
    table_name = "pessoa"
from checkers.base_quali_checker import BaseQualiChecker


class SituacaoCadastralChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "situacao_cadastral"

    def check(self, record):
        if "situacao_cadastral" in record.keys() and "descricao" in record['situacao_cadastral'].keys() and record["situacao_cadastral"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['situacao_cadastral']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_situacao_cadastral, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.situacao_cadastral WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('situacao_cadastral') Erro ao consultar tabela 'situacao_cadastral': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['situacao_cadastral'] = {"id_situacao_cadastral": best_match[0]}
            else:
                return False, f"('situacao_cadastral') Nenhuma correspondência encontrada para a descrição da situação cadastral: {descricao}"

        return True, None
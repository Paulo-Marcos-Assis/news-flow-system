from checkers.base_quali_checker import BaseQualiChecker


class NomeUnidadeOrcamentariaChecker(BaseQualiChecker):
    check_name = "nome_unidade_orcamentaria"
    table_name = "unidade_orcamentaria"

    def check(self, record):
        if "unidade_orcamentaria" in record and record['unidade_orcamentaria'].get("nome_unidade_orcamentaria") not in ("indefinido", "null", None):
            nome = record['unidade_orcamentaria']['nome_unidade_orcamentaria']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_unidade_orcamentaria, similarity(unaccent(%s), unaccent(nome_unidade_orcamentaria)) AS similaridade FROM public.unidade_orcamentaria WHERE similarity(unaccent(%s), unaccent(nome_unidade_orcamentaria)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(nome, nome)
                )
            
            if not success:
                return False, f"('unidade_orcamentaria') Erro ao consultar tabela 'unidade_orcamentaria': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['unidade_orcamentaria'] = {"id_unidade_orcamentaria": best_match[0]}

        return True, None
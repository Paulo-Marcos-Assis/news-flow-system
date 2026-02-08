from checkers.base_quali_checker import BaseQualiChecker


class TipoObjetoLicitacaoChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "tipo_objeto_licitacao"

    def check(self, record):
        if "tipo_objeto_licitacao" in record.keys() and "descricao" in record['tipo_objeto_licitacao'].keys() and record["tipo_objeto_licitacao"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['tipo_objeto_licitacao']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_tipo_objeto_licitacao, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.tipo_objeto_licitacao WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('tipo_objeto_licitacao') Erro ao consultar tabela 'tipo_objeto_licitacao': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['tipo_objeto_licitacao'] = {"id_tipo_objeto_licitacao": best_match[0]}
            else:
                return False, f"('tipo_objeto_licitacao') Nenhuma correspondência encontrada para a descrição do tipo do objeto da licitação: {descricao}"

        return True, None
from checkers.base_quali_checker import BaseQualiChecker


class TipoLicitacaoChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "tipo_licitacao" in record.keys() and "descricao" in record['tipo_licitacao'].keys() and record["tipo_licitacao"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['tipo_licitacao']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_tipo_licitacao, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.tipo_licitacao WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('tipo_licitacao') Erro ao consultar tabela 'tipo_licitacao': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['tipo_licitacao'] = {"id_tipo_licitacao": best_match[0]}
            else:
                return False, f"('tipo_licitacao') Nenhuma correspondência encontrada para a descrição do tipo da licitação: {descricao}"

        return True, None
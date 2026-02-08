from checkers.base_quali_checker import BaseQualiChecker


class ModalidadeLicitacaoChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "modalidade_licitacao"

    def check(self, record):
        if "modalidade_licitacao" in record.keys() and "descricao" in record['modalidade_licitacao'].keys() and record["modalidade_licitacao"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['modalidade_licitacao']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_modalidade_licitacao, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.modalidade_licitacao WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.6 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('modalidade_licitacao') Erro ao consultar tabela 'modalidade_licitacao': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['modalidade_licitacao'] = {"id_modalidade_licitacao": best_match[0]}
            else:
                return False, f"('modalidade_licitacao') Nenhuma correspondência encontrada para a descrição da modalidade da licitação: {descricao}"

        return True, None
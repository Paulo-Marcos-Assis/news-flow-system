from checkers.base_quali_checker import BaseQualiChecker

class TipoEspecificacaoUgChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "tipo_especificacao_ug"

    def check(self, record):
        if "tipo_especificacao_ug" in record.keys() and "descricao" in record['tipo_especificacao_ug'].keys() and record["tipo_especificacao_ug"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['tipo_especificacao_ug']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_tipo_especificacao_ug, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.tipo_especificacao_ug WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('tipo_especificacao_ug') Erro ao consultar tabela 'tipo_especificacao_ug': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['tipo_especificacao_ug'] = {"id_tipo_especificacao_ug": best_match[0]}
            else:
                return False, f"('tipo_especificacao_ug') Nenhuma correspondência encontrada para a descrição do tipo de especificação da unidade gestora: {descricao}"

        return True, None
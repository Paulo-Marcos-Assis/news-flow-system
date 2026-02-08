from checkers.base_quali_checker import BaseQualiChecker

class MotivoSituacaoCadastralChecker(BaseQualiChecker):
    check_name = "descricao"
    table_name = "motivo_situacao_cadastral"

    def check(self, record):
        if "motivo_situacao_cadastral" in record.keys() and "descricao" in record['motivo_situacao_cadastral'].keys() and record["motivo_situacao_cadastral"]["descricao"] not in ("indefinido", "null", None):
            descricao = record['motivo_situacao_cadastral']['descricao']

            success, rows, error, query = self.execute_db_query(
                "SELECT id_motivo_situacao_cadastral, similarity(unaccent(%s), unaccent(descricao)) AS similaridade FROM public.motivo_situacao_cadastral WHERE similarity(unaccent(%s), unaccent(descricao)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
                params=(descricao, descricao)
                )
            
            if not success:
                return False, f"('motivo_situacao_cadastral') Erro ao consultar tabela 'motivo_situacao_cadastral': {error} | Query: {query}"
            
            if len(rows) != 0:          
                best_match = rows[0]
                record['motivo_situacao_cadastral'] = {"id_motivo_situacao_cadastral": best_match[0]}
            else:
                return False, f"('motivo_situacao_cadastral') Nenhuma correspondência encontrada para a descrição do motivo da situação cadastral: {descricao}"

        return True, None
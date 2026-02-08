from utils.city_name_checker import CityNameChecker
import re


REGEX_CONS = re.compile(r'\b(cons\.|consorcio|consórcio)(?=\s|$)', re.IGNORECASE)
REGEX_INTERM = re.compile(r'\b(interm\.)(?=\s|$)')
REGEX_MUN = re.compile(r'^(município de|municipio de)\s+', re.IGNORECASE)

class NomeUgChecker(CityNameChecker):
    check_name = "nome_ug"
    table_name = "unidade_gestora"

    def check(self, record):
        if "unidade_gestora" in record:
            ugs_to_check = record['unidade_gestora']
            is_list = isinstance(ugs_to_check, list)
            if not is_list:
                ugs_to_check = [ugs_to_check]

            for i, ug in enumerate(ugs_to_check):
                if isinstance(ug, dict) and ug.get('nome_ug') not in ("indefinido", "null", None):
                    nome_ug = REGEX_INTERM.sub('Intermunicipal', ug['nome_ug'])

                    if self.city_check(REGEX_MUN.sub('', nome_ug)) is not None:
                        if 'ente' in record and record['ente'].get('ente') not in ("indefinido", "null", None):
                            ente = record['ente']['ente']
                            if not REGEX_CONS.search(ente) and self.city_check(REGEX_MUN.sub('', ente)) is None:
                                temp = record['ente']['ente']
                                record['ente']['ente'] = nome_ug.title()
                                nome_ug = temp

                    if (city_result := self.city_check(REGEX_MUN.sub('', nome_ug))) is not None:
                        id_municipio, nome_municipio = city_result
                        nome_ug = "Prefeitura Municipal de " + nome_municipio 

                    if ug.get('cnpj') not in ("indefinido", "null", None):
                        query = "SELECT id_unidade_gestora, similarity(unaccent(%s), unaccent(nome_ug)) AS similaridade FROM public.unidade_gestora WHERE similarity(unaccent(%s), unaccent(nome_ug)) >= 0.8 AND cnpj = %s ORDER BY similaridade DESC LIMIT 1;"
                        params = (nome_ug, nome_ug, ug['cnpj'])
                    else:
                        query = "SELECT id_unidade_gestora, similarity(unaccent(%s), unaccent(nome_ug)) AS similaridade FROM public.unidade_gestora WHERE similarity(unaccent(%s), unaccent(nome_ug)) >= 0.8 AND cnpj IS NULL ORDER BY similaridade DESC LIMIT 1;"
                        params = (nome_ug, nome_ug)

                    success, rows, error, executed_query = self.execute_db_query(query, params=params)
                    
                    if not success:
                        return False, f"('unidade_gestora') Erro ao consultar tabela 'unidade_gestora': {error} | Query: {executed_query}"
                    if len(rows) != 0:          
                        best_match = rows[0]
                        # Replace the item in the list/record with just the FK
                        if is_list:
                            ugs_to_check[i] = {"id_unidade_gestora": best_match[0]}
                        else:
                            record['unidade_gestora'] = {"id_unidade_gestora": best_match[0]}
                    else:
                        ug['nome_ug'] = nome_ug.title()

        return True, None
    

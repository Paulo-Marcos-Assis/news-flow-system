from abc import ABC
from checkers.base_quali_checker import BaseQualiChecker


class CityNameChecker(BaseQualiChecker, ABC):

    def city_check(self, city_name: str, confidence_limit: float = 0.6):
        """
        Returns tuple (id_municipio, nome_municipio) if found, None otherwise.
        """
        if not isinstance(city_name, str):
            return None

        query = """
            SELECT id_municipio, nome_municipio, similarity(unaccent(%s), unaccent(nome_municipio)) AS similaridade 
            FROM public.municipio 
            WHERE similarity(unaccent(%s), unaccent(nome_municipio)) >= %s 
            ORDER BY similaridade DESC 
            LIMIT 1;
        """
        params = (city_name, city_name, confidence_limit)

        success, rows, error, executed_query = self.execute_db_query(query, params=params)

        if not success:
            self.logger.error(f"Erro ao consultar tabela 'municipio': {error} | Query: {executed_query}")
            return None

        if rows and len(rows) > 0:
            return (rows[0][0], rows[0][1])  # (id_municipio, nome_municipio)

        return None

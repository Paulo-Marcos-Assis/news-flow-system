from utils.city_name_checker import CityNameChecker


class NomeMunicipioChecker(CityNameChecker):
    check_name = "nome_municipio"
    table_name = "municipio"

    def check(self, record):
        if "municipio" in record.keys() and "nome_municipio" in record['municipio'].keys() and record['municipio']["nome_municipio"] not in ("indefinido", "null", None, ""):
            nome_municipio = record['municipio']['nome_municipio']
            
            # Handle list input - extract first element if it's a list
            if isinstance(nome_municipio, list):
                if len(nome_municipio) == 0 or nome_municipio[0] in ("indefinido", "null", None, ""):
                    return True, None
                nome_municipio = nome_municipio[0]
            
            if (checked_city := self.city_check(nome_municipio)) is None:
                return False, f"Nome do município ({nome_municipio}) desconhecido."

            # Store id_municipio instead of nome_municipio
            id_municipio, nome_municipio = checked_city
            record['municipio'] = {"id_municipio": id_municipio}
        return True, None
from utils.city_name_checker import CityNameChecker
from rapidfuzz import fuzz
import re


REGEX_CONS = re.compile(r'\b(cons\.|consorcio|consórcio)(?=\s|$)', re.IGNORECASE)
REGEX_INTERM = re.compile(r'\b(interm\.)(?=\s|$)')
REGEX_MUN = re.compile(r'^(município de|municipio de)\s+', re.IGNORECASE)
REGEX_ESTADO = re.compile(r'^estado\s+d[eoa]\s+', re.IGNORECASE)
INVALID_VALUES = ("indefinido", "null", None, "")


class EnteChecker(CityNameChecker):
    check_name = "ente"
    table_name = "ente"

    def _get_ug(self, record):
        return record.get('unidade_gestora', {}).get('nome_ug')

    def _is_valid(self, value):
        return value not in INVALID_VALUES

    def _strip_municipio_prefix(self, name):
        return REGEX_MUN.sub('', name)

    def check(self, record):
        ente_data = record.get('ente', {})
        ente = ente_data.get('ente')

        if not self._is_valid(ente):
            return True, None

        # Handle consórcio case
        if REGEX_CONS.search(ente):
            ente = REGEX_INTERM.sub("Intermunicipal", ente)
            record.setdefault('unidade_gestora', {})
            
            nome_ug = self._get_ug(record)
            if not self._is_valid(nome_ug):
                record['unidade_gestora']['nome_ug'] = ente
            elif fuzz.WRatio(self.normalize_string(nome_ug), self.normalize_string(ente)) < 90:
                return False, f"Ente ({ente}) é um consórcio, mas o nome da unidade gestora ({nome_ug}) não faz referência ao consórcio"

        # Handle non-city ente - try to swap with unidade_gestora (skip if ente is a state)
        elif self.city_check(self._strip_municipio_prefix(ente)) is None and not REGEX_ESTADO.search(ente):
            nome_ug = self._get_ug(record)
            if not self._is_valid(nome_ug):
                return False, f"Ente ({ente}) fora do padrão esperado, e não pôde ser trocado com unidade gestora (sem unidade gestora)."

            if self.city_check(self._strip_municipio_prefix(nome_ug)) is None and not REGEX_ESTADO.search(nome_ug):
                return False, f"Ente ({ente}) fora do padrão esperado, e não pôde ser trocado com unidade gestora ({nome_ug})."

            # Swap ente with unidade_gestora
            record['unidade_gestora']['nome_ug'] = ente.title()
            ente = nome_ug

        # Normalize ente using city database
        if (city_result := self.city_check(self._strip_municipio_prefix(ente))) is not None:
            _, ente = city_result

        # Query ente table for id_ente
        success, rows, error, query = self.execute_db_query(
            "SELECT id_ente, similarity(unaccent(%s), unaccent(ente)) AS similaridade FROM public.ente WHERE similarity(unaccent(%s), unaccent(ente)) >= 0.8 ORDER BY similaridade DESC LIMIT 1;",
            params=(ente, ente)
        )

        if not success:
            return False, f"('ente') Erro ao consultar tabela 'ente': {error} | Query: {query}"

        # Normalize municipio field - store id_municipio
        municipio = ente_data.get('municipio')
        if self._is_valid(municipio):
            if (municipio_result := self.city_check(municipio)) is not None:
                ente_data['id_municipio'] = municipio_result[0]
            del ente_data['municipio']

        # Update record with normalized ente
        if rows:
            record['ente']['id_ente'] = rows[0][0]

        record['ente']['ente'] = ente.title()

        return True, None
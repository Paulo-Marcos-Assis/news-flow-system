from abc import ABC
from rapidfuzz import process
from rapidfuzz.fuzz import WRatio

from checkers.base_quali_checker import BaseQualiChecker

state_acronym = {
    "acre": "AC",
    "alagoas": "AL",
    "amapá": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceará": "CE",
    "distrito federal": "DF",
    "espírito santo": "ES",
    "goiás": "GO",
    "maranhão": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "pará": "PA",
    "paraíba": "PB",
    "paraná": "PR",
    "pernambuco": "PE",
    "piauí": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondônia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "são paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO"
}

states = {
    "acre": "Acre",
    "alagoas": "Alagoas",
    "amapa": "Amapá",
    "amazonas": "Amazonas",
    "bahia": "Bahia",
    "ceara": "Ceará",
    "distrito federal": "Distrito Federal",
    "espirito santo": "Espírito Santo",
    "goias": "Goiás",
    "maranhao": "Maranhão",
    "mato grosso": "Mato Grosso",
    "mato grosso do sul": "Mato Grosso do Sul",
    "minas gerais": "Minas Gerais",
    "para": "Pará",
    "paraiba": "Paraíba",
    "parana": "Paraná",
    "pernambuco": "Pernambuco",
    "piaui": "Piauí",
    "rio de janeiro": "Rio de Janeiro",
    "rio grande do norte": "Rio Grande do Norte",
    "rio grande do sul": "Rio Grande do Sul",
    "rondonia": "Rondônia",
    "roraima": "Roraima",
    "santa catarina": "Santa Catarina",
    "sao paulo": "São Paulo",
    "sergipe": "Sergipe",
    "tocantins": "Tocantins"
}



class UfChecker(BaseQualiChecker, ABC):

    def uf_acronym_check(self, uf_str: str):
        if uf_str.upper() in state_acronym.values():
            return uf_str.upper()

        return None

    def uf_name_check(self, uf_str: str, confidence_limit = 90.0):
        state_names = states.keys()

        normalized_uf_str = self.normalize_string(uf_str)
        if normalized_uf_str in state_names:
            return states[normalized_uf_str]

        (best_match, similarity, _) = process.extractOne(normalized_uf_str, state_names, scorer=WRatio)
        if similarity >= confidence_limit:
            return states[best_match]

        return None

    # Verifica se um nome de um estado é igual à sua sigla
    def uf_compare(self, name: str, acronym: str) -> bool:
        normalized_name = name.lower()
        if normalized_name in state_acronym.keys():
            return state_acronym[normalized_name] == acronym.upper()

        return False
from utils.date_checker import DateChecker


class NoticiaDataPublicacaoChecker(DateChecker):
    check_name = "data_publicacao"
    table_name = "noticia"

    def check(self, record):
        if "noticia" in record and record["noticia"].get("data_publicacao") not in ("indefinido", "null", None):
            if not self.is_valid_date(record['noticia']['data_publicacao']):
                return False, f"('noticia') Data de publicação da notícia ({record['noticia']['data_publicacao']}) inválida."
            record['noticia']['data_publicacao'] = self.return_str_date(record['noticia']['data_publicacao'])
        
        return True, None
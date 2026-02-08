from ..base_verifier import BaseVerifier

class ModalidadeVerifier(BaseVerifier):
    verification_name = "descricao"

    def verify(self, record):

        modalidades_licitacao = ["Convite", "Tomada de Preços", "Concorrência", "Leilão", "Concurso", "Pregão Presencial",
                                 "Pregão Eletrônico", "Dispensa de Licitação", "Inexigibilidade de Licitação",
                                 "Chamada Pública"]

        modalidade = record['extracted']['modalidade_licitacao']['descricao']

        # if modalidade and modalidade not in modalidades_licitacao:
        #     return False, f"O tipo de Molidade extraído ({modalidade}) não é válido."

        return True, None
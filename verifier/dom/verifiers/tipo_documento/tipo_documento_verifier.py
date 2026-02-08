from ..base_verifier import BaseVerifier

class TipoDocumentoVerifier(BaseVerifier):

    verification_name = "tipo_documento"

    def verify(self, record):
        tipos_documento = [
            "Aviso de Licitação",
            "Retificação de Aviso de Licitação", 
            "Termo de Ratificação",
            "Termo Aditivo",
            "Extrato de Contrato",
            "Retificação de Edital",
            "Retificação de Homologação",
            "Retificação de Termo Aditivo",
            "Termo de Referência",
            "Termo de Anulação",
            "Termo de Adjudicação",
            "Ata de Licitação Fracassada",
            "Ata de Registro de Preços",
            "Ata de Sessão Pública",
            "Ata de Solicitações",
            "Retificação de Contratação Direta",
            "Retificação de Termo de Formalização",
            "Termo de Credenciamento",
            "Termo de Formalização",
            "Ato de Contratação Direta",
            "Termo de Formalização",
            "Aviso de Dispensa",
            "Aviso de Inexigibilidade",
            "Termo de Homologação",
            "Termo de Homologação e Adjudicação",
            "Dispensa de Licitação",
            "Inexigibilidade de Licitação",
            "Edital",
            "Chamada Pública"
        ]

        tipo = record['extracted']['tipo_documento']['descricao']

        if tipo is None:
            return False, "O tipo do documento não foi extraído do documento original."

        if tipo and tipo not in tipos_documento:
            return False, f"O tipo de documento extraído ({tipo}) não é válido."

        return True, None

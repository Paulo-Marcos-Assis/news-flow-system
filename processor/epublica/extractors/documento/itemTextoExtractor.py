from ..base_extractor import BaseExtractor

class TabelaDocumentoExtractor(BaseExtractor):
    field_name = "documento_completo" 
    scope = "documento" 

    def extract(self, record):
        

        documentos_finais = []
        for doc_bruto in record.get('listTextos', []):
            doc_limpo = {
                "tipo_documento": doc_bruto.get("denominacao"),                
                "local_acesso_arquivo": doc_bruto.get("link")
            }
            documentos_finais.append(doc_limpo)
        
        return documentos_finais
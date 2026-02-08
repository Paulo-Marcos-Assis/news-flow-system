import inspect
import json
import re
import traceback
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional

from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService


class VerifierEsfinge(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        self.errors: List[Dict[str, str]] = []

    # Entry point
    def process_message(self, message):

        return message
    
    
        try:
            self.logger.info(" Message received on the VERIFIER ESFINGE ".center(84, "#"))
            self.errors.clear()

            # 1) Parse
            record = self._parse_json_message(message)

            # 2) Se vier lista, aceitar apenas 1 item
            if isinstance(record, list):
                if len(record) == 1:
                    record = record[0]
                else:
                    self._send_error(
                        message,
                        "Received list must contain exactly 1 item",
                        traceback.format_exc(),
                        severity="FAIL",
                        queue=self.fail_queue
                    )
                    return None

            # 3) Normalização (garante chaves e campos com None)
            record = self._normalize_record(record)
            self.logger.info(" Record normalized for hierarchical schema ".center(84, "#"))

            # 4) Verificações
            self._verify_schema(record)
            self.logger.info(" Schemas Checked ".center(84, "#"))

            self._verify_semantics(record)
            self.logger.info(" Semantics Checked ".center(84, "#"))

            self._verify_consistency(record)
            self.logger.info(" Consistency Checked ".center(84, "#"))

            # 5) Resultado
            if self.errors:
                formatted_errors = "; ".join([f"{e['field']}: {e['error']}" for e in self.errors])
                self.logger.warning(
                    f" success: {False}, Registration check failed, sending to {self.fail_queue} ".center(84, "#")
                )
                self._send_error(
                    record,
                    f"Registration check failed: {formatted_errors}",
                    traceback.format_exc(),
                    severity="FAIL",
                    queue=self.fail_queue
                )
                return None

            self.logger.info(
                f"success: True, Record processed successfully on VERIFIER ESFINGE, sending to {self.output_queue} ".center(
                    84, "#")
            )
            # retorna o mesmo payload (não alterado)
            return record

        except Exception as e:
            self._send_error(
                message,
                f"Unexpected error in VERIFIER ESFINGE: {str(e)}",
                traceback.format_exc(),
                severity="ERROR"
            )
            return None

    # Helpers gerais
    def _parse_json_message(self, message):
        self.logger.info(" Standardizing in dict format ".center(84, "#"))
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        if isinstance(message, str):
            return json.loads(message)
        elif isinstance(message, dict):
            return message
        else:
            raise TypeError(f"Unsupported message TYPE: {type(message)}")

    def _send_error(self, message, error_msg, tb=None, severity="ERROR", service=None, stage=None, queue=None):
        # Infere service e stage
        if service is None or stage is None:
            frame = inspect.currentframe()
            caller_frame = inspect.getouterframes(frame, 2)[1]
            if service is None and 'self' in caller_frame.frame.f_locals:
                service = caller_frame.frame.f_locals['self'].__class__.__name__
            if stage is None:
                stage = caller_frame.function
        if queue is None:
            queue = self.error_queue

        timestamp_utc = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        error_payload = {
            "timestamp": timestamp_utc,
            "service": service,
            "stage": stage,
            "severity": severity,
            "error": error_msg,
            "message": message if isinstance(message, (dict, str)) else str(message),
            "traceback": tb
        }
        self.queue_manager.publish_message(queue, json.dumps(error_payload, ensure_ascii=False))
        self.logger.error(json.dumps(error_payload, ensure_ascii=False))

    def _add_error(self, field: str, msg: str):
        self.errors.append({"field": field, "error": msg})

    # Normalização (item 4)
    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Garante que todas as tabelas/campos esperados existam,
        preenchendo faltantes com None. Não transforma tipos do payload.
        """
        defaults = {
            "ente": {
                "id_municipio": None,
                "id_tipo_esfera": None,
                "ente": None,
            },
            "unidade_gestora": {
                "id_ente": None,
                "nome_ug": None,
                "cnpj": None,
                "id_tipo_ug": None,
                "id_tipo_especificacao_ug": None,
                "jurisdicionado_cn": None,
                "cep": None,
                "orgao_previdencia": None,
                "sigla_ug": None,
                "cod_unidade_consolidadora": None,
                "id_poder": None,
                "cod_ug": None,
            },
            "processo_licitatorio": {
                "id_unidade_gestora": None,
                "numero_edital": None,
                "situacao": None,
                "id_tipo_cotacao": None,
                "data_abertura_certame": None,
                "descricao_objeto": None,
                "numero_processo_licitatorio": None,
                "id_comissao_licitacao": None,
                "id_unidade_orcamentaria": None,
                "id_tipo_objeto_licitacao": None,
                "valor_total_previsto": None,
                "data_limite": None,
            },
            "modalidade_licitacao": {
                "id_modalidade_licitacao": None,
            },
            "contrato": {
                "competencia": None,
                "id_texto_juridico": None,
                "id_processo_licitatorio": None,
                "data_autorizacao_estadual": None,
                "id_resp_juridico": None,
                "data_vencimento": None,
                "id_contrato": None,
                "valor_contrato": None,
                "id_contrato_superior": None,
                "data_assinatura": None,
                "numero_contrato": None,
                "valor_garantia": None,
                "numero_autorizacao_estadual": None,
                "descricao_objetivo": None,
            },
            "tipo_licitacao": {
                "id_tipo_licitacao": None,
                "descricao_modalidade": None,
                "descricao": None,
                "modalidade": None,
            }
        }

        # Garante chaves de topo
        for scope in defaults.keys():
            record.setdefault(scope, {})

        # Garante campos internos
        for scope, fields in defaults.items():
            for field, default in fields.items():
                record[scope].setdefault(field, default)

        return record

    # Verificações de Schema
    def _verify_schema(self, record: Dict[str, Any]):
        self.logger.info(" Checking Schemas ".center(84, "#"))

        required_tables = ["processo_licitatorio", "unidade_gestora", "ente"]
        for table in required_tables:
            if table not in record or not isinstance(record[table], dict):
                self._add_error(table, "Tabela obrigatória ausente")
                # se a tabela nem é dict, pare de checar campos dela
                continue

        # Campos obrigatórios mínimos no novo schema
        required_fields = {
            # processo_licitatorio: exige identificação mínima do processo
            "processo_licitatorio": ["numero_processo_licitatorio", "numero_edital"],
            # ente: somente o nome é obrigatório (IDs podem vir nulos)
            "ente": ["ente"],
            # unidade_gestora: identificação básica
            "unidade_gestora": ["cod_ug", "nome_ug"],
        }

        for table, fields in required_fields.items():
            if table not in record or not isinstance(record[table], dict):
                continue
            for field in fields:
                if record[table].get(field) in (None, "", []):
                    self._add_error(f"{table}.{field}", "Required field missing or empty")

    # Verificações Semânticas
    def _verify_semantics(self, record: Dict[str, Any]):
        self.logger.info(" Checking Semantics ".center(84, "#"))
        # ---------- Datas ----------
        # data_abertura_certame (YYYY-MM-DD) não pode ser futura
        self._check_date_past_or_today(
            record.get("processo_licitatorio", {}).get("data_abertura_certame"),
            "processo_licitatorio.data_abertura_certame"
        )

        # contrato: data_vencimento >= data_assinatura (quando ambas presentes)
        data_assinatura = self._parse_date(record.get("contrato", {}).get("data_assinatura"))
        data_vencimento = self._parse_date(record.get("contrato", {}).get("data_vencimento"))
        if data_assinatura and data_vencimento and data_vencimento < data_assinatura:
            self._add_error("contrato.data_vencimento", "End date cannot be earlier than start date")

        # data_autorizacao_estadual (se houver) não pode ser futura
        self._check_date_past_or_today(
            record.get("contrato", {}).get("data_autorizacao_estadual"),
            "contrato.data_autorizacao_estadual"
        )

        # data_limite (se houver) não pode ser anterior à data_abertura_certame
        data_limite = self._parse_date(record.get("processo_licitatorio", {}).get("data_limite"))
        data_abertura = self._parse_date(record.get("processo_licitatorio", {}).get("data_abertura_certame"))
        if data_limite and data_abertura and data_limite < data_abertura:
            self._add_error("processo_licitatorio.data_limite", "Deadline cannot be earlier than opening date")

        # ---------- Números ----------
        # numero_processo_licitatorio deve ser inteiro positivo (se presente)
        nproc = record.get("processo_licitatorio", {}).get("numero_processo_licitatorio")
        if nproc not in (None, ""):
            if not self._is_int_like(nproc) or int(nproc) <= 0:
                self._add_error("processo_licitatorio.numero_processo_licitatorio", "Must be a positive integer")

        # valor_total_previsto não pode ser negativo
        vtp = record.get("processo_licitatorio", {}).get("valor_total_previsto")
        if vtp not in (None, ""):
            num = self._to_float(vtp)
            if num is None:
                self._add_error("processo_licitatorio.valor_total_previsto", "Invalid numeric value")
            elif num < 0:
                self._add_error("processo_licitatorio.valor_total_previsto", "Value cannot be negative")

        # contrato.valor_contrato (se existir) deve ser > 0
        vcontr = record.get("contrato", {}).get("valor_contrato")
        if vcontr not in (None, ""):
            num = self._to_float(vcontr)
            if num is None:
                self._add_error("contrato.valor_contrato", "Invalid numeric value")
            elif num <= 0:
                self._add_error("contrato.valor_contrato", "Contract value must be greater than zero")

        # unidade_gestora.cod_ug inteiro positivo (se presente)
        cod_ug = record.get("unidade_gestora", {}).get("cod_ug")
        if cod_ug not in (None, ""):
            if not self._is_int_like(cod_ug) or int(cod_ug) <= 0:
                self._add_error("unidade_gestora.cod_ug", "Must be a positive integer")

        # ---------- Texto ----------
        # processo_licitatorio.numero_edital não vazio
        numero_edital = record.get("processo_licitatorio", {}).get("numero_edital")
        if numero_edital in ("",):
            self._add_error("processo_licitatorio.numero_edital", "Must not be empty")

        # tipo_licitacao.descricao (se presente) não vazio
        tipo_desc = record.get("tipo_licitacao", {}).get("descricao")
        if tipo_desc == "":
            self._add_error("tipo_licitacao.descricao", "Must not be empty")

        # ---------- Formatos específicos (Brasil) ----------
        # CEP simples (00000-000 ou 8 dígitos)
        cep = record.get("unidade_gestora", {}).get("cep")
        if cep not in (None, "") and not re.match(r"^\d{5}-?\d{3}$", str(cep)):
            self._add_error("unidade_gestora.cep", "Invalid CEP format (expected 00000-000)")

        # CNPJ simples (somente formato/contagem; não faz checagem de dígitos verificadores aqui)
        cnpj = record.get("unidade_gestora", {}).get("cnpj")
        if cnpj not in (None, "") and not re.match(r"^\d{14}$|^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$", str(cnpj)):
            self._add_error("unidade_gestora.cnpj", "Invalid CNPJ format")

    # Verificações de Consistência
    def _verify_consistency(self, record: Dict[str, Any]):
        self.logger.info(" Checking Consistency ".center(84, "#"))

        # Ente: nome não pode estar vazio
        if not record.get("ente", {}).get("ente"):
            self._add_error("ente.ente", "Nome do ente não pode estar vazio")

        # Se há unidade_gestora, deve haver ente (vínculo institucional mínimo)
        if record.get("unidade_gestora") and not record.get("ente"):
            self._add_error("unidade_gestora", "Unidade gestora deve estar vinculada a um ente")

        # Se contrato.valor_contrato existe, é razoável exigir numero_contrato (regra útil para consistência mínima)
        vcontr = record.get("contrato", {}).get("valor_contrato")
        if vcontr not in (None, "") and not record.get("contrato", {}).get("numero_contrato"):
            self._add_error("contrato.numero_contrato",
                            "'Numero do contrato' is mandatory when there is a 'valor_contrato'")

        # Se processo tem id_unidade_gestora, espera-se também cod_ug informado em unidade_gestora (indício da UG presente)
        if record.get("processo_licitatorio", {}).get("id_unidade_gestora") not in (None, ""):
            if record.get("unidade_gestora", {}).get("cod_ug") in (None, ""):
                self._add_error("unidade_gestora.cod_ug", "'cod_ug' is mandatory when 'id_unidade_gestora' is present")

    # Funções utilitárias (sem mutar payload)
    @staticmethod
    def _is_int_like(v: Any) -> bool:
        try:
            int(str(v))
            return True
        except Exception:
            return False

    @staticmethod
    def _to_float(v: Any) -> Optional[float]:
        """
        Converte strings numéricas aceitando vírgula decimal (ex.: '216392,2').
        Retorna None se não for possível converter.
        """
        if v is None or v == "":
            return None
        s = str(v).strip().replace(" ", "")
        # troca vírgula decimal por ponto
        s = s.replace(".", "") if re.match(r"^\d{1,3}(\.\d{3})+(,\d+)?$", s) else s
        s = s.replace(",", ".")
        try:
            return float(s)
        except Exception:
            return None

    @staticmethod
    def _parse_date(s: Any) -> Optional[date]:
        if not s:
            return None
        try:
            return datetime.strptime(str(s), "%Y-%m-%d").date()
        except Exception:
            return None

    def _check_date_past_or_today(self, s: Any, field_path: str):
        if s in (None, ""):
            return
        try:
            dt = datetime.strptime(str(s), "%Y-%m-%d").date()
        except ValueError:
            self._add_error(field_path, "Invalid date format (expected YYYY-MM-DD)")
            return
        today = datetime.today().date()
        if dt > today:
            self._add_error(field_path, "Date cannot be in the future")


if __name__ == '__main__':
    title = " Verifier Esfinge Started "
    print(title.center(60, "#"))
    processor = VerifierEsfinge()
    processor.logger.info(title.center(60, "#"))
    processor.start()

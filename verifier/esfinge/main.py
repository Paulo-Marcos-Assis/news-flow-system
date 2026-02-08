import inspect
import json
import re
import traceback
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional, Union, Tuple

from dateutil import parser
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService


class VerifierEsfinge(BasicProducerConsumerService):
    def __init__(self, schema_file: Optional[str] = None):
        super().__init__()
        self.errors: List[Dict[str, str]] = []
        self.logger.info("VerifierEsfinge initialized")

    def process_message(self, message: Union[str, bytes, dict]) -> Optional[dict]:
        """"
        Main method to process a message.

        Args:
            message: Message to process (str, bytes, or dict)

        Returns:
            dict: Processed record or None if processing fails
        """
        try:
            self.logger.info("Processing message in VERIFIER ESFINGE".center(84, "#"))

            # Parse message
            record = self._parse_json_message(message)

            # Handle list input (take first item if single-item list)
            if isinstance(record, list):
                if len(record) == 1:
                    record = record[0]
                else:
                    self._send_error(
                        message,
                        "Only single-item lists are supported",
                        severity="FAIL",
                        queue=self.fail_queue
                    )
                    return None

            # Process record (normalize dates and monetary values)
            record = self._process_record(record)

            # Process semantics
            self._verify_semantics(record)

            self.logger.info("Message processed successfully".center(84, "#"))
            return record

        except Exception as e:
            self._send_error(
                message,
                f"Error processing message: {str(e)}",
                traceback.format_exc(),
                severity="ERROR"
            )
            return None

    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """Normalize date strings to YYYY-MM-DD format.

        Args:
            date_str: Date string to normalize

        Returns:
            str: Normalized date in YYYY-MM-DD format or original value if parsing fails
        """
        if not date_str or not isinstance(date_str, str):
            return date_str

        try:
            dt = parser.parse(date_str, dayfirst=True)
            return dt.strftime('%Y-%m-%d')
        except (ValueError, TypeError) as e:
            #self.logger.warning(f"Failed to parse date '{date_str}': {str(e)}")
            return date_str

    def _normalize_monetary_value(self, value: Any) -> Union[str, Any]:
        """Convert monetary values from '1,234.56' to '1234.56'.

        Args:
            value: Monetary value to normalize (string, number, or other)

        Returns:
            str: Normalized monetary value as string with dot as decimal separator
                 or original value if conversion fails
        """
        if not value or not isinstance(value, str):
            return value

        try:
            # Remove any non-numeric characters except comma and dot
            cleaned = ''.join(c for c in value if c.isdigit() or c in ',.')

            # Handle different decimal/thousands separators
            if ',' in cleaned:
                if '.' in cleaned:  # If both separators exist, assume comma is decimal
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:  # Only comma exists, treat as decimal
                    cleaned = cleaned.replace(',', '.')

            # Convert to float and back to string to normalize
            return str(float(cleaned))

        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to normalize monetary value '{value}': {str(e)}")
            return value

    def _process_record(self, record: Any) -> Any:
        """Process record to normalize dates, monetary values, and validate documents.

        Args:
            record: Input record (dict, list, or other)

        Returns:
            Processed record with normalized dates, monetary values, and validated documents
        """
        if not isinstance(record, (dict, list)):
            return record

        if isinstance(record, list):
            return [self._process_record(item) for item in record]

        # Process document numbers first
        record = self._process_document_numbers(record)

        # Process dictionary
        result = {}
        for key, value in record.items():
            try:
                if isinstance(value, (dict, list)):
                    result[key] = self._process_record(value)
                elif isinstance(value, str):
                    key_lower = key.lower()
                    if any(prefix in key_lower for prefix in ['data_', 'dt_', '_data', '_dt']):
                        result[key] = self._normalize_date(value)
                    elif any(prefix in key_lower for prefix in ['valor_', 'vl_', '_valor', 'qtd_item_', 'qt_item_']):
                        result[key] = self._normalize_monetary_value(value)
                    else:
                        result[key] = value
                # Normalizar campos booleanos
                elif key.lower() in ['prestacao_contas', 'regularizacao_orcamentaria']:
                    if isinstance(value, int):
                        result[key] = bool(value)
                    else:
                        result[key] = value
                else:
                    result[key] = value
            except Exception as e:
                self.logger.error(f"Error processing field '{key}': {str(e)}")
                result[key] = value  # Keep original value on error

        return result

    def _validate_cpf(self, cpf: str) -> bool:
        """Validate a CPF number.

        Args:
            cpf: CPF number as string (digits only or formatted)

        Returns:
            bool: True if CPF is valid, False otherwise
        """
        # Remove non-digit characters
        cpf = re.sub(r'[^0-9]', '', cpf)

        # Check if it has 11 digits and not all digits are the same
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False

        # Calculate first verification digit
        sum_ = 0
        for i in range(9):
            sum_ += int(cpf[i]) * (10 - i)
        remainder = (sum_ * 10) % 11
        digit1 = 0 if remainder == 10 else remainder

        # Calculate second verification digit
        sum_ = 0
        for i in range(10):
            sum_ += int(cpf[i]) * (11 - i)
        remainder = (sum_ * 10) % 11
        digit2 = 0 if remainder == 10 else remainder

        # Check if calculated digits match the provided ones
        return int(cpf[9]) == digit1 and int(cpf[10]) == digit2

    def _validate_cnpj(self, cnpj: str) -> bool:
        """Validate a CNPJ number.

        Args:
            cnpj: CNPJ number as string (digits only or formatted)

        Returns:
            bool: True if CNPJ is valid, False otherwise
        """
        # Remove non-digit characters
        cnpj = re.sub(r'[^0-9]', '', cnpj)

        # Check if it has 14 digits and not all digits are the same
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False

        # Calculate first verification digit
        weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum_ = sum(int(cnpj[i]) * weights[i] for i in range(12))
        remainder = sum_ % 11
        digit1 = 0 if remainder < 2 else 11 - remainder

        # Calculate second verification digit
        weights.insert(0, 6)  # Add weight for the first verification digit
        sum_ = sum(int(cnpj[i]) * weights[i] for i in range(13))
        remainder = sum_ % 11
        digit2 = 0 if remainder < 2 else 11 - remainder

        # Check if calculated digits match the provided ones
        return int(cnpj[12]) == digit1 and int(cnpj[13]) == digit2

    def _process_document_numbers(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate CPF and CNPJ numbers in the record.

        Args:
            record: The record to process

        Returns:
            Dict: Processed record with invalid CPF/CNPJ numbers removed
        """
        if not isinstance(record, dict):
            return record

        # Process CPF in pessoa_fisica
        if 'pessoa_fisica' in record and 'cpf' in record['pessoa_fisica']:
            if isinstance(record['pessoa_fisica']['cpf'], list):
                valid_cpfs = [
                    cpf for cpf in record['pessoa_fisica']['cpf']
                    if cpf and self._validate_cpf(cpf)
                ]
                if valid_cpfs:
                    record['pessoa_fisica']['cpf'] = valid_cpfs
                else:
                    # Remove cpf field if no valid CPFs found
                    record['pessoa_fisica'].pop('cpf', None)
                    # Remove pessoa_fisica if it's now empty
                    if not record['pessoa_fisica']:
                        record.pop('pessoa_fisica', None)
            elif record['pessoa_fisica']['cpf'] is not None:
                if not self._validate_cpf(record['pessoa_fisica']['cpf']):
                    record['pessoa_fisica'].pop('cpf', None)
                    # Remove pessoa_fisica if it's now empty
                    if not record['pessoa_fisica']:
                        record.pop('pessoa_fisica', None)

        # Process CNPJ in pessoa_juridica
        if 'pessoa_juridica' in record and 'cnpj' in record['pessoa_juridica']:
            if isinstance(record['pessoa_juridica']['cnpj'], list):
                valid_cnpjs = [
                    cnpj for cnpj in record['pessoa_juridica']['cnpj']
                    if cnpj and self._validate_cnpj(cnpj)
                ]
                if valid_cnpjs:
                    record['pessoa_juridica']['cnpj'] = valid_cnpjs
                else:
                    # Remove cnpj field if no valid CNPJs found
                    record['pessoa_juridica'].pop('cnpj', None)
                    # Remove pessoa_juridica if it's now empty
                    if not record['pessoa_juridica']:
                        record.pop('pessoa_juridica', None)
            elif record['pessoa_juridica']['cnpj'] is not None:
                if not self._validate_cnpj(record['pessoa_juridica']['cnpj']):
                    record['pessoa_juridica'].pop('cnpj', None)
                    # Remove pessoa_juridica if it's now empty
                    if not record['pessoa_juridica']:
                        record.pop('pessoa_juridica', None)

        return record

    def _parse_json_message(self, message: Union[str, bytes, dict]) -> dict:
        """Parse incoming message to dictionary.

        Args:
            message: Input message (JSON string, bytes, or dict)

        Returns:
            dict: Parsed message as dictionary

        Raises:
            TypeError: If message type is not supported
            json.JSONDecodeError: If message is not valid JSON
        """
        self.logger.debug("Parsing incoming message")

        if isinstance(message, bytes):
            message = message.decode("utf-8")

        if isinstance(message, str):
            try:
                return json.loads(message)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON: {str(e)}")
                raise

        if isinstance(message, dict):
            return message

        raise TypeError(f"Unsupported message type: {type(message).__name__}")

    def _send_error(
            self,
            message: Any,
            error_msg: str,
            tb: Optional[str] = None,
            severity: str = "ERROR",
            service: Optional[str] = None,
            stage: Optional[str] = None,
            queue: Optional[str] = None
    ) -> None:
        """Send error message to error queue.

        Args:
            message: Original message that caused the error
            error_msg: Error message
            tb: Optional traceback
            severity: Error severity (default: "ERROR")
            service: Service name (auto-detected if None)
            stage: Stage name (auto-detected if None)
            queue: Target queue (defaults to error_queue if None)
        """
        try:
            # Infer service and stage if not provided
            if service is None or stage is None:
                frame = inspect.currentframe()
                if frame and frame.f_back:
                    frame = frame.f_back.f_back  # Get the caller's frame
                    if frame:
                        if service is None and 'self' in frame.f_locals:
                            service = frame.f_locals['self'].__class__.__name__
                        if stage is None and frame.f_code:
                            stage = frame.f_code.co_name

            timestamp_utc = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

            # Prepare error payload
            error_payload = {
                "timestamp": timestamp_utc,
                "service": service or "VerifierEsfinge",
                "stage": stage or "unknown",
                "severity": severity,
                "error": error_msg,
                "message": message if isinstance(message, (dict, str)) else str(message),
                "traceback": tb
            }

            # Publish to error queue
            target_queue = queue or self.error_queue
            if hasattr(self, 'queue_manager') and self.queue_manager:
                self.queue_manager.publish_message(
                    target_queue,
                    json.dumps(error_payload, ensure_ascii=False)
                )

            # Log the error
            log_msg = f"{severity}: {error_msg}"
            if tb:
                log_msg += f"\n{tb}"

            if severity == "ERROR":
                self.logger.error(log_msg)
            elif severity == "WARNING":
                self.logger.warning(log_msg)
            else:
                self.logger.info(log_msg)

        except Exception as e:
            # Fallback logging if error occurs in error handling
            self.logger.critical(f"Failed to send error: {str(e)}\nOriginal error: {error_msg}")
            if tb:
                self.logger.debug(f"Original traceback: {tb}")

    def _add_error(self, field: str, msg: str) -> None:
        """Add an error to the errors list.

        Args:
            field: Field name where the error occurred
            msg: Error message
        """
        self.errors.append({"field": field, "error": msg})
        self.logger.warning(f"Validation error in field '{field}': {msg}")

    # Verificações de Schema
    def _verify_schema(self, record: Dict[str, Any]):
        self.logger.info(" Checking Schemas ".center(84, "#"))

        required_tables = ["raw_data_id", "data_font"]
        for table in required_tables:
            if table not in record or not isinstance(record[table], dict):
                self._add_error(table, "Tabela obrigatória ausente")
                # se a tabela nem é dict, pare de checar campos dela
                continue

        # Campos obrigatórios mínimos no novo schema
        required_fields = {
            # processo_licitatorio: exige identificação mínima do processo
            "processo_licitatorio": ["numero_processo_licitatorio"],
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

        # tipo_especificacao_ug (se presente)
        tipo_espec_desc = record.get("tipo_especificacao_ug", {}).get("descricao")
        if tipo_espec_desc is not None:  # Verifica explicitamente por None
            try:
                # Tenta converter para inteiro primeiro
                tipo_espec_int = int(tipo_espec_desc)
                # Converte de volta para string para garantir o formato
                record["tipo_especificacao_ug"]["descricao"] = str(tipo_espec_int)
            except (ValueError, TypeError):
                # Se não for um número, mantém como string
                record["tipo_especificacao_ug"]["descricao"] = str(tipo_espec_desc).strip()

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

        # unidade_gestora (se presente)
        ug_cnpj = record.get("unidade_gestora", {}).get("cnpj")
        if ug_cnpj is not None:  # Verifica explicitamente por None
            try:
                # Tenta converter para inteiro primeiro
                ug_cnpj_int = int(ug_cnpj)
                # Converte de volta para string para garantir o formato
                record["unidade_gestora"]["cnpj"] = str(ug_cnpj_int)
            except (ValueError, TypeError):
                # Se não for um número, mantém como string
                record["unidade_gestora"]["cnpj"] = str(ug_cnpj).strip()

        # ---------- Booleans ----------
        # cotacao.vencedor
        if "cotacao" in record:
            vencedor_boolean = record.get("cotacao", {}).get("vencedor")
            if vencedor_boolean is not None:  # Verifica explicitamente por None
                try:
                    if vencedor_boolean == -1:
                        record["cotacao"]["vencedor"] = True
                    else:
                        record["cotacao"]["vencedor"] = False
                except (ValueError, TypeError):
                    self.logger.info(f"Field not found in record")

        # ---------- Formatos específicos (Brasil) ----------
        # CEP simples (00000-000 ou 8 dígitos)
        # cep = record.get("unidade_gestora", {}).get("cep")
        # if cep not in (None, "") and not re.match(r"^\d{5}-?\d{3}$", str(cep)):
        #    self._add_error("unidade_gestora.cep", "Invalid CEP format (expected 00000-000)")

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

    def _remove_null_fields(self, data: Any) -> Any:
        """Recursively remove null/empty fields from data.

        Args:
            data: Input data (dict, list, or other)

        Returns:
            Cleaned data with null/empty values removed
        """
        if isinstance(data, dict):
            return {
                k: v for k, v in
                ((k, self._remove_null_fields(v)) for k, v in data.items())
                if v not in (None, "", [], {}, ())
            }

        if isinstance(data, list):
            return [
                self._remove_null_fields(item)
                for item in data
                if item not in (None, "", [], {}, ())
            ]

        return data

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
        """
        Tenta converter para datetime.date aceitando múltiplos formatos.
        Exemplos aceitos:
        - '2024-01-23'
        - '2024-01-23 00:00:00'
        - '2024-01-23 00:00:00.000000'
        - datetime ou date nativo
        """
        if not s:
            return None
        if isinstance(s, date):
            return s
        try:
            # Usa dateutil, muito mais tolerante
            dt = parser.parse(str(s))
            return dt.date()
        except Exception:
            return None

    def _check_date_past_or_today(self, s: Any, field_path: str):
        """
        Valida se a data não é futura. Aceita formatos variados.
        """
        if s in (None, ""):
            return
        dt = self._parse_date(s)
        if not dt:
            self._add_error(field_path, "Invalid date format (expected YYYY-MM-DD or compatible)")
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

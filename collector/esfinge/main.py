"""Esfinge Collector - collects data from e-Sfinge CSV files in S3."""

import json
import math
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from big_table_creator import BigTableCreator
from s3_client import S3Client
from service_essentials.basic_service.cached_collector_service import CachedCollectorService
from service_essentials.exceptions.Error_Flow_exception import FlowError


class CollectorEsfinge(CachedCollectorService):
    """
    Collector for e-Sfinge data.
    
    - Processes entity_type specified in message
    - For processo_licitatorio: builds nested JSON with all related entities
    - For other entities: returns flat records from CSV
    - Adds root fields: raw_data_id, entity_type, data_source
    """

    DATA_SOURCE = "esfinge"

    def __init__(self):
        super().__init__(data_source=self.DATA_SOURCE)
        self.s3_client = S3Client(self.logger)

    def collect_data(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main entry point: collect data based on message.
        
        Args:
            message: Contains entity_type, year, bucket, data_path, etc.
            
        Returns:
            List of records with root fields added
        """
        try:
            entity_type = message.get("entity_type")
            if not entity_type:
                raise ValueError("entity_type not specified in message")

            self.s3_client.configure(message)

            if entity_type == "processo_licitatorio":
                records = self._collect_processo_licitatorio(message)
            else:
                records = self._collect_simple_entity(entity_type, message)

            if not records:
                self.logger.warning(f"No records found for {entity_type}")
                return []

            # Format all records for JSON output
            formatted = self._format_records(records)
            self.logger.info(f"Collected {len(formatted)} records for {entity_type}")
            return formatted

        except FlowError as e:
            self._log_error(message, str(e))
            return []
        except Exception as e:
            self._log_error(message, f"Unexpected error: {e}")
            return []

    def _collect_processo_licitatorio(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect processo_licitatorio with all nested relations."""
        self.logger.info("Processing processo_licitatorio with BigTableCreator")
        
        creator = BigTableCreator(self.s3_client, self.logger)
        records = creator.get_big_table(message)
        
        if not records:
            return []
        
        return records

    def _collect_simple_entity(self, entity_type: str, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect a simple entity (flat CSV)."""
        self.logger.info(f"Processing simple entity: {entity_type}")
        
        df = self.s3_client.load_csv(entity_type)
        if df is None or df.empty:
            return []

        # Add root fields
        df["raw_data_id"] = None
        df["entity_type"] = entity_type
        df["data_source"] = self.DATA_SOURCE

        return df.to_dict(orient="records")

    def _format_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format records for JSON output: clean keys, convert types."""
        return [self._format_record(r) for r in records]

    def _format_record(self, data: Any) -> Any:
        """
        Recursively format a record:
        - Clean key names (snake_case, remove '?')
        - Convert id_* fields to int
        - Convert other fields to string
        - Handle NaN/None/datetime
        """
        if data is None:
            return None

        if isinstance(data, float) and math.isnan(data):
            return None

        if isinstance(data, datetime):
            return data.strftime('%Y-%m-%d %H:%M:%S')

        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                clean_key = self._clean_key(key)
                clean_value = self._format_record(value)
                
                if clean_key.startswith('id'):
                    result[clean_key] = self._to_int_or_string(clean_value)
                elif isinstance(clean_value, (list, dict)):
                    result[clean_key] = clean_value
                elif clean_value is None:
                    result[clean_key] = None
                else:
                    result[clean_key] = self._to_string(clean_value)
            return result

        if isinstance(data, list):
            return [self._format_record(item) for item in data]

        if isinstance(data, str) and data.lower() in ('nan', 'none'):
            return None

        return data

    def _clean_key(self, key: str) -> str:
        """Clean a key to snake_case without special chars."""
        return key.lower().replace(' ', '_').replace('.', '_').replace('?', '').strip('_')

    def _to_int_or_string(self, value: Any) -> Any:
        """Convert value to int if possible, else string."""
        if value is None:
            return None
        try:
            float_val = float(value)
            if float_val == int(float_val):
                return int(float_val)
            return str(value)
        except (ValueError, TypeError):
            return str(value) if value is not None else None

    def _to_string(self, value: Any) -> Optional[str]:
        """Convert value to string, handling nan/none."""
        if value is None:
            return None
        str_val = str(value).strip()
        if str_val.lower() in ('nan', 'none'):
            return None
        return str_val

    def _log_error(self, message: Dict[str, Any], error_msg: str) -> None:
        """Log error and publish to error queue."""
        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        
        payload = {
            "timestamp": timestamp,
            "service": "CollectorEsfinge",
            "stage": "collect_data",
            "severity": "ERROR",
            "error": error_msg,
            "message": message if isinstance(message, dict) else str(message),
            "traceback": traceback.format_exc(),
        }

        self.logger.error(json.dumps(payload, ensure_ascii=False))
        
        if self.error_queue:
            try:
                self.queue_manager.publish_message(
                    self.error_queue, 
                    json.dumps(payload, ensure_ascii=False)
                )
            except Exception as e:
                self.logger.error(f"Failed to publish to error queue: {e}")


if __name__ == '__main__':
    title = " Collector Esfinge Started "
    print(title.center(60, "#"))
    collector = CollectorEsfinge()
    collector.logger.info(title.center(60, "#"))
    collector.start()

"""BigTableCreator for Esfinge Collector - builds nested JSON from CSVs.

Memory-optimized version with:
- Lazy loading: files loaded only when needed
- Pre-indexed lookups: join columns normalized once at load time
- Memory cleanup: dataframes cleared after processing
"""

import gc
import math
import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, Union

import pandas as pd


class BigTableCreator:
    """Builds nested JSON structure by joining multiple related CSV files."""

    # Small auxiliary files (loaded eagerly - low memory footprint)
    SMALL_AUX_FILES = [
        'situacao_processo_licitatorio',
        'modalidade_licitacao',
        'ente',
        'unidade_gestora',
        'tipo_cotacao',
        'tipo_licitacao',
        'tipo_objeto_licitacao'
    ]
    
    # Large data files (loaded lazily - high memory footprint)
    LARGE_DATA_FILES = [
        'item_licitacao',
        'participante_licitacao',
        'cotacao',
        'empenho',
        'liquidacao',
        'pagamento_empenho',
        'unidade_orcamentaria',
        'convidado_licitacao',
        'contrato',
    ]

    # Join relations: entity -> (main_table_column, entity_column)
    # If tuple, first is main table column, second is entity column
    # If string, same column name is used for both
    # Note: unidade_gestora and ente are handled specially in _build_record
    JOIN_KEYS = {
        'ente': 'id_ente',
        'tipo_licitacao': 'id_tipo_licitacao',
        'modalidade_licitacao': 'id_modalidade_licitacao',
        'situacao_processo_licitatorio': 'id_situacaoprocesso_licitatorio',
        'tipo_cotacao': 'id_tipo_cotacao',
        'tipo_objeto_licitacao': 'id_tipo_objeto_licitacao',
        'item_licitacao': 'id_procedimento_lictatorio',
        'participante_licitacao': 'id_procedimento_lictatorio',
        'convidado_licitacao': 'id_procedimento_lictatorio',
        'contrato': 'id_procedimento_lictatorio',
        'empenho': ('id_procedimento_lictatorio', 'id_processo_licitatorio'),
    }

    # Nested relations: parent -> {child: foreign_key_in_child}
    NESTED_RELATIONS = {
        'ente': {'unidade_gestora': 'id_ente'},
        'item_licitacao': {'cotacao': 'id_item_licitacao'},
        'participante_licitacao': {'cotacao': 'id_participante_licitacao_cotacao'},
        'empenho': [
            {'liquidacao': 'id_empenho'},
            {'pagamento_empenho': 'id_empenho'},
        ],
        'liquidacao': {'pagamento_empenho': 'id_liquidacao'},
        'unidade_orcamentaria': {'empenho': 'id_unidade_orcamentaria'},
    }

    def __init__(self, s3_client, logger):
        self.s3_client = s3_client
        self.logger = logger
        self._dataframes: Dict[str, pd.DataFrame] = {}
        self._indexes: Dict[str, Dict[str, List[int]]] = {}  # Pre-built indexes for fast lookups
        self._loaded_entities: Set[str] = set()  # Track which entities are loaded

    def get_big_table(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Main entry point: builds nested JSON for all processo_licitatorio records.
        
        Args:
            message: Configuration with date filters, bucket, etc.
            
        Returns:
            List of nested JSON records
        """
        try:
            # Load main table
            main_df = self._load_and_prepare('processo_licitatorio')
            if main_df is None or main_df.empty:
                self.logger.error("Failed to load processo_licitatorio")
                return []

            # Filter by date FIRST to minimize memory usage
            main_df = self._filter_by_date(main_df, message)
            if main_df.empty:
                self.logger.warning("No records after date filter")
                return []

            # Get all IDs we need to process
            target_ids = set(main_df['id_procedimento_lictatorio'].astype(str).str.replace(r'\.0$', '', regex=True))
            self.logger.info(f"Processing {len(target_ids)} processo_licitatorio records")

            # Load only small auxiliary files eagerly (low memory)
            self._load_small_aux_files()

            # Build nested JSON for each row (large files loaded lazily)
            results = []
            for _, row in main_df.iterrows():
                record = self._build_record(row, message, target_ids)
                record = self._clean_nans(record)
                results.append(record)

            self.logger.info(f"Built {len(results)} records")
            return results
        finally:
            # Always cleanup memory
            self._cleanup()

    def _load_and_prepare(self, entity: str) -> Optional[pd.DataFrame]:
        """Load CSV and normalize column names."""
        df = self.s3_client.load_csv(entity)
        if df is None or df.empty:
            return None
        return self._normalize_columns(df)

    def _load_small_aux_files(self) -> None:
        """Load only small auxiliary files (low memory footprint)."""
        for entity in self.SMALL_AUX_FILES:
            self._load_entity_with_index(entity)

    def _load_entity_with_index(self, entity: str) -> None:
        """Load entity and build index for fast lookups."""
        if entity in self._loaded_entities:
            return
            
        df = self._load_and_prepare(entity)
        if df is None or df.empty:
            self.logger.warning(f"Failed to load or empty: {entity}")
            return
            
        self._dataframes[entity] = df
        self._loaded_entities.add(entity)
        
        # Build index on join column for O(1) lookups
        join_spec = self.JOIN_KEYS.get(entity)
        if join_spec:
            col = join_spec[1] if isinstance(join_spec, tuple) else join_spec
            if col in df.columns:
                self._build_index(entity, col)
        
        # Special indexes for ente/unidade_gestora (handled specially in _build_record)
        if entity == 'unidade_gestora' and 'id_unidade_gestora' in df.columns:
            self._build_index(entity, 'id_unidade_gestora')
        if entity == 'ente' and 'id_ente' in df.columns:
            self._build_index(entity, 'id_ente')
        
        # Also build indexes for nested relation columns
        self._build_nested_indexes(entity, df)
        
        self.logger.info(f"Loaded {entity}: {len(df)} rows")

    def _build_nested_indexes(self, entity: str, df: pd.DataFrame) -> None:
        """Build indexes for columns used in nested relations."""
        # Find all columns used to join TO this entity
        for parent, relations in self.NESTED_RELATIONS.items():
            if isinstance(relations, list):
                for rel in relations:
                    for child, fk_col in rel.items():
                        if child == entity and fk_col in df.columns:
                            self._build_index(entity, fk_col)
            elif isinstance(relations, dict):
                for child, fk_col in relations.items():
                    if child == entity and fk_col in df.columns:
                        self._build_index(entity, fk_col)

    def _build_index(self, entity: str, column: str) -> None:
        """Build a lookup index for fast matching."""
        # Use composite key for multiple indexes per entity
        index_key = f"{entity}:{column}"
        if index_key in self._indexes:
            return  # Already built
            
        df = self._dataframes[entity]
        # Normalize values and group by them
        normalized = df[column].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        
        index = {}
        for idx, val in enumerate(normalized):
            if val not in index:
                index[val] = []
            index[val].append(idx)
        
        self._indexes[index_key] = index
        # Also store under entity name for backward compatibility with JOIN_KEYS lookup
        if entity not in self._indexes:
            self._indexes[entity] = index

    def _get_entity_lazy(self, entity: str) -> Optional[pd.DataFrame]:
        """Lazy load an entity only when needed."""
        if entity not in self._loaded_entities:
            self._load_entity_with_index(entity)
        return self._dataframes.get(entity)

    def _cleanup(self) -> None:
        """Release memory by clearing all cached data."""
        self._dataframes.clear()
        self._indexes.clear()
        self._loaded_entities.clear()
        gc.collect()
        self.logger.debug("Memory cleanup completed")

    def _build_record(self, row: pd.Series, message: Dict[str, Any], target_ids: Set[str]) -> Dict[str, Any]:
        """Build a complete nested record for one processo_licitatorio row."""
        record = {
            'raw_data_id': None,
            'entity_type': message.get('entity_type'),
            'data_source': 'esfinge',
            'processo_licitatorio': row.to_dict(),
        }

        processo = record['processo_licitatorio']

        # Special handling for ente/unidade_gestora (inverted nesting)
        # FK chain: processo_licitatorio -> unidade_gestora -> ente
        # Desired nesting: processo_licitatorio contains ente, ente contains unidade_gestora
        self._add_ente_with_unidade_gestora(row, processo)

        # Join all related entities (small files already loaded, large files lazy loaded)
        all_entities = self.SMALL_AUX_FILES + self.LARGE_DATA_FILES
        for entity in all_entities:
            if entity not in self.JOIN_KEYS:
                continue
            # Skip ente and unidade_gestora - handled specially above
            if entity in ('ente', 'unidade_gestora'):
                continue

            # Lazy load large files only when needed
            df = self._get_entity_lazy(entity)
            if df is None:
                continue

            related = self._find_related_rows_indexed(row, entity)
            if not related:
                continue

            # Add nested relations to each related row
            related_with_nested = []
            for item in related:
                item = self._add_nested_relations(entity, item)
                related_with_nested.append(item)

            processo[entity] = related_with_nested

        return record

    def _add_ente_with_unidade_gestora(self, row: pd.Series, processo: Dict[str, Any]) -> None:
        """
        Handle special ente/unidade_gestora nesting.
        FK chain: processo_licitatorio.id_unidade_gestora -> unidade_gestora.id_ente -> ente
        Result: processo_licitatorio.ente[] contains unidade_gestora[]
        """
        # Get unidade_gestora for this processo_licitatorio
        ug_df = self._get_entity_lazy('unidade_gestora')
        ente_df = self._get_entity_lazy('ente')
        
        if ug_df is None or ente_df is None:
            return
        
        # Get id_unidade_gestora from processo_licitatorio
        id_ug = row.get('id_unidade_gestora')
        if id_ug is None:
            return
        
        id_ug_str = str(id_ug).strip()
        if id_ug_str.endswith('.0'):
            id_ug_str = id_ug_str[:-2]
        
        # Find matching unidade_gestora
        if 'unidade_gestora' in self._indexes:
            ug_indices = self._indexes['unidade_gestora'].get(id_ug_str, [])
            if not ug_indices:
                return
            matched_ugs = ug_df.iloc[ug_indices].to_dict('records')
        else:
            return
        
        # Group unidade_gestoras by their ente
        entes_dict = {}  # id_ente -> {'ente_data': {...}, 'unidade_gestora': [...]}
        
        for ug in matched_ugs:
            id_ente = ug.get('id_ente')
            if id_ente is None:
                continue
            
            id_ente_str = str(id_ente).strip()
            if id_ente_str.endswith('.0'):
                id_ente_str = id_ente_str[:-2]
            
            if id_ente_str not in entes_dict:
                # Find ente data
                ente_data = None
                if 'ente' in self._indexes:
                    ente_indices = self._indexes['ente'].get(id_ente_str, [])
                    if ente_indices:
                        ente_data = ente_df.iloc[ente_indices[0]].to_dict()
                
                if ente_data:
                    entes_dict[id_ente_str] = {
                        **ente_data,
                        'unidade_gestora': []
                    }
            
            if id_ente_str in entes_dict:
                entes_dict[id_ente_str]['unidade_gestora'].append(ug)
        
        if entes_dict:
            processo['ente'] = list(entes_dict.values())

    def _find_related_rows_indexed(self, main_row: pd.Series, entity: str) -> List[Dict[str, Any]]:
        """Find rows using pre-built index for O(1) lookup."""
        join_spec = self.JOIN_KEYS.get(entity)
        if not join_spec:
            return []

        # Handle tuple (main_col, entity_col) or string (same column)
        if isinstance(join_spec, tuple):
            main_col, entity_col = join_spec
        else:
            main_col = entity_col = join_spec

        # Get join value from main row
        join_value = main_row.get(main_col)
        if join_value is None:
            return []

        # Normalize join value
        join_value_str = str(join_value).strip()
        if join_value_str.endswith('.0'):
            join_value_str = join_value_str[:-2]

        # Use pre-built index if available (O(1) lookup)
        if entity in self._indexes:
            row_indices = self._indexes[entity].get(join_value_str, [])
            if not row_indices:
                if entity in ('contrato', 'empenho'):
                    self.logger.debug(f"{entity}: no match for {entity_col}={join_value_str}")
                return []
            
            df = self._dataframes[entity]
            matched = df.iloc[row_indices]
            self.logger.debug(f"{entity}: found {len(matched)} rows for {main_col}={join_value_str}")
            return matched.to_dict('records')

        # Fallback to scan if no index (shouldn't happen)
        df = self._dataframes.get(entity)
        if df is None or entity_col not in df.columns:
            return []

        entity_vals = df[entity_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        mask = entity_vals == join_value_str
        matched = df[mask]

        if matched.empty:
            return []

        self.logger.debug(f"{entity}: found {len(matched)} rows for {main_col}={join_value_str}")
        return matched.to_dict('records')

    def _add_nested_relations(
        self, 
        parent_entity: str, 
        parent_row: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively add nested child entities to a parent row."""
        if parent_entity not in self.NESTED_RELATIONS:
            return parent_row

        relations = self.NESTED_RELATIONS[parent_entity]

        # Handle list of relations (e.g., empenho has multiple children)
        if isinstance(relations, list):
            for rel in relations:
                parent_row = self._add_nested_relations_single(parent_row, rel)
        else:
            parent_row = self._add_nested_relations_single(parent_row, relations)

        return parent_row

    def _add_nested_relations_single(
        self, 
        parent_row: Dict[str, Any], 
        relation: Dict[str, str]
    ) -> Dict[str, Any]:
        """Add a single nested relation to parent row."""
        for child_entity, fk_column in relation.items():
            # Lazy load child entity if not already loaded
            child_df = self._get_entity_lazy(child_entity)
            if child_df is None:
                continue
            
            # Get parent's FK value
            fk_value = parent_row.get(fk_column)
            if fk_value is None:
                continue

            fk_value_str = str(fk_value).strip()
            if fk_value_str.endswith('.0'):
                fk_value_str = fk_value_str[:-2]

            if fk_column not in child_df.columns:
                continue

            # Use index if available, otherwise scan
            index_key = f"{child_entity}:{fk_column}"
            if index_key in self._indexes:
                row_indices = self._indexes[index_key].get(fk_value_str, [])
                if not row_indices:
                    continue
                matched = child_df.iloc[row_indices]
            elif child_entity in self._indexes:
                row_indices = self._indexes[child_entity].get(fk_value_str, [])
                if not row_indices:
                    continue
                matched = child_df.iloc[row_indices]
            else:
                # Fallback to scan
                mask = child_df[fk_column].astype(str).str.strip().str.replace(r'\.0$', '', regex=True) == fk_value_str
                matched = child_df[mask]
                if matched.empty:
                    continue

            # Build nested list with recursive nesting
            nested = []
            for _, child_row in matched.iterrows():
                child_dict = child_row.to_dict()
                child_dict = self._add_nested_relations(child_entity, child_dict)
                nested.append(child_dict)

            parent_row[child_entity] = nested

        return parent_row

    def _filter_by_date(self, df: pd.DataFrame, message: Dict[str, Any]) -> pd.DataFrame:
        """Filter DataFrame by data_abertura_certame date."""
        date_column = 'data_abertura_certame'
        
        if date_column not in df.columns:
            self.logger.warning(f"Date column {date_column} not found")
            return df

        day = str(message.get('day', '01')).strip("[]\"'")
        month = str(message.get('month', '01')).strip("[]\"'")
        year = str(message.get('year', '2000')).strip("[]\"'")

        # Use ISO format for unambiguous date parsing (YYYY-MM-DD)
        target_date = f"{year}-{int(month):02d}-{int(day):02d}"

        try:
            df[date_column] = pd.to_datetime(df[date_column], dayfirst=True, errors='coerce')
            target_dt = pd.Timestamp(target_date)
            filtered = df[df[date_column] == target_dt]
            self.logger.info(f"Date filter: {len(filtered)} of {len(df)} records match {target_date}")
            return filtered
        except Exception as e:
            self.logger.error(f"Date filter error: {e}")
            return df

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to snake_case."""
        rename_map = {col: self._to_snake_case(col) for col in df.columns}
        return df.rename(columns=rename_map)

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        # Remove accents
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        # Insert underscore before capitals
        text = re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', '_', text)
        # Lowercase
        text = text.lower()
        # Replace non-alphanumeric (except ?) with underscore
        text = re.sub(r'[^a-z0-9?]+', '_', text)
        # Remove duplicate underscores
        text = re.sub(r'_+', '_', text)
        # Strip leading/trailing underscores
        return text.strip('_')

    def _clean_nans(self, obj: Any) -> Any:
        """Recursively remove NaN values from nested structure."""
        if isinstance(obj, dict):
            return {
                k: self._clean_nans(v) 
                for k, v in obj.items() 
                if self._clean_nans(v) is not None
            }
        elif isinstance(obj, list):
            return [
                self._clean_nans(item) 
                for item in obj 
                if self._clean_nans(item) is not None
            ]
        elif isinstance(obj, float) and math.isnan(obj):
            return None
        return obj

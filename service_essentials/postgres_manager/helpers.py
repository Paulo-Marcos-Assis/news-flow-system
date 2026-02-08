import datetime
import decimal
import uuid

def is_postgres_type(value, pg_type):
    pg_type = pg_type.lower()
    if pg_type in ('integer', 'smallint', 'bigint'):
        return isinstance(value, int)
    if pg_type in ('numeric', 'decimal'):
        return isinstance(value, decimal.Decimal)
    if pg_type in ('real', 'double precision', 'float'):
        return isinstance(value, float)
    if pg_type == 'boolean':
        return isinstance(value, bool)
    if pg_type in ('text', 'varchar', 'char', 'character varying', 'character'):
        return isinstance(value, str)
    if pg_type == 'date':
        return isinstance(value, datetime.date)
    if pg_type in ('timestamp', 'timestamp without time zone', 'timestamp with time zone', 'timestamptz'):
        return isinstance(value, datetime.datetime)
    if pg_type == 'time':
        return isinstance(value, datetime.time)
    if pg_type == 'bytea':
        return isinstance(value, bytes)
    if pg_type in ('json', 'jsonb'):
        return isinstance(value, (dict, list))
    if pg_type == 'uuid':
        return isinstance(value, uuid.UUID)
    if pg_type.endswith('[]'):
        return isinstance(value, list)
    return False


def coerce_postgres_type(value, pg_type):
    pg_type = pg_type.lower()

    try:
        if pg_type in ('integer', 'smallint', 'bigint'):
            return int(value)
        if pg_type in ('numeric', 'decimal'):
            return decimal.Decimal(value)
        if pg_type in ('real', 'double precision', 'float'):
            return float(value)
        if pg_type == 'boolean':
            if isinstance(value, str):
                return value.lower() in ('true', 't', '1', 'yes', 'y', 'sim')
            return bool(value)
        if pg_type in ('text', 'varchar', 'char', 'character varying', 'character'):
            return str(value)
        if pg_type == 'date' and isinstance(value, str):
            datetime.date.fromisoformat(value) 
            return value 
        if pg_type in ('timestamp', 'timestamp without time zone', 'timestamp with time zone', 'timestamptz') and isinstance(value, str):
            datetime.datetime.fromisoformat(value)  # levanta erro se for inválida
            return value
        if pg_type == 'time':
            datetime.time.fromisoformat(value)
            return value
        if pg_type == 'bytea':
            if isinstance(value, str):
                return value.encode()
            return bytes(value)
        if pg_type in ('json', 'jsonb'):
            import json
            if isinstance(value, str):
                return json.loads(value)
            return value
        if pg_type == 'uuid':
            return uuid.UUID(str(value))
        if pg_type.endswith('[]'):
            if not isinstance(value, list):
                return [value]
            return value
    except Exception:
        pass  # Se a conversão falhar, deixa cair para o retorno original

    return False

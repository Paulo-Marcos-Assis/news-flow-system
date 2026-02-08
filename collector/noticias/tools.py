from datetime import datetime
from service_essentials.utils.logger import Logger  
logger = Logger(log_to_console=True)

# ==============================================================================
# FUNÇÕES AUXILIARES DE PARSING DE DATA
# ==============================================================================

def parse_iso_or_portuguese_date(date_str):
    """
    Analisa datas em formato ISO 8601 ou em português (ex: '24 jul 2025 às 14h38').
    Retorna um objeto de data.
    """
    if not date_str:
        return None
    try:
        # Formato ISO com fuso horário (ex: "2025-07-24T14:38:34-03:00")
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        
        # Formato em português (ex: "24 jul 2025 às 14h38")
        months_pt = {
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
        }
        date_part = date_str.split(' às ')[0]
        parts = date_part.split()
        if len(parts) == 3:
            day, month_pt, year = parts
            month = months_pt.get(month_pt.lower())
            if month:
                return datetime(int(year), month, int(day)).date()
    except Exception as e:
        logger.warning(f"Falha ao analisar a data '{date_str}': {e}")
    return None

def parse_dmy_format(date_str):
    """
    Analisa datas no formato DD/MM/YYYY.
    Retorna um objeto de data.
    """
    if not date_str:
        return None
    try:
        # Formato "DD/MM/YYYY - HH:MM"
        date_only = date_str.split(' - ')[0].strip()
        return datetime.strptime(date_only, '%d/%m/%Y').date()
    except Exception as e:
        logger.warning(f"Falha ao analisar a data '{date_str}': {e}")
    return None

def parse_other_format(date_str):
    """
    Analisa datas no formato 'DD/MM/YYYY às HH:MM'.
    Retorna um objeto de data.
    """
    if not date_str:
        return None
    try:
        # Formato "DD/MM/YYYY às HH:MM"
        strip_date = date_str.split("Atualizada")[0].strip()
        dt = datetime.strptime(strip_date, "%d/%m/%Y às %Hh%M")
        only_date = dt.date()
        return only_date
    except Exception as e:
        logger.warning(f"Falha ao analisar a data '{date_str}': {e}")
    return None
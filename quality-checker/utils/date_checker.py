from abc import ABC

from checkers.base_quali_checker import BaseQualiChecker
from dateutil import parser, tz
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Maximum number of years allowed in the future (specially for contracts)
MAX_FUTURE_YEARS = 60


class DateChecker(BaseQualiChecker, ABC):

    def date_parse(self, date_str: str):
        if date_str is None:
            return None

        common_formats = [
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in common_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                dt = dt.replace(tzinfo=tz.tzlocal())
                return dt.astimezone(tz.UTC)
            except (ValueError, TypeError):
                pass

        try:
            dt = parser.parse(date_str, dayfirst=True)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=tz.tzlocal())
            return dt.astimezone(tz.UTC)
        except (ValueError, TypeError):
            return None

    def period_check(self, begin_date: str, end_date: str, test_date: str) -> bool:
        begin_date = self.date_parse(begin_date)
        end_date = self.date_parse(end_date)
        test_date = self.date_parse(test_date)

        if not all([begin_date, end_date, test_date]):
            return False

        return begin_date <= test_date <= end_date

    def is_valid_date(self, date_str: str, allow_future_date: bool = False, max_future_years: int = None, reference_date: str = None) -> bool:
        parsed = self.date_parse(date_str)
        if parsed is None:
            return False

        if reference_date is not None:
            ref_date = self.date_parse(reference_date)
            if ref_date is None:
                return False
        else:
            ref_date = datetime.now(tz=tz.UTC)

        if not allow_future_date and parsed >= ref_date:
            return False

        if allow_future_date and max_future_years is not None:
            max_future_date = ref_date + relativedelta(years=max_future_years)
            if parsed > max_future_date:
                return False

        return True
            
    def return_str_date(self, date_str: str, date_format: str = "date", allow_future_date: bool = False, max_future_years: int = None, reference_date: str = None):
        parsed = self.date_parse(date_str)
        if parsed is None:
            return None

        if reference_date is not None:
            ref_date = self.date_parse(reference_date)
            if ref_date is None:
                return None
        else:
            ref_date = datetime.now(tz=tz.UTC)

        oldest_valid_date = datetime(1970, 1, 1, tzinfo=tz.UTC)
        if parsed <= oldest_valid_date or (not allow_future_date and parsed >= ref_date):
            return None

        if allow_future_date and max_future_years is not None:
            max_future_date = ref_date + relativedelta(years=max_future_years)
            if parsed > max_future_date:
                return None

        if date_format == "date":
            return parsed.date().isoformat()
        if date_format == "timestamp":
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        
        return None

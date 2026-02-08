from .base_quali_checker import BaseQualiChecker


class BaseNestedChecker(BaseQualiChecker):
    
    def __init__(self, logger, checkers = None):
        super().__init__(logger)
        self.checkers = checkers or {}

    def check(self, record):

        parent_data = record.get(self.table_name, {})

        nested_items = parent_data.get(self.check_name, [])

        if not nested_items:
            return True, None
        
        # Wrap single object in a list for consistent processing
        was_list = isinstance(nested_items, list)
        if not was_list:
            nested_items = [nested_items]
        
        nested_checkers = self.checkers.get(self.check_name, [])

        self.logger.info(f"[NESTED] {self.table_name} -> {self.check_name}: {len(nested_items)} items, {len(nested_checkers) if nested_checkers else 0} checkers")

        if not nested_checkers:
            self.logger.warning(f"No checkers found for scope: {self.check_name}")
            return True, None
        
        results = []
        for index, item in enumerate(nested_items):
            temp_record = {
                self.check_name: item,
                self.table_name: parent_data
                }

            for checker_name, checkers in nested_checkers.items():
                try:
                    result = checkers.check(temp_record)
                    if not isinstance(result, list):
                        result = [result]

                    for checker_result in result:
                        checked, msg = checker_result
                        results.append((checked, msg))
                except Exception as e:
                    self.logger.warning(f"Error checking {checker_name} from nested {self.check_name}: {e}")

            # Update the original item with changes from the checker
            nested_items[index] = temp_record[self.check_name]

        # Write back to parent_data (handles both list and non-list cases)
        parent_data[self.check_name] = nested_items if was_list else nested_items[0]

        return results

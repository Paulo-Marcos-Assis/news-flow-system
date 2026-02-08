import logging

def clean_description(description: str) -> str:
    """
    Cleans a single description string by converting it to lowercase.
    """
    logging.info(f"Cleaning description: '{description}'")
    if not isinstance(description, str):
        logging.warning(f"Input to clean_description is not a string: {description}")
        return ""
    cleaned_description = description.lower()
    logging.info(f"Cleaned description: '{cleaned_description}'")
    return cleaned_description
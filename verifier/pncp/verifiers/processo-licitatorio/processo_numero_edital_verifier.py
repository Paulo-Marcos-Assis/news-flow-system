from verifiers.base_verifier import BaseVerifier

class ProcessoNumeroEditalVerifier(BaseVerifier):
    """Verifier for the 'numero_edital' destination field."""
    destination_field = "numero_edital"
    destination_table = "processo_licitatorio"

    def verify(self, data):
        # The verifier receives the processed data, so it checks 'numero_edital'.
        numero_edital = data.get(self.destination_table, {}).get(self.destination_field, None)

        # This is the only non-nullable field.
        if not numero_edital:
            return False, "Field 'numero_edital' is missing or empty."

        if not isinstance(numero_edital, str):
            return False, f"Field 'numero_edital' must be a string, but got {type(numero_edital).__name__}."

        # Validate the format by checking the suffix, allowing for '/' in the main body.
        if len(numero_edital) < 6:  # Must be at least 'a/YYYY'
            return False, f"Field 'numero_edital' ('{numero_edital}') is too short to be valid."

        year_part = numero_edital[-4:]
        slash_part = numero_edital[-5]

        if not (slash_part == '/' and year_part.isdigit()):
            return False, f"The suffix of 'numero_edital' ('{numero_edital[-5:]}') does not match the expected '/YYYY' format."

        return True, None

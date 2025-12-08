"""Custom exceptions för menprövningsverktyget."""


class MenprovningError(Exception):
    """Bas-exception för alla menprövningsfel."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ExtractionError(MenprovningError):
    """Fel vid dokumentextraktion."""

    pass


class NERError(MenprovningError):
    """Fel vid Named Entity Recognition."""

    pass


class ClassificationError(MenprovningError):
    """Fel vid känslighetskategorisering."""

    pass


class LLMError(MenprovningError):
    """Fel vid LLM-kommunikation."""

    pass


class ValidationError(MenprovningError):
    """Fel vid datavalidering."""

    pass


class ConfigurationError(MenprovningError):
    """Fel i konfiguration."""

    pass


class RuleEngineError(MenprovningError):
    """Fel i regelmotor."""

    pass

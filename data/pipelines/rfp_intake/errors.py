"""RFP intake failures. Messages stay free of document text and connection strings."""


class RfpDatabaseUnconfigured(RuntimeError):
    """No Postgres URL is configured for RFP tickets."""


class RfpStorageError(RuntimeError):
    """The ticket store could not be read or written."""


class UploadRejected(ValueError):
    """The upload is not an acceptable PDF. ``code`` is a fixed token."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ConversionError(RuntimeError):
    """MarkItDown could not turn the PDF into text."""


class ModelUnavailable(RuntimeError):
    """The language model could not be reached or did not return JSON."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)

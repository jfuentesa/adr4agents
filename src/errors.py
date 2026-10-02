class ApplicationError(Exception):
    def __init__(self, message, status=400, code="validation_error", field=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.field = field


def not_found(resource):
    return ApplicationError(f"{resource} not found.", 404, "not_found")


def conflict(message):
    return ApplicationError(message, 409, "conflict")

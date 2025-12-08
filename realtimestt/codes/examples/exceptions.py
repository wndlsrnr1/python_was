"""
실시간 STT Consumer 전용 예외 계층
"""


class RealtimeSTTError(Exception):
    """실시간 STT Consumer 기본 예외"""
    code: str
    status_code: int
    detail: str

    def __init__(self, detail: str, code: str | None = None, status_code: int = 500):
        self.detail = detail
        self.code = code or self.__class__.__name__
        self.status_code = status_code
        super().__init__(self.detail)


class RealtimeSTTValidationError(RealtimeSTTError):
    """검증 오류 (400)"""
    def __init__(self, detail: str):
        super().__init__(detail, status_code=400)


class RealtimeSTTAuthenticationError(RealtimeSTTError):
    """인증 오류 (401)"""
    def __init__(self, detail: str):
        super().__init__(detail, status_code=401)


class RealtimeSTTNotFoundError(RealtimeSTTError):
    """리소스 없음 오류 (404)"""
    def __init__(self, detail: str):
        super().__init__(detail, status_code=404)


class RealtimeSTTConfigurationError(RealtimeSTTError):
    """설정 오류 (500)"""
    def __init__(self, detail: str):
        super().__init__(detail, status_code=500)


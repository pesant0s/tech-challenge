from fastapi import HTTPException, status

class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Recurso não encontrado"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ConflictException(HTTPException):
    def __init__(self, detail: str = "Conflito de dados"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

class BusinessRuleException(HTTPException):
    def __init__(self, detail: str = "Regra de negócio violada"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

from enum import Enum

class LLMEnums(Enum):
    GEMINI = "GEMINI"


class GeminiEnums(Enum):
    #SYSTEM = "system"
    USER = "user"
    ASSISTANT = "model"
    DOCUMENT = "retrieval_document"
    QUERY = "retrieval_query"

class DocumentTypeEnum(Enum):
    DOCUMENT = "document"
    QUERY = "query"
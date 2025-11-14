from enum import Enum

class LLMEnums(Enum):
    GEMINI = "GEMINI"
    COHERE = "COHERE"


class GeminiEnums(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "model"
    DOCUMENT = "retrieval_document"
    QUERY = "retrieval_query"

class CoHereEnums(Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    ASSISTANT = "CHATBOT"

    DOCUMENT = "search_document"
    QUERY = "search_query"
    
class DocumentTypeEnum(Enum):
    DOCUMENT = "document"
    QUERY = "query"
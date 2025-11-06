from enum import Enum

class ResponseSignal(Enum):

    FILE_VALIDATION_SUCCESS = "File validation successful"
    FILE_TYPE_NOT_SUPPORTED = "File type is not supported"
    FILE_SIZE_EXCEEDED = "File size exceeded the limit"
    FILE_UPLOAD_SUCCESS = "File uploaded successfully"
    FILE_UPLOAD_FAILED = "File upload failed"
    PROCESSING_SUCCESS = "File processing successful"
    PROCESSING_FAILED = "File processing failed"
    NO_FILES_ERROR = "not_found_files"
    FILE_ID_ERROR = "no_file_found_with_this_id"
from .BaseController import BaseController
from fastapi import FastAPI, APIRouter,Depends, UploadFile
from models import ResponseSignal

class DataController(BaseController):
    
    def __init__(self):
        super().__init__()
    
    # validate the file properities
    def validate_file_properties(self, file: UploadFile):
        
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False , ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.app_settings.FILE_MAX_SIZE:
            return False , ResponseSignal.FILE_SIZE_EXCEEDED.value

        return True , ResponseSignal.FILE_VALIDATION_SUCCESS.value
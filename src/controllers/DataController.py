from .BaseController import BaseController
from fastapi import FastAPI, APIRouter,Depends, UploadFile

class DataController(BaseController):
    
    def __init__(self):
        super().__init__()
    
    # validate the file properities
    def validate_file_properties(self, file: UploadFile):
        
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False , "File size is not supported"

        if file.size > self.app_settings.FILE_MAX_SIZE:
            return False , "File size exceeded the limit"

        return True ,"success"
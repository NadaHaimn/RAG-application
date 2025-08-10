from .ProjectController import ProjectController
from .BaseController import BaseController
from fastapi import FastAPI, APIRouter,Depends, UploadFile
from models import ResponseSignal
import os
import re

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

    
    def generate_unique_filename(self , orig_file_name: str , project_id: str):

        random_key = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)
        cleaned_file_name = self.get_clean_file_name(
            orig_file_name=orig_file_name
        )

        # Create a unique file name by combining the cleaned file name with a random string
        new_file_name = os.path.join(
            project_path, 
            f"{random_key}_{cleaned_file_name}"
        )

        while os.path.exists(new_file_name):
            random_key = self.generate_random_string()
            new_file_name = os.path.join(
                project_path, 
                f"{random_key}_{cleaned_file_name}"
            )

        return new_file_name


    def get_clean_file_name(self, orig_file_name: str):
        # Remove any special characters except for dot and underscore
        cleaned_file_name = re.sub(r'[^\w.]','', orig_file_name.strip())

        # replace spaces with underscores
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        return cleaned_file_name

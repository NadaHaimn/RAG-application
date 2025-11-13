from ..LLMInterface import LLMInterface
from ..LLMEnums import GeminiEnums, DocumentTypeEnum
import google.generativeai as genai
import logging

class GeminiProvider(LLMInterface):
    
    def __init__(self, api_key: str, 
            default_input_max_characters: int = 4000,
            default_generation_max_output_tokens: int = 2000,
            default_generation_temperature: float = 0.7):
        
        self.api_key = api_key
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature
        
        self.generation_model_id = None
        self.embedding_model_id = None
        self.embedding_size = None
        
        # تكوين عميل Gemini
        genai.configure(api_key=self.api_key)
        self.client = genai
        self.logger = logging.getLogger(__name__)
    
    def set_generation_model(self, model_id: str):
        """تعيين نموذج توليد النص"""
        self.generation_model_id = model_id
    
    def set_embedding_model(self, model_id: str, embedding_size: int):
        """تعيين نموذج التضمين"""
        self.embedding_model_id = model_id
        self.embedding_size = embedding_size
    
    def process_text(self, text: str):
        """معالجة النص واقتصاصه للحد الأقصى"""
        return text[:self.default_input_max_characters].strip()
    
    def generate_text(self, prompt: str, chat_history: list = [], max_output_tokens: int = None,
                      temperature: float = None):
        """توليد النص باستخدام Gemini"""
        
        if not self.client:
            self.logger.error("Gemini client was not set")
            return None
        
        if not self.generation_model_id:
            self.logger.error("Generation model for Gemini was not set")
            return None
        
        # استخدام القيم الافتراضية إذا لم يتم توفيرها
        max_output_tokens = max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature = temperature if temperature else self.default_generation_temperature
        
        try:
            # تهيئة النموذج
            model = self.client.GenerativeModel(self.generation_model_id)
            
            # تكوين إعدادات التوليد
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature
            )
            
            # إذا كان هناك تاريخ محادثة، نقوم بتحويله لتنسيق Gemini
            if chat_history:
                gemini_messages = []
                for msg in chat_history:
                    # تحويل الأدوار من تنسيق النظام إلى تنسيق Gemini
                    if msg.get("role") == GeminiEnums.USER.value:
                        role = GeminiEnums.USER.value
                    else:
                        role = GeminiEnums.MODEL.value
                    
                    content = msg.get("content") or msg.get("text") or ""
                    if content.strip():  # نتأكد أن المحتوى ليس فارغاً
                        gemini_messages.append({"role": role, "parts": [content]})
                
                # بدء محادثة مع التاريخ
                chat = model.start_chat(history=gemini_messages)
                response = chat.send_message(
                    self.process_text(prompt),
                    generation_config=generation_config
                )
            else:
                # محادثة جديدة بدون تاريخ
                response = model.generate_content(
                    self.process_text(prompt),
                    generation_config=generation_config
                )
            
            if not response or not response.text:
                self.logger.error("Error while generating text with Gemini")
                return None
            
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error in Gemini generate_text: {str(e)}")
            return None
    
    def embed_text(self, text: str, document_type: str = None):
        """إنشاء تضمين النص باستخدام Gemini"""
        if not self.client:
            self.logger.error("Gemini client was not set")
            return None
        
        if not self.embedding_model_id:
            self.logger.error("Embedding model for Gemini was not set")
            return None
        
        try:
            # معالجة النص
            processed_text = self.process_text(text)
            
            # تحديد نوع المهمة للتضمين
            task_type = GeminiEnums.DOCUMENT.value
            if document_type == DocumentTypeEnum.QUERY.value:
                task_type = GeminiEnums.QUERY.value
            
            # إنشاء التضمين
            result = self.client.embed_content(
                model=self.embedding_model_id,
                content=processed_text,
                task_type=task_type
            )
            
            if not result or not result.embedding:
                self.logger.error("Error while embedding text with Gemini")
                return None
            
            return result.embedding
            
        except Exception as e:
            self.logger.error(f"Error in Gemini embed_text: {str(e)}")
            return None
    
    def construct_prompt(self, prompt: str, role: str):
        """بناء رسالة بتنسيق Gemini"""
        # تحويل الأدوار من تنسيق النظام إلى تنسيق Gemini
        if role == GeminiEnums.MODEL.value:
            gemini_role = GeminiEnums.MODEL.value
        else:
            gemini_role = GeminiEnums.USER.value
        
        return {
            "role": gemini_role,
            "content": self.process_text(prompt)
        }
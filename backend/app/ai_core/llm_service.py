from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from typing import List, Dict, Optional
import asyncio


class LocalLLMService:
    """Сервис для работы с локальными нейросетями"""
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipe = None
        self.llm = None
        self.is_loaded = False
    
    async def load_model(self):
        """Загрузка модели (асинхронно)"""
        if self.is_loaded:
            return
        
        try:
            # Проверка доступности CUDA
            device = 0 if torch.cuda.is_available() else -1
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if device >= 0 else torch.float32,
                device_map="auto" if device >= 0 else None,
                load_in_8bit=device >= 0  # Квантование для экономии памяти
            )
            
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.1,
                do_sample=True,
            )
            
            self.llm = HuggingFacePipeline(pipeline=self.pipe)
            self.is_loaded = True
        except Exception as e:
            print(f"Error loading model: {e}")
            self.is_loaded = False
    
    async def analyze_document(self, document_text: str, check_type: str, ntd_context: str = "") -> Dict:
        """Анализ документа с использованием локальной модели"""
        if not self.is_loaded:
            await self.load_model()
        
        if not self.is_loaded:
            return {
                "status": "error",
                "message": "Модель не загружена. Требуется больше ресурсов или проверьте наличие модели."
            }
        
        prompt_template = PromptTemplate(
            input_variables=["document", "check_type", "ntd"],
            template="""Ты эксперт по рабочей документации на строительство инженерных систем в РФ.

Правила проверки:
1. Если не хватает исходных данных не надо ничего придумывать. Нужно запросить недостающую информацию.
2. Если какие-либо проверки документации не проводились, то сообщить об этом и указать, что не проведено и по какой причине.
3. Не надо ничего придумывать нужно давать ответ как есть.

Тип проверки: {check_type}

Нормативные документы:
{ntd}

Документ для проверки:
{document}

Выполни проверку и предоставь результат в формате JSON:
{{
    "status": "passed/failed/skipped",
    "severity": "critical/non_critical/info",
    "message": "описание результата",
    "ntd_reference": "ссылка на пункт НТД",
    "details": "детали проверки"
}}
"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: chain.run(document=document_text, check_type=check_type, ntd=ntd_context)
            )
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class CloudLLMService:
    """Сервис для работы с облачными нейросетями (бесплатные API)"""
    
    def __init__(self):
        # Используем бесплатные модели через Hugging Face Inference API
        self.api_endpoints = {
            "qwen": "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-1.5B-Instruct",
            "mistral": "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
            "phi": "https://api-inference.huggingface.co/models/microsoft/phi-2"
        }
        self.selected_model = "qwen"
    
    async def analyze_document(self, document_text: str, check_type: str, ntd_context: str = "", api_key: str = "") -> Dict:
        """Анализ документа с использованием облачной модели"""
        import httpx
        
        prompt = f"""Ты эксперт по рабочей документации на строительство инженерных систем в РФ.

Правила проверки:
1. Если не хватает исходных данных не надо ничего придумывать. Нужно запросить недостающую информацию.
2. Если какие-либо проверки документации не проводились, то сообщить об этом и указать, что не проведено и по какой причине.
3. Не надо ничего придумывать нужно давать ответ как есть.

Тип проверки: {check_type}

Нормативные документы: {ntd_context}

Документ для проверки: {document_text}

Выполни проверку и предоставь результат."""

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 1024,
                "temperature": 0.7,
                "top_p": 0.95
            }
        }
        
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_endpoints[self.selected_model],
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {"status": "success", "result": result}
                else:
                    return {
                        "status": "error",
                        "message": f"API error: {response.status_code} - {response.text}"
                    }
        except Exception as e:
            return {"status": "error", "message": str(e)}


class HybridLLMService:
    """Гибридный сервис - сначала пробует локальную, затем облачную"""
    
    def __init__(self):
        self.local_service = LocalLLMService()
        self.cloud_service = CloudLLMService()
    
    async def analyze_document(self, document_text: str, check_type: str, ntd_context: str = "", api_key: str = "") -> Dict:
        """Анализ документа с гибридным подходом"""
        # Пробуем локальную модель
        local_result = await self.local_service.analyze_document(document_text, check_type, ntd_context)
        
        if local_result.get("status") == "success":
            return local_result
        
        # Если локальная не работает, используем облачную
        return await self.cloud_service.analyze_document(document_text, check_type, ntd_context, api_key)


# Фабрика для создания сервисов
def get_llm_service(mode: str, model_name: str = ""):
    """Фабричный метод для получения сервиса"""
    if mode == "local":
        return LocalLLMService(model_name)
    elif mode == "cloud":
        return CloudLLMService()
    elif mode == "hybrid":
        return HybridLLMService()
    else:
        return LocalLLMService(model_name)

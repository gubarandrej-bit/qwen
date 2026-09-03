import pdfplumber
from docx import Document
import openpyxl
import ezdxf
from typing import Dict, List, Optional
import os


class DocumentParser:
    """Сервис для парсинга различных форматов документов"""
    
    @staticmethod
    async def parse_pdf(file_path: str) -> str:
        """Извлечение текста из PDF"""
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            return f"Error parsing PDF: {str(e)}"
        return text
    
    @staticmethod
    async def parse_docx(file_path: str) -> str:
        """Извлечение текста из DOCX"""
        text = ""
        try:
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            # Извлечение текста из таблиц
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text for cell in row.cells]
                    text += " | ".join(row_text) + "\n"
        except Exception as e:
            return f"Error parsing DOCX: {str(e)}"
        return text
    
    @staticmethod
    async def parse_xlsx(file_path: str) -> Dict[str, List[List]]:
        """Извлечение данных из XLSX"""
        data = {}
        try:
            wb = openpyxl.load_workbook(file_path)
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                sheet_data = []
                for row in sheet.iter_rows(values_only=True):
                    sheet_data.append(list(row))
                data[sheet_name] = sheet_data
        except Exception as e:
            return {"error": [f"Error parsing XLSX: {str(e)}"]}
        return data
    
    @staticmethod
    async def parse_dxf(file_path: str) -> Dict:
        """Извлечение данных из DXF (DWG конвертируется в DXF)"""
        data = {
            "layers": [],
            "entities": [],
            "blocks": []
        }
        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            
            # Слои
            for layer in doc.layers:
                data["layers"].append({
                    "name": layer.dxf.name,
                    "color": layer.dxf.color
                })
            
            # Объекты
            for entity in msp:
                entity_data = {
                    "type": entity.dxftype(),
                    "layer": entity.dxf.layer
                }
                # Попытка извлечь координаты
                if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'insert'):
                    entity_data['position'] = str(entity.dxf.insert)
                data["entities"].append(entity_data)
            
            # Блоки
            for block in doc.blocks:
                data["blocks"].append(block.name)
                
        except Exception as e:
            return {"error": f"Error parsing DXF: {str(e)}"}
        return data
    
    @staticmethod
    async def parse_file(file_path: str) -> Dict:
        """Универсальный парсер файлов"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            text = await DocumentParser.parse_pdf(file_path)
            return {"type": "text", "content": text}
        elif ext in ['.doc', '.docx']:
            text = await DocumentParser.parse_docx(file_path)
            return {"type": "text", "content": text}
        elif ext in ['.xls', '.xlsx']:
            data = await DocumentParser.parse_xlsx(file_path)
            return {"type": "spreadsheet", "content": data}
        elif ext in ['.dxf', '.dwg']:
            data = await DocumentParser.parse_dxf(file_path)
            return {"type": "cad", "content": data}
        else:
            return {"type": "unknown", "content": f"Unsupported file type: {ext}"}


class CableJournalParser:
    """Парсер кабельных журналов"""
    
    @staticmethod
    async def parse_cable_journal(data: Dict) -> List[Dict]:
        """Извлечение данных из кабельного журнала"""
        cables = []
        
        # Предполагаем стандартную структуру кабельного журнала
        # Марка кабеля, Количество, Длина, Трасса
        for sheet_name, rows in data.items():
            if not rows:
                continue
            
            # Пропускаем заголовок
            for row in rows[1:]:
                if len(row) >= 4 and row[0]:
                    cable = {
                        "mark": str(row[0]) if row[0] else "",
                        "quantity": int(row[1]) if row[1] else 1,
                        "length": float(row[2]) if row[2] else 0,
                        "route": str(row[3]) if len(row) > 3 and row[3] else "",
                        "source_sheet": sheet_name
                    }
                    cables.append(cable)
        
        return cables


class SpecificationParser:
    """Парсер спецификаций оборудования"""
    
    @staticmethod
    async def parse_specification(data: Dict) -> List[Dict]:
        """Извлечение данных из спецификации"""
        equipment = []
        
        for sheet_name, rows in data.items():
            if not rows:
                continue
            
            # Пропускаем заголовок
            for row in rows[1:]:
                if len(row) >= 3 and row[0]:
                    item = {
                        "name": str(row[0]) if row[0] else "",
                        "type": str(row[1]) if len(row) > 1 and row[1] else "",
                        "quantity": int(row[2]) if len(row) > 2 and row[2] else 1,
                        "unit": str(row[3]) if len(row) > 3 and row[3] else "шт",
                        "notes": str(row[4]) if len(row) > 4 and row[4] else "",
                        "source_sheet": sheet_name
                    }
                    equipment.append(item)
        
        return equipment

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openpyxl import Workbook
from datetime import datetime
from typing import List, Dict
import os


class ReportGenerator:
    """Генератор отчетов в форматах DOC и XLS"""
    
    @staticmethod
    def generate_doc_report(check_info: Dict, results: List[Dict], ntd_docs: List[Dict], output_path: str) -> str:
        """Генерация отчета в формате DOCX"""
        doc = Document()
        
        # Заголовок
        heading = doc.add_heading('ОТЧЕТ О ПРОВЕРКЕ ДОКУМЕНТАЦИИ', 0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Информация о проверке
        doc.add_heading('1. Общая информация', level=1)
        table = doc.add_table(rows=6, cols=2)
        table.style = 'Table Grid'
        
        info_data = [
            ('Наименование проверки:', check_info.get('name', '')),
            ('Инженерная система:', check_info.get('engineering_system', '')),
            ('Режим работы:', check_info.get('mode', '')),
            ('Модель ИИ:', check_info.get('ai_model', '')),
            ('Дата проведения:', datetime.now().strftime('%Y-%m-%d %H:%M')),
            ('Статус:', check_info.get('status', ''))
        ]
        
        for i, (label, value) in enumerate(info_data):
            table.rows[i].cells[0].text = label
            table.rows[i].cells[1].text = str(value)
        
        # Критические замечания
        doc.add_heading('2. Критические замечания', level=1)
        critical_issues = [r for r in results if r.get('severity') == 'critical']
        if critical_issues:
            for issue in critical_issues:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(f"[{issue.get('check_type', '')}] {issue.get('message', '')}")
                if issue.get('ntd_reference'):
                    p.add_run(f" (НТД: {issue.get('ntd_reference')})")
        else:
            doc.add_paragraph('Критические замечания отсутствуют.')
        
        # Некритические замечания
        doc.add_heading('3. Некритические замечания', level=1)
        non_critical_issues = [r for r in results if r.get('severity') == 'non_critical']
        if non_critical_issues:
            for issue in non_critical_issues:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(f"[{issue.get('check_type', '')}] {issue.get('message', '')}")
                if issue.get('ntd_reference'):
                    p.add_run(f" (НТД: {issue.get('ntd_reference')})")
        else:
            doc.add_paragraph('Некритические замечания отсутствуют.')
        
        # Непроведенные проверки
        doc.add_heading('4. Непроведенные проверки', level=1)
        skipped_checks = [r for r in results if r.get('status') == 'skipped']
        if skipped_checks:
            for check in skipped_checks:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(f"[{check.get('check_type', '')}] {check.get('message', 'Причина не указана')}")
        else:
            doc.add_paragraph('Все проверки проведены.')
        
        # Выводы
        doc.add_heading('5. Выводы', level=1)
        total_critical = len(critical_issues)
        total_non_critical = len(non_critical_issues)
        
        if total_critical > 0:
            conclusion = f"Документация НЕ СООТВЕТСТВУЕТ требованиям. Выявлено {total_critical} критических и {total_non_critical} некритических замечаний."
        elif total_non_critical > 0:
            conclusion = f"Документация соответствует требованиям с замечаниями. Выявлено {total_non_critical} некритических замечаний."
        else:
            conclusion = "Документация соответствует всем требованиям. Замечания отсутствуют."
        
        doc.add_paragraph(conclusion)
        
        # НТД
        doc.add_heading('6. Использованные нормативные документы', level=1)
        if ntd_docs:
            for ntd in ntd_docs:
                p = doc.add_paragraph(style='List Bullet')
                p.add_run(f"{ntd.get('doc_number', '')} - {ntd.get('doc_name', '')}")
        else:
            doc.add_paragraph('Список НТД не предоставлен.')
        
        # Сохранение
        doc.save(output_path)
        return output_path
    
    @staticmethod
    def generate_xls_report(check_info: Dict, results: List[Dict], output_path: str) -> str:
        """Генерация отчета в формате XLSX"""
        wb = Workbook()
        
        # Лист 1: Общая информация
        ws_info = wb.active
        ws_info.title = "Общая информация"
        
        info_data = [
            ['Параметр', 'Значение'],
            ['Наименование проверки', check_info.get('name', '')],
            ['Инженерная система', check_info.get('engineering_system', '')],
            ['Режим работы', check_info.get('mode', '')],
            ['Модель ИИ', check_info.get('ai_model', '')],
            ['Дата проведения', datetime.now().strftime('%Y-%m-%d %H:%M')],
            ['Статус', check_info.get('status', '')]
        ]
        
        for row_idx, row_data in enumerate(info_data, 1):
            for col_idx, cell_value in enumerate(row_data, 1):
                ws_info.cell(row=row_idx, column=col_idx, value=cell_value)
        
        # Лист 2: Замечания
        ws_issues = wb.create_sheet(title="Замечания")
        headers = ['Тип проверки', 'Статус', 'Серьезность', 'Сообщение', 'Ссылка на НТД', 'Детали']
        ws_issues.append(headers)
        
        for result in results:
            row = [
                result.get('check_type', ''),
                result.get('status', ''),
                result.get('severity', ''),
                result.get('message', ''),
                result.get('ntd_reference', ''),
                result.get('details', '')
            ]
            ws_issues.append(row)
        
        # Лист 3: Статистика
        ws_stats = wb.create_sheet(title="Статистика")
        
        critical_count = len([r for r in results if r.get('severity') == 'critical'])
        non_critical_count = len([r for r in results if r.get('severity') == 'non_critical'])
        passed_count = len([r for r in results if r.get('status') == 'passed'])
        failed_count = len([r for r in results if r.get('status') == 'failed'])
        skipped_count = len([r for r in results if r.get('status') == 'skipped'])
        
        stats_data = [
            ['Показатель', 'Количество'],
            ['Критические замечания', critical_count],
            ['Некритические замечания', non_critical_count],
            ['Проверок пройдено', passed_count],
            ['Проверок не пройдено', failed_count],
            ['Проверок пропущено', skipped_count]
        ]
        
        for row_idx, row_data in enumerate(stats_data, 1):
            for col_idx, cell_value in enumerate(row_data, 1):
                ws_stats.cell(row=row_idx, column=col_idx, value=cell_value)
        
        # Сохранение
        wb.save(output_path)
        return output_path
    
    @staticmethod
    def generate_cable ведомость(cables: List[Dict], output_path: str) -> str:
        """Генерация ведомости кабеля в формате XLSX"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Ведомость кабеля"
        
        headers = ['№ п/п', 'Марка кабеля', 'Количество', 'Ед. изм.', 'Длина (м)', 'Трасса', 'Примечание']
        ws.append(headers)
        
        for idx, cable in enumerate(cables, 1):
            row = [
                idx,
                cable.get('mark', ''),
                cable.get('quantity', 1),
                'м',
                cable.get('length', 0),
                cable.get('route', ''),
                cable.get('notes', '')
            ]
            ws.append(row)
        
        # Итого
        total_length = sum(c.get('length', 0) for c in cables)
        ws.append(['', '', '', 'ИТОГО:', total_length, '', ''])
        
        wb.save(output_path)
        return output_path
    
    @staticmethod
    def generate_equipment ведомость(equipment: List[Dict], output_path: str) -> str:
        """Генерация ведомости оборудования в формате XLSX"""
        wb = Workbook()
        ws = wb.active
        ws.title = "Ведомость оборудования"
        
        headers = ['№ п/п', 'Наименование', 'Тип', 'Количество', 'Ед. изм.', 'Примечание']
        ws.append(headers)
        
        for idx, item in enumerate(equipment, 1):
            row = [
                idx,
                item.get('name', ''),
                item.get('type', ''),
                item.get('quantity', 1),
                item.get('unit', 'шт'),
                item.get('notes', '')
            ]
            ws.append(row)
        
        wb.save(output_path)
        return output_path

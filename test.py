from parse import *
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import cm  # Импортируем единицы измерения

tsv_file = "D:\\Офисные технологии\\ЛР4\\4.1\\data\\2024-09-16_21-23-32.tsv"
tsv_file = "D:\\Офисные технологии\\ЛР4\\4.1\\data\\2024-09-16_21-23-32_short.tsv"

def build_document_compact(tables):
    print("Создание компактного PDF документа...")
    
    # Еще более компактные поля
    doc = SimpleDocTemplate("simple_table.pdf", 
                          pagesize=A4,
                          leftMargin=0.5*cm,
                          rightMargin=0.5*cm,
                          topMargin=0.7*cm,
                          bottomMargin=0.7*cm)
    
    styles = getSampleStyleSheet()
    story = []
    
    # Компактный стиль таблицы
    compact_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Выравнивание по левому краю компактнее
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),    # Еще меньше шрифт
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2),   # Отступы сверху
        ('LEFTPADDING', (0, 0), (-1, -1), 2),  # Отступы слева
        ('RIGHTPADDING', (0, 0), (-1, -1), 2), # Отступы справа
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black)  # Более тонкие линии
    ])
    
    # Создаем компактный стиль для текста
    compact_text_style = styles['Normal']
    compact_text_style.fontSize = 7
    compact_text_style.leading = 9  # Межстрочный интервал
    
    compact_title_style = styles['Heading2']
    compact_title_style.fontSize = 12
    compact_title_style.leading = 14
    
    for section_name, content in tables.items():
        print(f"Обработка: {section_name}")
        
        title = Paragraph(f"<b>{section_name}</b>", compact_title_style)
        story.append(title)
        story.append(Spacer(1, 4))  # Минимальный отступ
        
        if content:
            table_data = []
            for line in content:
                if isinstance(line, str) and line.strip():
                    table_data.append([Paragraph(line, compact_text_style)])
                elif isinstance(line, list):
                    row = [Paragraph(str(cell), compact_text_style) for cell in line]
                    table_data.append(row)
            
            if table_data:
                table = Table(table_data)
                table.setStyle(compact_style)
                story.append(table)
                story.append(Spacer(1, 8))  # Компактный отступ между таблицами
    
    if story:
        doc.build(story)
        print("Компактный PDF создан успешно!")

def build_document(tables):
    print("Создание PDF документа...")
    
    # Создаем документ
    doc = SimpleDocTemplate("simple_table.pdf", pagesize=A4, )
    styles = getSampleStyleSheet()
    story = []  # Список всех элементов документа
    
    # Базовый стиль для таблиц
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    for section_name, content in tables.items():
        print(f"\nОбработка раздела: {section_name}")
        
        # Добавляем заголовок раздела
        title = Paragraph(f"<b>{section_name}</b>", styles['Heading2'])
        story.append(title)
        story.append(Spacer(1, 12))  # Отступ после заголовка
        
        # Преобразуем данные для таблицы
        table_data = []
        if content and len(content) > 0:
            # Если content - список строк, создаем таблицу с одной колонкой
            if all(isinstance(item, str) for item in content):
                table_data = [[Paragraph(line, styles['Normal'])] for line in content if line.strip()]
            # Если content - список списков (уже таблица)
            elif all(isinstance(item, list) for item in content):
                for row in content:
                    table_row = []
                    for cell in row:
                        if isinstance(cell, str):
                            table_row.append(Paragraph(cell, styles['Normal']))
                        else:
                            table_row.append(Paragraph(str(cell), styles['Normal']))
                    table_data.append(table_row)
            else:
                # Смешанный случай - обрабатываем как одноколоночную таблицу
                table_data = [[Paragraph(str(item), styles['Normal'])] for item in content]
        
        if table_data:
            # Создаем таблицу
            table = Table(table_data)
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 24))  # Отступ после таблицы
            print(f" - Таблица добавлена ({len(table_data)} строк)")
        else:
            print(f" - Нет данных для таблицы")
    
    # Строим весь документ одним вызовом
    if story:
        doc.build(story)
        print(f"\nPDF файл 'simple_table.pdf' создан успешно!")
        print(f"Всего элементов в документе: {len(story)}")
    else:
        print("\nОшибка: Нет данных для создания документа!")

def create_simple_pdf_table():
    # Создаем PDF документ
    readed_file = parse_sections_file(tsv_file)
    print_parse_data(readed_file)
    tables = parse_for_table(readed_file)
    print_parse_data(tables)
    build_document_compact(tables)

# Запуск
create_simple_pdf_table()

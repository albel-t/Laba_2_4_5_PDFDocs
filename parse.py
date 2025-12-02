import re

def remove_empty_lines(lines):
    print ("Удаляет пустые строки из списка")
    return [line.replace("\t", '') for line in lines if line.strip() != '']

def parse_sections_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        
        pattern = r'==\s*(.*?)\s*==\s*\n?(.*?)(?=\s*==\s*|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        sections = {}
        for section_name, section_content in matches:
            sections[section_name.strip()] = [line.rstrip() for line in section_content.split('\n') if line.strip()]

        return sections
        
    except FileNotFoundError:
        print(f"Ошибка: Файл '{filename}' не найден")
        return {}
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return {}

def parse_for_table(data):
    table = {}
    print("Разбиение для таблицы")
    for section_name, content in data.items():
        print(f"\nСекция - {section_name} -")
        if section_name == "Items":
            content = ''.join(content)
            content = remove_empty_lines(content.split(" "))
            tmp_content = []
            for item in content:
                tmp_content.append(item.split(":"))
            tmp_table = [["Parameter", "Value", "Parameter", "Value"]]
            for i in range(0, len(tmp_content)//2):
                tmp_table.append([tmp_content[i*2][0], tmp_content[i*2][1], tmp_content[i*2+1][0], tmp_content[i*2+1][1]])
            if len(tmp_content)%2 == 1:
                tmp_table.append([tmp_content[len(tmp_content)//2+1][0], tmp_content[len(tmp_content)//2+1][1], "-empty-", "-empty-"])
            table[section_name] = tmp_table
        if section_name == "Data":
            tmp_table = []
            for item in content:
                tmp_table.append(remove_empty_lines(item.split(" ")))
            table[section_name] = tmp_table
    return table

def print_parse_data(data):
    # Выводим результат
    print("Содержимое файла разбито на разделы:")
    for section_name, content in data.items():
        print(f"\n({section_name}")
        print(f"{content})")
import time
import csv
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import os
from datetime import datetime

class FIPSSearch:
    def __init__(self, headless=False):
        """Инициализация драйвера Chrome с автоматической установкой драйвера"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Автоматическая установка ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Убираем признаки автоматизации
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        self.wait = WebDriverWait(self.driver, 30)
        self.base_url = "https://www.fips.ru/iiss/search.xhtml"
        self.results = []
        
    def search_document(self, title=None, authors=None):
        """Поиск документа по названию и/или авторам"""
        try:
            print("Открытие сайта ФИПС...")
            self.driver.get(self.base_url)
            
            # Ждем полной загрузки страницы
            time.sleep(5)
            
            # Проверяем, загрузилась ли страница
            if "fips.ru" not in self.driver.current_url:
                print("Не удалось загрузить страницу ФИПС")
                self.driver.save_screenshot("page_load_error.png")
                return False
            
            print("Поиск полей ввода...")
            
            # Ищем поле для названия документа
            title_field = None
            try:
                title_field = self.driver.find_element(By.XPATH, "//input[contains(@id, 'docName') or contains(@name, 'docName')]")
            except:
                # Пробуем другие возможные селекторы
                try:
                    title_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Название документа' or contains(@placeholder, 'назван')]")
                except:
                    try:
                        # Ищем любые текстовые поля
                        inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        for inp in inputs:
                            if inp.get_attribute('type') == 'text':
                                title_field = inp
                                break
                    except:
                        pass
            
            # Ищем поле для авторов
            authors_field = None
            try:
                authors_field = self.driver.find_element(By.XPATH, "//input[contains(@id, 'author') or contains(@name, 'author')]")
            except:
                try:
                    authors_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Автор' or contains(@placeholder, 'автор')]")
                except:
                    pass
            
            # Ввод названия (если указано и найдено поле)
            if title and title_field:
                print(f"Ввод названия: {title}")
                try:
                    title_field.clear()
                    title_field.send_keys(title)
                    time.sleep(1)
                except Exception as e:
                    print(f"Ошибка при вводе названия: {e}")
            
            # Ввод авторов (если указано и найдено поле)
            if authors and authors_field:
                print(f"Ввод авторов: {authors}")
                try:
                    authors_field.clear()
                    authors_field.send_keys(authors)
                    time.sleep(1)
                except Exception as e:
                    print(f"Ошибка при вводе авторов: {e}")
            
            # Поиск кнопки "Найти" или "Поиск"
            print("Поиск кнопки для выполнения поиска...")
            search_button = None
            
            # Пробуем разные варианты кнопок
            button_selectors = [
                "//button[contains(text(), 'Найти')]",
                "//button[contains(text(), 'Поиск')]",
                "//input[@type='submit' and contains(@value, 'Найти')]",
                "//button[@type='submit']",
                "//a[contains(text(), 'Найти')]",
                "//*[contains(@onclick, 'search')]"
            ]
            
            for selector in button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    if buttons:
                        search_button = buttons[0]
                        print(f"Найдена кнопка с селектором: {selector}")
                        break
                except:
                    continue
            
            if search_button:
                print("Выполнение поиска...")
                try:
                    # Пробуем кликнуть через JavaScript
                    self.driver.execute_script("arguments[0].click();", search_button)
                    time.sleep(3)
                except:
                    try:
                        search_button.click()
                        time.sleep(3)
                    except:
                        print("Не удалось нажать кнопку поиска")
                        return False
            else:
                # Если не нашли кнопку, пробуем нажать Enter в поле ввода
                print("Кнопка не найдена, пробуем нажать Enter...")
                if title_field:
                    title_field.send_keys(Keys.RETURN)
                    time.sleep(3)
                elif authors_field:
                    authors_field.send_keys(Keys.RETURN)
                    time.sleep(3)
                else:
                    print("Не найдены элементы для поиска")
                    return False
            
            # Ждем загрузки результатов
            print("Ожидание загрузки результатов...")
            time.sleep(5)
            
            # Проверка наличия результатов
            return self._check_results()
            
        except Exception as e:
            print(f"Ошибка при поиске: {str(e)[:200]}")
            self.driver.save_screenshot("search_error.png")
            return False
    
    def _check_results(self):
        """Проверка наличия результатов поиска"""
        try:
            # Делаем скриншот текущего состояния
            self.driver.save_screenshot("check_results.png")
            
            # Проверяем наличие сообщения об отсутствии результатов
            no_results_phrases = [
                "ничего не найдено", "не найдено", "нет результатов", 
                "no results found", "не найдены", "ничего не обнаружено"
            ]
            
            page_text = self.driver.page_source.lower()
            for phrase in no_results_phrases:
                if phrase in page_text:
                    print(f"Найдена фраза '{phrase}' - документы не найдены")
                    return False
            
            # Проверяем наличие таблицы или списка результатов
            # Ищем любые элементы, которые могут быть результатами
            potential_results = []
            
            # Ищем таблицы
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            if tables:
                print(f"Найдено таблиц: {len(tables)}")
                for i, table in enumerate(tables):
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"  Таблица {i+1}: {len(rows)} строк")
                    if len(rows) > 1:
                        potential_results.append(table)
            
            # Ищем списки
            lists = self.driver.find_elements(By.XPATH, "//ul | //ol | //div[contains(@class, 'list')]")
            if lists:
                print(f"Найдено списков: {len(lists)}")
            
            # Ищем ссылки на документы
            doc_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'document') or contains(@href, 'id=')]")
            print(f"Найдено ссылок на документы: {len(doc_links)}")
            
            # Ищем любые данные в результатах
            result_indicators = ["патент", "заявка", "регистрац", "автор", "название", "№", "№ заявки"]
            
            for indicator in result_indicators:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{indicator}')]")
                if elements:
                    print(f"Найден индикатор результата: '{indicator}' - {len(elements)} элементов")
            
            # Если нашли потенциальные результаты
            if potential_results or doc_links:
                print("Найдены потенциальные результаты поиска")
                return True
            else:
                print("Не найдено результатов поиска")
                return False
                
        except Exception as e:
            print(f"Ошибка при проверке результатов: {e}")
            return False
    
    def extract_document_info(self, max_docs=10):
        """Извлечение информации о документах"""
        try:
            print("Начало извлечения информации о документах...")
            
            # Делаем скриншот для отладки
            self.driver.save_screenshot("before_extraction.png")
            
            # Получаем HTML страницы для анализа
            page_source = self.driver.page_source
            
            # Сохраняем HTML для отладки
            with open("page_source.html", "w", encoding="utf-8") as f:
                f.write(page_source)
            print("HTML страницы сохранен в page_source.html")
            
            # Ищем все потенциальные блоки с документами
            print("Поиск блоков с документами...")
            
            # Пробуем разные подходы для извлечения данных
            
            # 1. Ищем через таблицы
            documents = self._extract_from_tables()
            
            # 2. Если через таблицы не нашли, ищем через ссылки
            if not documents:
                documents = self._extract_from_links()
            
            # 3. Если все еще не нашли, ищем по тексту
            if not documents:
                documents = self._extract_from_text()
            
            print(f"Всего найдено документов: {len(documents)}")
            
            # Ограничиваем количество документов
            documents = documents[:max_docs]
            
            # Сохраняем результаты
            self.results = documents
            
            if documents:
                print(f"Успешно извлечено {len(documents)} документов")
                return True
            else:
                print("Не удалось извлечь информацию о документах")
                return False
            
        except Exception as e:
            print(f"Ошибка при извлечении информации: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _extract_from_tables(self):
        """Извлечение данных из таблиц"""
        documents = []
        try:
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"Найдено таблиц для анализа: {len(tables)}")
            
            for table_idx, table in enumerate(tables):
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"  Таблица {table_idx+1}: {len(rows)} строк")
                    
                    # Пропускаем таблицы с малым количеством строк
                    if len(rows) < 2:
                        continue
                    
                    # Анализируем первую строку (заголовок) для понимания структуры
                    header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                    if not header_cells:
                        header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                    
                    header_texts = [cell.text.strip().lower() for cell in header_cells]
                    print(f"    Заголовки: {header_texts}")
                    
                    # Обрабатываем строки с данными (начиная со второй)
                    for row_idx, row in enumerate(rows[1:], 1):
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) < 2:
                                continue
                            
                            doc_info = {}
                            
                            # Название документа (обычно в первой ячейке)
                            if len(cells) > 0:
                                doc_info['Название'] = cells[0].text.strip()
                            
                            # Авторы
                            if len(cells) > 1:
                                doc_info['Авторы'] = cells[1].text.strip()
                            
                            # Регистрационный номер
                            if len(cells) > 2:
                                doc_info['Регистрационный номер'] = cells[2].text.strip()
                            
                            # Номер заявки
                            if len(cells) > 3:
                                doc_info['Номер заявки'] = cells[3].text.strip()
                            
                            # Правообладатель
                            if len(cells) > 4:
                                doc_info['Правообладатель'] = cells[4].text.strip()
                            
                            # Даты
                            if len(cells) > 5:
                                doc_info['Дата поступления'] = cells[5].text.strip()
                            
                            if len(cells) > 6:
                                doc_info['Дата регистрации'] = cells[6].text.strip()
                            
                            # Ссылка на документ
                            try:
                                link = row.find_element(By.TAG_NAME, "a")
                                doc_info['Ссылка на страницу документа'] = link.get_attribute('href')
                            except:
                                doc_info['Ссылка на страницу документа'] = ""
                            
                            # Добавляем только если есть название
                            if doc_info.get('Название'):
                                documents.append(doc_info)
                                print(f"    Добавлен документ из строки {row_idx}: {doc_info['Название'][:50]}...")
                            
                        except Exception as e:
                            print(f"    Ошибка в строке {row_idx}: {e}")
                            continue
                            
                except Exception as e:
                    print(f"  Ошибка при обработке таблицы {table_idx+1}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Ошибка при извлечении из таблиц: {e}")
        
        return documents
    
    def _extract_from_links(self):
        """Извлечение данных из ссылок"""
        documents = []
        try:
            # Ищем все ссылки, которые могут вести к документам
            link_selectors = [
                "//a[contains(@href, 'document')]",
                "//a[contains(@href, 'id=')]",
                "//a[contains(@href, 'search_result')]",
                "//a[contains(text(), 'патент') or contains(text(), 'заявка')]"
            ]
            
            all_links = []
            for selector in link_selectors:
                try:
                    links = self.driver.find_elements(By.XPATH, selector)
                    all_links.extend(links)
                except:
                    continue
            
            # Убираем дубликаты
            unique_links = []
            seen_hrefs = set()
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    if href and href not in seen_hrefs:
                        seen_hrefs.add(href)
                        unique_links.append(link)
                except:
                    continue
            
            print(f"Найдено уникальных ссылок: {len(unique_links)}")
            
            for i, link in enumerate(unique_links[:20]):  # Ограничиваем для скорости
                try:
                    doc_info = {
                        'Название': link.text.strip() if link.text.strip() else f"Ссылка {i+1}",
                        'Авторы': "Не указано",
                        'Регистрационный номер': "Не указано",
                        'Номер заявки': "Не указано",
                        'Правообладатель': "Не указано",
                        'Дата поступления': "Не указано",
                        'Дата регистрации': "Не указано",
                        'Ссылка на страницу документа': link.get_attribute('href')
                    }
                    
                    # Пытаемся найти дополнительную информацию рядом со ссылкой
                    parent = link.find_element(By.XPATH, "..")
                    parent_text = parent.text.strip()
                    if parent_text:
                        lines = parent_text.split('\n')
                        if len(lines) > 1:
                            doc_info['Название'] = lines[0]
                    
                    documents.append(doc_info)
                    print(f"  Добавлена ссылка {i+1}: {doc_info['Название'][:50]}...")
                    
                except Exception as e:
                    print(f"  Ошибка при обработке ссылки {i+1}: {e}")
                    continue
            
        except Exception as e:
            print(f"Ошибка при извлечении из ссылок: {e}")
        
        return documents
    
    def _extract_from_text(self):
        """Извлечение данных из текста страницы"""
        documents = []
        try:
            # Получаем весь текст страницы
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Ищем паттерны, похожие на документы
            lines = page_text.split('\n')
            
            current_doc = {}
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Проверяем, содержит ли строка признаки документа
                if any(word in line.lower() for word in ['патент', 'заявка', 'изобретение', '№', 'рег.']):
                    if current_doc:
                        documents.append(current_doc)
                        current_doc = {}
                    
                    current_doc['Название'] = line
                    current_doc['Ссылка на страницу документа'] = ""
                elif 'автор' in line.lower() and not current_doc.get('Авторы'):
                    current_doc['Авторы'] = line
                elif any(word in line.lower() for word in ['рег.номер', 'регистрац', 'номер']):
                    current_doc['Регистрационный номер'] = line
            
            # Добавляем последний документ
            if current_doc:
                documents.append(current_doc)
            
            print(f"Извлечено документов из текста: {len(documents)}")
            
        except Exception as e:
            print(f"Ошибка при извлечении из текста: {e}")
        
        return documents
    
    def save_pages_as_pdf(self, output_dir="output_pdf"):
        """Сохранение страниц документов в PDF"""
        try:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            print(f"\nСохранение страниц документов в папку: {output_dir}")
            
            saved_count = 0
            for i, result in enumerate(self.results):
                link = result.get('Ссылка на страницу документа')
                if link and link.startswith('http'):
                    try:
                        print(f"\nОбработка документа {i+1}/{len(self.results)}...")
                        print(f"  Название: {result.get('Название', 'Без названия')[:50]}...")
                        print(f"  Ссылка: {link}")
                        
                        # Открываем страницу документа
                        self.driver.get(link)
                        time.sleep(3)
                        
                        # Создаем имя файла
                        safe_title = "".join(c for c in result.get('Название', f'doc_{i}') if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_title = safe_title[:50]
                        filename = f"{safe_title}_{datetime.now().strftime('%H%M%S')}.pdf"
                        filepath = os.path.join(output_dir, filename)
                        
                        # Пытаемся сохранить как PDF
                        print("  Попытка сохранения как PDF...")
                        
                        # Способ 1: через печать (откроет диалог печати)
                        self.driver.execute_script('window.print();')
                        time.sleep(2)
                        
                        print(f"  Открыт диалог печати для файла: {filename}")
                        saved_count += 1
                        
                        # Возвращаемся на предыдущую страницу
                        self.driver.back()
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"  Ошибка при сохранении документа {i+1}: {e}")
                        # Продолжаем с другими документами
            
            print(f"\nВсего подготовлено для сохранения: {saved_count} документов")
            print("Примечание: Для сохранения в PDF необходимо вручную выбрать 'Сохранить как PDF' в диалоге печати.")
            
        except Exception as e:
            print(f"Ошибка при сохранении PDF: {e}")
    
    def save_to_csv(self, filename="fips_results.csv"):
        """Сохранение результатов в CSV файл"""
        try:
            if not self.results:
                print("Нет данных для сохранения")
                return False
            
            # Определяем все возможные заголовки
            all_headers = set()
            for result in self.results:
                all_headers.update(result.keys())
            
            headers = list(all_headers)
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                for result in self.results:
                    writer.writerow(result)
            
            print(f"Результаты сохранены в CSV файл: {filename}")
            print(f"Всего записей: {len(self.results)}")
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении в CSV: {e}")
            return False
    
    def save_to_json(self, filename="fips_results.json"):
        """Сохранение результатов в JSON файл"""
        try:
            if not self.results:
                print("Нет данных для сохранения")
                return False
            
            with open(filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(self.results, jsonfile, ensure_ascii=False, indent=2)
            
            print(f"Результаты сохранены в JSON файл: {filename}")
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении в JSON: {e}")
            return False
    
    def print_results(self):
        """Вывод результатов в консоль"""
        if not self.results:
            print("Нет результатов для отображения")
            return
        
        print("\n" + "="*100)
        print(f"НАЙДЕНО ДОКУМЕНТОВ: {len(self.results)}")
        print("="*100)
        
        for i, result in enumerate(self.results, 1):
            print(f"\nДокумент {i}:")
            print("-" * 50)
            for key, value in result.items():
                if value and str(value).strip():  # Показываем только непустые значения
                    print(f"{key}: {value}")
            print("-" * 50)
    
    def close(self):
        """Закрытие браузера"""
        try:
            self.driver.quit()
            print("\nБраузер закрыт")
        except:
            pass


def main():
    """Основная функция программы"""
    print("="*70)
    print("ПРОГРАММА ПОИСКА ДОКУМЕНТОВ ФИПС")
    print("="*70)
    
    # Можно задать параметры поиска прямо в коде
    title = "система питания импульсной нагрузки"
    authors = ""
    
    print(f"\nПараметры поиска:")
    print(f"Название документа: {title}")
    print(f"Авторы: {authors if authors else 'не указаны'}")
    
    print("\n" + "="*70)
    print("ЗАПУСК ПОИСКА...")
    print("="*70)
    
    # Инициализация поиска
    searcher = FIPSSearch(headless=False)  # headless=False для отображения браузера
    
    try:
        # Выполнение поиска
        success = searcher.search_document(
            title=title if title else None, 
            authors=authors if authors else None
        )
        
        if success:
            # Извлечение информации
            print("\n" + "="*70)
            print("ИЗВЛЕЧЕНИЕ ИНФОРМАЦИИ...")
            print("="*70)
            
            if searcher.extract_document_info(max_docs=10):
                # Вывод результатов
                searcher.print_results()
                
                # Сохранение результатов
                print("\n" + "="*70)
                print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
                print("="*70)
                
                # Сохраняем в CSV
                csv_file = "fips_results.csv"
                searcher.save_to_csv(csv_file)
                
                # Сохраняем в JSON
                json_file = "fips_results.json"
                searcher.save_to_json(json_file)
                
                # Предлагаем сохранить страницы как PDF
                print("\n" + "-"*70)
                print("Для сохранения страниц в PDF:")
                print("1. Программа откроет диалог печати для каждого документа")
                print("2. В диалоге печати выберите 'Сохранить как PDF'")
                print("3. Укажите место сохранения")
                print("-"*70)
                
                save_pdf = input("\nСохранить страницы документов в PDF? (y/n): ").strip().lower()
                
                if save_pdf == 'y':
                    print("\n" + "="*70)
                    print("СОХРАНЕНИЕ СТРАНИЦ В PDF")
                    print("="*70)
                    searcher.save_pages_as_pdf()
                    
                print("\n" + "="*70)
                print(f"РЕЗУЛЬТАТЫ СОХРАНЕНЫ:")
                print(f"1. {csv_file} - данные в формате CSV")
                print(f"2. {json_file} - данные в формате JSON")
                if save_pdf == 'y':
                    print(f"3. Диалоги печати открыты для сохранения в PDF")
                print("="*70)
                
            else:
                print("\nНе удалось извлечь информацию о документах")
        else:
            print("\nДокументы не найдены по заданным критериям")
            
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Закрытие браузера
        input("\nНажмите Enter для завершения...")
        searcher.close()


if __name__ == "__main__":
    main()
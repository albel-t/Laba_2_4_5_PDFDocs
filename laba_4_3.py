import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

class FIPSSearch:
    def __init__(self, headless=False):
        """Инициализация драйвера Chrome"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        self.wait = WebDriverWait(self.driver, 30)
        self.base_url = "https://www.fips.ru/iiss/search.xhtml"
        self.results = []
        
    def search_document(self, title=None, authors=None):
        """Поиск документа по названию и/или авторам"""
        try:
            print("Открытие сайта ФИПС...")
            self.driver.get(self.base_url)
            time.sleep(5)
            
            if "fips.ru" not in self.driver.current_url:
                print("Не удалось загрузить страницу ФИПС")
                return False
            
            print("Поиск полей ввода...")
            
            # Поиск поля для названия
            title_field = None
            try:
                title_field = self.driver.find_element(By.XPATH, "//input[contains(@id, 'docName') or contains(@name, 'docName')]")
            except:
                try:
                    title_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Название документа' or contains(@placeholder, 'назван')]")
                except:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        if inp.get_attribute('type') == 'text':
                            title_field = inp
                            break
            
            # Ввод названия
            if title and title_field:
                print(f"Ввод названия: {title}")
                title_field.clear()
                title_field.send_keys(title)
                time.sleep(1)
            
            # Поиск кнопки "Найти"
            print("Поиск кнопки для выполнения поиска...")
            search_button = None
            
            button_selectors = [
                "//button[contains(text(), 'Найти')]",
                "//button[contains(text(), 'Поиск')]",
                "//input[@type='submit' and contains(@value, 'Найти')]",
                "//button[@type='submit']"
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
                self.driver.execute_script("arguments[0].click();", search_button)
                time.sleep(3)
            else:
                if title_field:
                    title_field.send_keys(Keys.RETURN)
                    time.sleep(3)
                else:
                    print("Не найдены элементы для поиска")
                    return False
            
            print("Ожидание загрузки результатов...")
            time.sleep(5)
            
            return self._check_results()
            
        except Exception as e:
            print(f"Ошибка при поиске: {str(e)[:200]}")
            return False
    
    def _check_results(self):
        """Проверка наличия результатов поиска"""
        try:
            no_results_phrases = [
                "ничего не найдено", "не найдено", "нет результатов", 
                "no results found", "не найдены"
            ]
            
            page_text = self.driver.page_source.lower()
            for phrase in no_results_phrases:
                if phrase in page_text:
                    print(f"Найдена фраза '{phrase}' - документы не найдены")
                    return False
            
            # Проверяем наличие ссылок на документы
            doc_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'document') or contains(@href, 'id=')]")
            print(f"Найдено ссылок на документы: {len(doc_links)}")
            
            if doc_links:
                print("Найдены потенциальные результаты поиска")
                return True
            else:
                print("Не найдено результатов поиска")
                return False
                
        except Exception as e:
            print(f"Ошибка при проверке результатов: {e}")
            return False
    
    def extract_document_links(self, max_docs=10):
        """Извлечение ссылок на документы"""
        try:
            print("Извлечение ссылок на документы...")
            
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
                    if href and href not in seen_hrefs and 'fips.ru' in href:
                        seen_hrefs.add(href)
                        unique_links.append(link)
                except:
                    continue
            
            print(f"Найдено уникальных ссылок: {len(unique_links)}")
            
            # Сохраняем информацию о документах
            self.results = []
            for i, link in enumerate(unique_links[:max_docs]):
                try:
                    doc_info = {
                        'Название': link.text.strip() if link.text.strip() else f"Ссылка {i+1}",
                        'Ссылка на страницу документа': link.get_attribute('href')
                    }
                    
                    self.results.append(doc_info)
                    print(f"  Добавлена ссылка {i+1}: {doc_info['Название'][:50]}...")
                    
                except Exception as e:
                    print(f"  Ошибка при обработке ссылки {i+1}: {e}")
                    continue
            
            return len(self.results) > 0
            
        except Exception as e:
            print(f"Ошибка при извлечении ссылок: {e}")
            return False
    
    def save_pages_as_pdf(self):
        """Сохранение страниц документов через печать в PDF"""
        try:
            print(f"\nСохранение страниц документов...")
            
            if not self.results:
                print("Нет ссылок на документы для сохранения")
                return
            
            print(f"Найдено документов для сохранения: {len(self.results)}")
            
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
                        
                        # Открываем диалог печати
                        print("  Открытие диалога печати...")
                        self.driver.execute_script('window.print();')
                        
                        print(f"  Диалог печати открыт. Для сохранения выберите 'Сохранить как PDF'")
                        print(f"  Рекомендуемое имя файла: {safe_title}.pdf")
                        
                        # Ждем перед следующим документом
                        if i < len(self.results) - 1:
                            print("\n  Для продолжения закройте диалог печати и нажмите Enter...")
                            input()
                            
                    except Exception as e:
                        print(f"  Ошибка при обработке документа {i+1}: {e}")
                        continue
            
            print(f"\nЗавершено. Всего обработано: {len(self.results)} документов")
            
        except Exception as e:
            print(f"Ошибка при сохранении PDF: {e}")
    
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
    
    # Параметры поиска
    title = "система питания импульсной нагрузки"
    authors = ""
    
    print(f"\nПараметры поиска:")
    print(f"Название документа: {title}")
    
    print("\n" + "="*70)
    print("ЗАПУСК ПОИСКА...")
    print("="*70)
    
    # Инициализация поиска
    searcher = FIPSSearch(headless=False)  # headless=False для отображения браузера
    
    try:
        # Выполнение поиска
        success = searcher.search_document(title=title, authors=authors)
        
        if success:
            # Извлечение ссылок на документы
            print("\n" + "="*70)
            print("ИЗВЛЕЧЕНИЕ ССЫЛОК НА ДОКУМЕНТЫ...")
            print("="*70)
            
            if searcher.extract_document_links(max_docs=10):
                print(f"\nНайдено ссылок: {len(searcher.results)}")
                
                # Сохранение через печать
                print("\n" + "="*70)
                print("СОХРАНЕНИЕ СТРАНИЦ В PDF ЧЕРЕЗ ПЕЧАТЬ")
                print("="*70)
                print("Инструкция:")
                print("1. Для каждого документа откроется диалог печати")
                print("2. В диалоге печати выберите 'Сохранить как PDF'")
                print("3. Укажите место сохранения и имя файла")
                print("4. После сохранения закройте диалог печати")
                print("="*70)
                
                searcher.save_pages_as_pdf()
                
            else:
                print("\nНе удалось извлечь ссылки на документы")
        else:
            print("\nДокументы не найдены по заданным критериям")
            
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
    
    finally:
        # Закрытие браузера
        input("\nНажмите Enter для завершения...")
        searcher.close()


if __name__ == "__main__":
    main()
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta
from typing import List, Optional
import re

from ..config.settings import DJE_BASE_URL, SELENIUM_HEADLESS, SELENIUM_TIMEOUT, SEARCH_KEYWORDS
from ..models.publicacao import Publicacao
from ..utils.text_parser import TextParser
from ..utils.js_scripts import CONFIGURE_SEARCH_FORM, SCROLL_TO_BOTTOM, OPEN_LINK_IN_NEW_TAB

class DJEScraper:
    
    def __init__(self):
        self.driver = None
        self.parser = TextParser()
        
    def _setup_driver(self):
        chrome_options = Options()
        
        if SELENIUM_HEADLESS:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Driver configurado")
        
    def scrape_data(self, target_date: datetime) -> List[Publicacao]:
        publications = []
        
        try:
            print(f"Iniciando scraping para: {target_date.strftime('%d/%m/%Y')}")
            
            self._setup_driver()
            self._navigate_to_dje()
            self._configure_search_form()
            
            if self._execute_search():
                publications = self._extract_all_results()
            
            print(f"Scraping concluído. Encontradas: {len(publications)} publicações")
            
        except Exception as e:
            print(f"Erro no scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("Driver encerrado")
        
        return publications
    
    def _navigate_to_dje(self):
        self.driver.get(DJE_BASE_URL)
        time.sleep(5)
        print(f"Página carregada: {self.driver.title}")
    
    def _configure_search_form(self):
        
        try:
            result = self.driver.execute_script(CONFIGURE_SEARCH_FORM)
            print(f"✅ {result}")
            time.sleep(2)
        except Exception as e:
            print(f"Erro na configuração: {e}")
    
    def _execute_search(self) -> bool:
        print("Executando pesquisa...")
        
        try:
            search_btn = self.driver.find_element(By.XPATH, "//input[@value='Pesquisar']")
            search_btn.click()
            print("Botão pesquisar clicado")
            
            time.sleep(8)
            
            current_url = self.driver.current_url
            print(f"URL dos resultados: {current_url}")
            return True
            
        except Exception as e:
            print(f"Erro na pesquisa: {e}")
            return False
    
    def _extract_all_results(self) -> List[Publicacao]:
        publications = []
        
        try:
            self.driver.execute_script(SCROLL_TO_BOTTOM)
            time.sleep(3)
            
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            rpv_count = body_text.lower().count('rpv')
            payment_count = body_text.lower().count('pagamento')
            
            if rpv_count > 0 and payment_count > 0:
                publications.extend(self._extract_by_patterns(body_text))
                publications.extend(self._extract_from_html_elements())
                publications.extend(self._extract_from_links())
            
            publications = self._remove_duplicates(publications)
            
        except Exception as e:
            print(f"Erro na extração: {e}")
        
        return publications
    
    def _extract_by_patterns(self, text: str) -> List[Publicacao]:
        """Extrai publicações usando padrões regex"""
        print("Extraindo por padrões de texto...")
        publications = []
        
        try:
            date_pattern = r'(\d{2}/\d{2}/\d{4}.*?(?=\d{2}/\d{2}/\d{4}|$))'
            blocks = re.findall(date_pattern, text, re.DOTALL)
            
            for block in blocks:
                if self._contains_keywords(block):
                    publication = self._process_text_block(block)
                    if publication:
                        publications.append(publication)
                        print("Publicação extraída por padrão de data")
            
            process_pattern = r'(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}.*?)(?=\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}|$)'
            process_blocks = re.findall(process_pattern, text, re.DOTALL)
            
            for block in process_blocks:
                if self._contains_keywords(block):
                    publication = self._process_text_block(block)
                    if publication:
                        publications.append(publication)
                        print("Publicação extraída por padrão de processo")
            
            if not publications and self._contains_keywords(text):
                publication = self._process_text_block(text)
                if publication:
                    publications.append(publication)
                    print("Publicação extraída do texto completo")
            
        except Exception as e:
            print(f"Erro na extração por padrões: {e}")
        
        return publications
    
    def _extract_from_html_elements(self) -> List[Publicacao]:
        print("Extraindo de elementos HTML...")
        publications = []
        
        try:
            xpath_selectors = [
                "//div[contains(text(), 'RPV')]",
                "//tr[contains(text(), 'RPV')]", 
                "//p[contains(text(), 'RPV')]",
                "//td[contains(text(), 'RPV')]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        element_text = element.text
                        if self._contains_keywords(element_text):
                            publication = self._process_text_block(element_text)
                            if publication:
                                publications.append(publication)
                except:
                    continue
            
        except Exception as e:
            print(f"Erro na extração HTML: {e}")
        
        return publications
    
    def _extract_from_links(self) -> List[Publicacao]:
        publications = []
        
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            relevant_links = []
            for link in links:
                href = link.get_attribute("href")
                if href and ("consultaSimples" in href or "publicacao" in href):
                    relevant_links.append(href)
            
            print(f"Encontrados {len(relevant_links)} links relevantes")
            
            for i, href in enumerate(relevant_links[:3]):
                try:
                    print(f"Processando link {i+1}: {href}")
                    
                    self.driver.execute_script(OPEN_LINK_IN_NEW_TAB, href)
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    
                    time.sleep(3)
                    
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    
                    if self._contains_keywords(page_text):
                        publication = self._process_text_block(page_text)
                        if publication:
                            publication.url_publicacao = href
                            publications.append(publication)
                            print(f"✅ Publicação extraída do link {i+1}")
                    
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    
                except Exception as e:
                    print(f"Erro no link {i+1}: {e}")
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    continue
        
        except Exception as e:
            print(f"Erro na extração via links: {e}")
        
        return publications
    
    def _process_text_block(self, text: str) -> Optional[Publicacao]:
       # Processa bloco de texto para extrair dados da publicação
        if not text or len(text.strip()) < 50:
            return None
        
        if not self._contains_keywords(text):
            return None
        
        publication = Publicacao()
        publication.conteudo_completo = text[:2000]
        
        info = self.parser.extrair_informacoes_completas(text)
        
        publication.numero_processo = info['processo_principal']
        publication.autores = info['autor']
        publication.advogados = info['advogados']
        
        if info['datas']:
            publication.data_disponibilizacao = info['datas'][0]
        
        values = info['valores']
        publication.valor_principal_bruto = values.get('principal_bruto')
        publication.valor_principal_liquido = values.get('principal_liquido')
        publication.valor_juros_moratorios = values.get('juros_moratorios')
        publication.honorarios_advocaticios = values.get('honorarios_advocaticios')
        
        if publication.numero_processo:
            print(f"Processo extraído: {publication.numero_processo}")
        if publication.autores:
            print(f"Autor extraído: {publication.autores}")
        if publication.advogados:
            print(f"Advogados extraídos: {publication.advogados}")
        if publication.valor_principal_bruto:
            print(f"Valor principal: R$ {publication.valor_principal_bruto:,.2f}")
        
        return publication
    
    def _contains_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return 'rpv' in text_lower and 'pagamento' in text_lower
    
    def _remove_duplicates(self, publications: List[Publicacao]) -> List[Publicacao]:
        if not publications:
            return []
        
        seen_keys = set()
        unique_publications = []
        
        for pub in publications:
            key = pub.numero_processo or pub.conteudo_completo[:100]
            
            if key not in seen_keys:
                seen_keys.add(key)
                unique_publications.append(pub)
        
        if len(publications) != len(unique_publications):
            print(f"Removidas {len(publications) - len(unique_publications)} duplicatas")
        
        return unique_publications
    
    def scrape_today(self) -> List[Publicacao]:
        return self.scrape_data(datetime.now())
    
    def scrape_yesterday(self) -> List[Publicacao]:
        yesterday = datetime.now() - timedelta(days=1)
        return self.scrape_data(yesterday)
    
    def test_connection(self) -> bool:
        #Testa conexão com o site do DJE
        try:
            self._setup_driver()
            self.driver.get(DJE_BASE_URL)
            
            WebDriverWait(self.driver, SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            print(f"Conectado: {self.driver.title}")
            return True
            
        except Exception as e:
            print(f"Erro de conexão: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
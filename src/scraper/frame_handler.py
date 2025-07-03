import time
import os
import glob
from typing import Optional # Importar Optional
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

class FrameHandler:
    def __init__(self, pasta_download="./downloads_dje"):
        self.driver = None
        self.wait = None
        self.extraction_count = 0
        self.pasta_download = os.path.abspath(pasta_download)
        self.arquivos_antes = set()
        
        os.makedirs(self.pasta_download, exist_ok=True)

    def set_driver(self, driver, wait):
        """Configura driver e wait para interação com o navegador."""
        self.driver = driver
        self.wait = wait
        self._configurar_download_chrome()

    def _configurar_download_chrome(self):
        """Configura o Chrome para downloads automáticos via CDP."""
        try:
            self.driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                'behavior': 'allow',
                'downloadPath': self.pasta_download
            })
        except Exception:
            pass # Ignorar erro, pode ser ambiente sem CDP ou já configurado

    def extrair_conteudo_pdf(self) -> str:
        self.extraction_count += 1
        
        try:
            self._registrar_arquivos_existentes()
            time.sleep(3) # Aguardar carregamento inicial
            
            arquivo_baixado = self._baixar_via_frame()
            if arquivo_baixado:
                conteudo = self._ler_pdf_baixado(arquivo_baixado)
                if self._is_conteudo_valido(conteudo):
                    return conteudo
            
            arquivo_baixado = self._baixar_via_javascript()
            if arquivo_baixado:
                conteudo = self._ler_pdf_baixado(arquivo_baixado)
                if self._is_conteudo_valido(conteudo):
                    return conteudo
            
            arquivo_baixado = self._baixar_via_url_direta()
            if arquivo_baixado:
                conteudo = self._ler_pdf_baixado(arquivo_baixado)
                if self._is_conteudo_valido(conteudo):
                    return conteudo
            
            return self._criar_fallback()
            
        except Exception:
            return ""
        finally:
            self._garantir_contexto_principal()

    def _registrar_arquivos_existentes(self):
        """Registra arquivos que já existem na pasta de download antes de uma nova operação."""
        try:
            self.arquivos_antes = set(os.listdir(self.pasta_download))
        except:
            self.arquivos_antes = set()

    def _baixar_via_frame(self) -> Optional[str]:
        """Tenta baixar PDF interagindo com o frame 'bottomFrame'."""
        try:
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, "bottomFrame"))
            )
            time.sleep(3)
            
            arquivo = self._tentar_botao_download()
            if arquivo: return arquivo
            
            arquivo = self._tentar_ctrl_s()
            if arquivo: return arquivo
            
            arquivo = self._tentar_botao_direito()
            if arquivo: return arquivo
            
            return None
            
        except Exception:
            self._garantir_contexto_principal()
            return None

    def _tentar_botao_download(self) -> Optional[str]:
        """Tenta encontrar e clicar no botão de download ou 'Open' no visualizador de PDF."""
        try:
            url_atual = self.driver.current_url
            
            if 'blob:' in url_atual or url_atual.endswith('.pdf'):
                return self._baixar_do_visualizador_chrome()
            
            seletores_download = [
                "//button[contains(text(), 'Open')]", "//button[contains(text(), 'Abrir')]",
                "//input[@value='Open']", "//input[@value='Abrir']",
                "//button[contains(@title, 'Download')]", "//button[contains(@class, 'download')]",
                "//a[contains(@title, 'Download')]", "//a[contains(@href, '.pdf')]",
                "//button[contains(text(), 'Download')]", "//input[@value='Download']",
                "//span[contains(@class, 'download')]", "//*[@title='Baixar']",
                "//*[contains(@onclick, 'download')]",
                "//button[contains(@style, 'center')]", "//div[@class='center']//button",
                "//button[@type='button']"
            ]
            
            for seletor in seletores_download:
                try:
                    elementos = self.driver.find_elements(By.XPATH, seletor)
                    for elemento in elementos:
                        if elemento.is_displayed() and elemento.is_enabled():
                            texto_botao = elemento.text.strip()
                            elemento.click()
                            
                            if 'open' in texto_botao.lower() or 'abrir' in texto_botao.lower():
                                time.sleep(5)
                                nova_url = self.driver.current_url
                                if nova_url != url_atual:
                                    return self._baixar_do_visualizador_chrome()
                            
                            time.sleep(3)
                            arquivo = self._aguardar_download()
                            if arquivo: return arquivo
                except Exception:
                    continue
            return None
            
        except Exception:
            return None

    def _baixar_do_visualizador_chrome(self) -> Optional[str]:
        """Tenta baixar PDF quando a página atual é o visualizador de PDF do Chrome."""
        try:
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
            time.sleep(3)
            arquivo = self._aguardar_download()
            if arquivo: return arquivo
            
            seletores_viewer = [
                "//cr-icon-button[@id='download']", "//*[@id='download']",
                "//button[@title='Download']", "//cr-icon-button[@title='Download']",
                "//*[contains(@class, 'download')]", "//paper-icon-button[@icon='file-download']"
            ]
            for seletor in seletores_viewer:
                try:
                    elementos = self.driver.find_elements(By.XPATH, seletor)
                    for elemento in elementos:
                        if elemento.is_displayed():
                            elemento.click()
                            time.sleep(3)
                            arquivo = self._aguardar_download()
                            if arquivo: return arquivo
                except Exception:
                    continue
            
            js_result = self.driver.execute_script("""
                if (window.chrome && window.chrome.pdf) { window.chrome.pdf.download(); return 'chrome_pdf_download'; }
                var url = window.location.href;
                if (url.includes('blob:')) {
                    var link = document.createElement('a'); link.href = url; link.download = 'documento.pdf';
                    document.body.appendChild(link); link.click(); document.body.removeChild(link); return 'blob_download';
                }
                return 'no_method';
            """)
            time.sleep(5)
            arquivo = self._aguardar_download()
            if arquivo: return arquivo
            
            return None
            
        except Exception:
            return None

    def _tentar_ctrl_s(self) -> Optional[str]:
        """Tenta usar Ctrl+S para salvar o PDF."""
        try:
            self.driver.execute_script("document.body.focus();")
            time.sleep(1)
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
            time.sleep(3)
            try:
                actions.send_keys(Keys.ENTER).perform()
                time.sleep(2)
            except:
                pass
            arquivo = self._aguardar_download()
            if arquivo: return arquivo
            return None
        except Exception:
            return None

    def _tentar_botao_direito(self) -> Optional[str]:
        """Tenta clicar com botão direito e salvar."""
        try:
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            actions = ActionChains(self.driver)
            actions.context_click(body_element).perform()
            time.sleep(2)
            actions.send_keys('a').perform()
            time.sleep(2)
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(3)
            arquivo = self._aguardar_download()
            if arquivo: return arquivo
            return None
        except Exception:
            return None

    def _baixar_via_javascript(self) -> Optional[str]:
        """Tenta baixar usando JavaScript."""
        try:
            js_script = """
            try {
                var links = document.querySelectorAll('a[href*=".pdf"]');
                if (links.length > 0) { links[0].click(); return 'link_clicked'; }
                
                var url = window.location.href;
                if (url.includes('pdf') || url.includes('PDF')) {
                    var link = document.createElement('a'); link.href = url; link.download = 'documento.pdf';
                    document.body.appendChild(link); link.click(); document.body.removeChild(link); return 'download_created';
                }
                window.print(); return 'print_called';
            } catch (e) { return 'error: ' + e.message; }
            """
            self.driver.execute_script(js_script)
            time.sleep(5)
            arquivo = self._aguardar_download()
            if arquivo: return arquivo
            return None
        except Exception:
            return None

    def _baixar_via_url_direta(self) -> Optional[str]:
        """Tenta acessar URL direta do PDF ou modificar URL para forçar download."""
        try:
            url_atual = self.driver.current_url
            if 'blob:' in url_atual:
                return self._baixar_blob_url()
            
            if '.pdf' in url_atual.lower() or 'pdf' in url_atual.lower():
                urls_para_tentar = []
                if '?' in url_atual:
                    urls_para_tentar.extend([url_atual + "&download=true", url_atual + "&attachment=true"])
                else:
                    urls_para_tentar.extend([url_atual + "?download=true", url_atual + "?attachment=true"])
                
                for url_teste in urls_para_tentar:
                    try:
                        self.driver.get(url_teste)
                        time.sleep(5)
                        arquivo = self._aguardar_download()
                        if arquivo: return arquivo
                    except: continue
            
            url_modificadas = [
                url_atual.replace('consultaSimples.do', 'downloadPdf.do'),
                url_atual.replace('consultaSimples.do', 'getPdf.do'),
                url_atual.replace('index.do', 'downloadPdf.do'),
                url_atual + '&outputType=pdf', url_atual + '&format=pdf'
            ]
            for url_modificada in url_modificadas:
                if url_modificada != url_atual:
                    try:
                        self.driver.get(url_modificada)
                        time.sleep(5)
                        arquivo = self._aguardar_download()
                        if arquivo: return arquivo
                    except: continue
            return None
        except Exception:
            return None

    def _baixar_blob_url(self) -> Optional[str]:
        """Baixa PDF de uma URL blob usando JavaScript e métodos alternativos."""
        try:
            js_script = """
            async function downloadBlob() {
                try {
                    if (typeof window.download === 'function') { window.download(); return 'native_download'; }
                    var url = window.location.href;
                    if (url.includes('blob:')) {
                        try {
                            var response = await fetch(url); var blob = await response.blob();
                            var link = document.createElement('a'); link.href = URL.createObjectURL(blob);
                            link.download = 'documento_' + Date.now() + '.pdf';
                            document.body.appendChild(link); link.click(); document.body.removeChild(link);
                            return 'blob_fetch_success';
                        } catch (e) { return 'blob_fetch_error: ' + e.message; }
                    }
                    document.execCommand('SaveAs', true, 'documento.pdf'); return 'save_as_command';
                } catch (e) { return 'error: ' + e.message; }
            }
            return downloadBlob();
            """
            self.driver.execute_script(js_script)
            time.sleep(5)
            arquivo = self._aguardar_download()
            if arquivo: return arquivo
            
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('s').key_up(Keys.CONTROL).perform()
            time.sleep(3)
            arquivo = self._aguardar_download()
            if arquivo: return arquivo
            
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys('s').key_up(Keys.SHIFT).key_up(Keys.CONTROL).perform()
            time.sleep(3)
            arquivo = self._aguardar_download()
            if arquivo: return arquivo
            
            return None
        except Exception:
            return None

    def _aguardar_download(self, timeout=10) -> Optional[str]:
        """Aguarda o download ser concluído e retorna o nome do arquivo, com renomeação."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    arquivos_atuais = set(os.listdir(self.pasta_download))
                    novos_arquivos = arquivos_atuais - self.arquivos_antes
                    
                    for arquivo in novos_arquivos:
                        caminho_completo = os.path.join(self.pasta_download, arquivo)
                        if arquivo.endswith(('.crdownload', '.tmp', '.part')):
                            continue
                        if os.path.isfile(caminho_completo) and os.path.getsize(caminho_completo) > 1000:
                            time.sleep(1)
                            if os.path.getsize(caminho_completo) == os.path.getsize(caminho_completo):
                                arquivo_renomeado = self._renomear_arquivo_unico(arquivo)
                                return arquivo_renomeado if arquivo_renomeado else arquivo
                    time.sleep(0.5)
                except Exception:
                    time.sleep(0.5)
            
            arquivos_atuais = set(os.listdir(self.pasta_download))
            novos_arquivos = arquivos_atuais - self.arquivos_antes
            for arquivo in novos_arquivos:
                if not arquivo.endswith(('.crdownload', '.tmp', '.part')):
                    caminho_completo = os.path.join(self.pasta_download, arquivo)
                    if os.path.isfile(caminho_completo) and os.path.getsize(caminho_completo) > 1000:
                        arquivo_renomeado = self._renomear_arquivo_unico(arquivo)
                        return arquivo_renomeado if arquivo_renomeado else arquivo
            return None
        except Exception:
            return None

    def _renomear_arquivo_unico(self, nome_arquivo: str) -> Optional[str]:
        """Renomeia arquivo para evitar conflitos, usando timestamp + contador."""
        try:
            from datetime import datetime
            
            caminho_original = os.path.join(self.pasta_download, nome_arquivo)
            if not os.path.exists(caminho_original): return None
            
            nome_base, extensao = os.path.splitext(nome_arquivo)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            contador = str(self.extraction_count).zfill(3)
            
            formatos_nome = [
                f"dje_{contador}_{timestamp}{extensao}",
                f"documento_{contador}_{timestamp}{extensao}",
                f"pdf_{contador}_{timestamp}{extensao}"
            ]
            
            for novo_nome in formatos_nome:
                novo_caminho = os.path.join(self.pasta_download, novo_nome)
                if not os.path.exists(novo_caminho):
                    try:
                        os.rename(caminho_original, novo_caminho)
                        return novo_nome
                    except OSError:
                        continue
            
            contador_sufixo = 1
            while contador_sufixo < 1000:
                novo_nome = f"{nome_base}_{contador_sufixo:03d}{extensao}"
                novo_caminho = os.path.join(self.pasta_download, novo_nome)
                if not os.path.exists(novo_caminho):
                    try:
                        os.rename(caminho_original, novo_caminho)
                        return novo_nome
                    except OSError:
                        contador_sufixo += 1
                        continue
                else:
                    contador_sufixo += 1
            return nome_arquivo
        except Exception:
            return nome_arquivo

    def _registrar_arquivos_existentes(self):
        """Registra arquivos que já existem na pasta de download."""
        try:
            self.arquivos_antes = set(os.listdir(self.pasta_download))
        except:
            self.arquivos_antes = set()

    def _ler_pdf_baixado(self, nome_arquivo: str) -> str:
        """Lê o conteúdo textual de um arquivo PDF baixado."""
        try:
            caminho_arquivo = os.path.join(self.pasta_download, nome_arquivo)
            
            if PyPDF2:
                try:
                    with open(caminho_arquivo, 'rb') as file:
                        pdf_reader = PyPDF2.PdfReader(file)
                        texto = "".join(page.extract_text() + "\n" for page in pdf_reader.pages)
                        if texto.strip(): return texto
                except Exception: pass
            
            if pdfplumber:
                try:
                    with pdfplumber.open(caminho_arquivo) as pdf:
                        texto = "".join(page.extract_text() + "\n" for page in pdf.pages if page.extract_text())
                        if texto.strip(): return texto
                except Exception: pass
            
            tamanho = os.path.getsize(caminho_arquivo)
            return f"PDF_BAIXADO: {nome_arquivo} ({tamanho} bytes)"
            
        except Exception:
            return ""

    def _is_conteudo_valido(self, conteudo: str) -> bool:
        """Verifica se o conteúdo extraído é válido e relevante."""
        if not conteudo: return False
        
        indicadores = ["Publicação Oficial", "Diário da Justiça", "Processo", "ADV:", "Vistos", "R$", "PDF_BAIXADO"]
        tamanho_ok = len(conteudo.strip()) > 100
        tem_indicadores = sum(1 for ind in indicadores if ind in conteudo) >= 1
        
        return tamanho_ok and tem_indicadores

    def _garantir_contexto_principal(self):
        """Garante que o driver está no contexto principal (fora de iframes)."""
        try:
            self.driver.switch_to.default_content()
        except:
            pass

    def _criar_fallback(self) -> str:
        """Cria uma string de fallback com informações básicas quando o download falha."""
        try:
            titulo = self.driver.title
            url = self.driver.current_url
            return f"DOWNLOAD_FALHOU: Título='{titulo}', URL='{url}', Tentativa={self.extraction_count}"
        except:
            return "DOWNLOAD_FALHOU - Erro genérico"

    def reset_contador(self):
        """Reseta o contador de extrações."""
        self.extraction_count = 0

    def limpar_downloads_antigos(self, dias=7):
        """Remove arquivos PDF baixados com mais de N dias."""
        try:
            import time
            agora = time.time()
            dias_em_segundos = dias * 24 * 60 * 60
            for arquivo in os.listdir(self.pasta_download):
                caminho = os.path.join(self.pasta_download, arquivo)
                if os.path.isfile(caminho):
                    if agora - os.stat(caminho).st_mtime > dias_em_segundos:
                        os.remove(caminho)
        except Exception:
            pass

    def listar_downloads(self):
        """Lista os arquivos PDF na pasta de downloads."""
        try:
            arquivos = os.listdir(self.pasta_download)
            for arquivo in sorted(arquivos):
                caminho = os.path.join(self.pasta_download, arquivo)
                if os.path.isfile(caminho):
                    tamanho = os.path.getsize(caminho)
        except Exception:
            pass
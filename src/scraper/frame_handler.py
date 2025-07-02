import time
import pyperclip
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import MoveTargetOutOfBoundsException

class FrameHandler:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.extraction_count = 0

    def set_driver(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def extrair_conteudo_pdf(self) -> str:
        self.extraction_count += 1
        
        try:
            self._limpar_estado_completo()
            time.sleep(5)
            
            conteudo = self._extrair_via_frame_dinamico()
            if self._is_conteudo_valido(conteudo):
                return conteudo
            
            conteudo = self._extrair_via_javascript_otimizado()
            if self._is_conteudo_valido(conteudo):
                return conteudo
            
            conteudo = self._extrair_via_foco_body()
            if self._is_conteudo_valido(conteudo):
                return conteudo
            
            return self._criar_fallback()
            
        except Exception:
            return ""
        finally:
            self._garantir_contexto_principal()

    def _limpar_estado_completo(self):
        try:
            self.driver.switch_to.default_content()
            for _ in range(3):
                pyperclip.copy("")
                time.sleep(0.2)
            try:
                ActionChains(self.driver).move_to_element(self.driver.find_element(By.TAG_NAME, "body")).perform()
            except:
                pass
            self.driver.execute_script("window.getSelection().removeAllRanges();")
        except Exception:
            pass

    def _extrair_via_frame_dinamico(self) -> str:
        try:
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "bottomFrame")))
            time.sleep(3)
            frame_ready = self.driver.execute_script("""
                return document.readyState === 'complete' && 
                       document.body && 
                       document.body.innerText.length > 0;
            """)
            if not frame_ready:
                time.sleep(5)
            conteudo = self._executar_copia_dinamica()
            self.driver.switch_to.default_content()
            return conteudo
        except Exception:
            self._garantir_contexto_principal()
            return ""

    def _executar_copia_dinamica(self) -> str:
        conteudo_melhor = ""
        for tentativa in range(3):
            try:
                pyperclip.copy("")
                time.sleep(0.5)
                if tentativa == 0:
                    conteudo_atual = self._clicar_centro_viewport()
                elif tentativa == 1:
                    conteudo_atual = self._clicar_body_frame()
                else:
                    conteudo_atual = self._copia_sem_clique()
                if conteudo_atual and len(conteudo_atual) > len(conteudo_melhor):
                    conteudo_melhor = conteudo_atual
                if self._is_conteudo_valido(conteudo_melhor):
                    break
            except Exception:
                continue
        return conteudo_melhor

    def _clicar_centro_viewport(self) -> str:
        try:
            viewport_size = self.driver.execute_script("""
                return {
                    width: window.innerWidth,
                    height: window.innerHeight
                };
            """)
            center_x = viewport_size['width'] // 2
            center_y = viewport_size['height'] // 2
            actions = ActionChains(self.driver)
            actions.move_by_offset(center_x, center_y).click().perform()
            time.sleep(1)
            return self._executar_ctrl_a_c()
        except MoveTargetOutOfBoundsException:
            return self._clicar_coordenadas_seguras()
        except Exception:
            return ""

    def _clicar_body_frame(self) -> str:
        try:
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            actions = ActionChains(self.driver)
            actions.move_to_element(body_element).click().perform()
            time.sleep(1)
            return self._executar_ctrl_a_c()
        except Exception:
            return ""

    def _clicar_coordenadas_seguras(self) -> str:
        try:
            actions = ActionChains(self.driver)
            actions.move_by_offset(100, 100).click().perform()
            time.sleep(1)
            return self._executar_ctrl_a_c()
        except Exception:
            return ""

    def _copia_sem_clique(self) -> str:
        try:
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.TAB).perform()
            time.sleep(1)
            return self._executar_ctrl_a_c()
        except Exception:
            return ""

    def _executar_ctrl_a_c(self) -> str:
        try:
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            time.sleep(1)
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('c').key_up(Keys.CONTROL).perform()
            time.sleep(1.5)
            conteudo = pyperclip.paste()
            return conteudo or ""
        except Exception:
            return ""

    def _extrair_via_foco_body(self) -> str:
        try:
            self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "bottomFrame")))
            self.driver.execute_script("""
                document.body.focus();
                document.execCommand('selectAll');
            """)
            time.sleep(1)
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('c').key_up(Keys.CONTROL).perform()
            time.sleep(1.5)
            conteudo = pyperclip.paste()
            self.driver.switch_to.default_content()
            return conteudo or ""
        except Exception:
            self._garantir_contexto_principal()
            return ""

    def _extrair_via_javascript_otimizado(self) -> str:
        try:
            js_script = """
            try {
                var bottomFrame = document.getElementsByName('bottomFrame')[0];
                if (bottomFrame && bottomFrame.contentDocument) {
                    var doc = bottomFrame.contentDocument;
                    var texto = doc.body.innerText || doc.body.textContent || '';
                    if (texto.length > 500) return texto;
                }
                var frames = document.getElementsByTagName('frame');
                for (var i = 0; i < frames.length; i++) {
                    try {
                        var frameDoc = frames[i].contentDocument;
                        if (frameDoc && frameDoc.body) {
                            var texto = frameDoc.body.innerText || frameDoc.body.textContent || '';
                            if (texto.length > 500) return texto;
                        }
                    } catch (e) {}
                }
                var iframes = document.getElementsByTagName('iframe');
                for (var i = 0; i < iframes.length; i++) {
                    try {
                        var iframeDoc = iframes[i].contentDocument;
                        if (iframeDoc && iframeDoc.body) {
                            var texto = iframeDoc.body.innerText || iframeDoc.body.textContent || '';
                            if (texto.length > 500) return texto;
                        }
                    } catch (e) {}
                }
                return '';
            } catch (e) {
                return '';
            }
            """
            resultado = self.driver.execute_script(js_script)
            if resultado and len(resultado.strip()) > 500:
                return resultado
        except Exception:
            pass
        return ""

    def _is_conteudo_valido(self, conteudo: str) -> bool:
        if not conteudo:
            return False
        indicadores = ["Publicação Oficial", "Diário da Justiça", "Processo", "ADV:", "Vistos", "R$"]
        tamanho_ok = len(conteudo.strip()) > 1000
        tem_indicadores = sum(1 for ind in indicadores if ind in conteudo) >= 3
        return tamanho_ok and tem_indicadores

    def _garantir_contexto_principal(self):
        try:
            self.driver.switch_to.default_content()
        except:
            pass

    def _criar_fallback(self) -> str:
        try:
            titulo = self.driver.title
            url = self.driver.current_url
            return f"EXTRAÇÃO FALHOU\nTítulo: {titulo}\nURL: {url}\nTentativa: {self.extraction_count}\nMétodo: Todos os métodos falharam\n"
        except:
            return "EXTRAÇÃO FALHOU - Erro total"

    def reset_contador(self):
        self.extraction_count = 0
# frame_handler.py
"""
Módulo responsável pela extração de conteúdo de frames/PDFs
Versão com coordenadas dinâmicas para evitar "move target out of bounds"
"""

import time
import pyperclip
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, MoveTargetOutOfBoundsException


class FrameHandler:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.extraction_count = 0

    def set_driver(self, driver, wait):
        """Configura driver e wait"""
        self.driver = driver
        self.wait = wait

    def extrair_conteudo_pdf(self) -> str:
        """
        Extrai conteúdo do PDF com coordenadas dinâmicas
        """
        self.extraction_count += 1
        print(f"      📋 Extraindo PDF #{self.extraction_count}...")
        
        try:
            # LIMPEZA COMPLETA ANTES DE CADA EXTRAÇÃO
            self._limpar_estado_completo()
            
            # Aguardar carregamento da página
            time.sleep(5)
            
            # Método principal: Frame bottomFrame com coordenadas dinâmicas
            conteudo = self._extrair_via_frame_dinamico()
            if self._is_conteudo_valido(conteudo):
                print(f"         ✅ Sucesso via frame: {len(conteudo)} chars")
                return conteudo
            
            # Método backup: JavaScript
            conteudo = self._extrair_via_javascript_otimizado()
            if self._is_conteudo_valido(conteudo):
                print(f"         ✅ Sucesso via JavaScript: {len(conteudo)} chars")
                return conteudo
            
            # Método alternativo: Foco no body do frame
            conteudo = self._extrair_via_foco_body()
            if self._is_conteudo_valido(conteudo):
                print(f"         ✅ Sucesso via foco body: {len(conteudo)} chars")
                return conteudo
            
            # Se falhou, retornar informações básicas
            return self._criar_fallback()
            
        except Exception as e:
            print(f"         ❌ Erro na extração: {e}")
            return ""
        finally:
            # Garantir que voltamos ao contexto principal
            self._garantir_contexto_principal()

    def _limpar_estado_completo(self):
        """Limpa completamente o estado antes de cada extração"""
        try:
            # 1. Voltar ao contexto principal
            self.driver.switch_to.default_content()
            
            # 2. Limpar clipboard múltiplas vezes
            for _ in range(3):
                pyperclip.copy("")
                time.sleep(0.2)
            
            # 3. Resetar posição do mouse para coordenada segura
            try:
                ActionChains(self.driver).move_to_element(self.driver.find_element(By.TAG_NAME, "body")).perform()
            except:
                pass
            
            # 4. Garantir que não há seleções ativas
            self.driver.execute_script("window.getSelection().removeAllRanges();")
            
            print("         🧹 Estado limpo")
            
        except Exception as e:
            print(f"         ⚠️ Erro na limpeza: {e}")

    def _extrair_via_frame_dinamico(self) -> str:
        """Extrai via frame bottomFrame com coordenadas dinâmicas"""
        try:
            print("         🖼️ Tentando frame bottomFrame dinâmico...")
            
            # Aguardar e trocar para frame bottomFrame
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, "bottomFrame"))
            )
            
            # Aguardar carregamento do conteúdo do frame
            time.sleep(3)
            print("         ✅ Entrou no frame bottomFrame")
            
            # Verificar se o frame tem conteúdo carregado
            frame_ready = self.driver.execute_script("""
                return document.readyState === 'complete' && 
                       document.body && 
                       document.body.innerText.length > 0;
            """)
            
            if not frame_ready:
                print("         ⏳ Aguardando carregamento do frame...")
                time.sleep(5)
            
            # Método de cópia com coordenadas dinâmicas
            conteudo = self._executar_copia_dinamica()
            
            # Voltar para frame principal
            self.driver.switch_to.default_content()
            
            return conteudo
            
        except Exception as e:
            print(f"         ❌ Erro frame bottomFrame: {e}")
            self._garantir_contexto_principal()
            return ""

    def _executar_copia_dinamica(self) -> str:
        """Executa a cópia com coordenadas calculadas dinamicamente"""
        conteudo_melhor = ""
        
        for tentativa in range(3):
            try:
                print(f"         🔄 Tentativa {tentativa + 1}/3...")
                
                # Limpar clipboard antes da tentativa
                pyperclip.copy("")
                time.sleep(0.5)
                
                # Método 1: Clicar no centro do viewport do frame
                if tentativa == 0:
                    conteudo_atual = self._clicar_centro_viewport()
                # Método 2: Clicar no body do frame
                elif tentativa == 1:
                    conteudo_atual = self._clicar_body_frame()
                # Método 3: Usar apenas teclado sem clicar
                else:
                    conteudo_atual = self._copia_sem_clique()
                
                # Verificar se o conteúdo é melhor que o anterior
                if conteudo_atual and len(conteudo_atual) > len(conteudo_melhor):
                    conteudo_melhor = conteudo_atual
                    print(f"         📈 Melhor conteúdo: {len(conteudo_melhor)} chars")
                
                # Se já temos conteúdo bom, parar
                if self._is_conteudo_valido(conteudo_melhor):
                    break
                    
            except Exception as e:
                print(f"         ⚠️ Erro na tentativa {tentativa + 1}: {e}")
                continue
        
        return conteudo_melhor

    def _clicar_centro_viewport(self) -> str:
        """Clica no centro do viewport atual"""
        try:
            # Obter dimensões do viewport
            viewport_size = self.driver.execute_script("""
                return {
                    width: window.innerWidth,
                    height: window.innerHeight
                };
            """)
            
            # Calcular centro do viewport
            center_x = viewport_size['width'] // 2
            center_y = viewport_size['height'] // 2
            
            print(f"         👆 Clicando no centro: ({center_x}, {center_y})")
            
            # Clicar no centro
            actions = ActionChains(self.driver)
            actions.move_by_offset(center_x, center_y).click().perform()
            time.sleep(1)
            
            return self._executar_ctrl_a_c()
            
        except MoveTargetOutOfBoundsException:
            print("         ⚠️ Centro fora dos limites, tentando coordenadas menores")
            return self._clicar_coordenadas_seguras()
        except Exception as e:
            print(f"         ❌ Erro ao clicar no centro: {e}")
            return ""

    def _clicar_body_frame(self) -> str:
        """Clica diretamente no elemento body do frame"""
        try:
            print("         👆 Clicando no body do frame...")
            
            # Encontrar e clicar no body
            body_element = self.driver.find_element(By.TAG_NAME, "body")
            
            actions = ActionChains(self.driver)
            actions.move_to_element(body_element).click().perform()
            time.sleep(1)
            
            return self._executar_ctrl_a_c()
            
        except Exception as e:
            print(f"         ❌ Erro ao clicar no body: {e}")
            return ""

    def _clicar_coordenadas_seguras(self) -> str:
        """Clica em coordenadas seguras menores"""
        try:
            print("         👆 Usando coordenadas seguras (100, 100)")
            
            actions = ActionChains(self.driver)
            actions.move_by_offset(100, 100).click().perform()
            time.sleep(1)
            
            return self._executar_ctrl_a_c()
            
        except Exception as e:
            print(f"         ❌ Erro com coordenadas seguras: {e}")
            return ""

    def _copia_sem_clique(self) -> str:
        """Tenta copiar sem clicar, apenas usando teclado"""
        try:
            print("         ⌨️ Copiando sem clique...")
            
            # Dar foco ao frame usando Tab
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.TAB).perform()
            time.sleep(1)
            
            return self._executar_ctrl_a_c()
            
        except Exception as e:
            print(f"         ❌ Erro na cópia sem clique: {e}")
            return ""

    def _executar_ctrl_a_c(self) -> str:
        """Executa Ctrl+A e Ctrl+C"""
        try:
            # Selecionar tudo
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
            time.sleep(1)
            
            # Copiar
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('c').key_up(Keys.CONTROL).perform()
            time.sleep(1.5)
            
            # Ler clipboard
            conteudo = pyperclip.paste()
            return conteudo or ""
            
        except Exception as e:
            print(f"         ❌ Erro no Ctrl+A/C: {e}")
            return ""

    def _extrair_via_foco_body(self) -> str:
        """Método alternativo focando no body sem cliques"""
        try:
            print("         🎯 Tentando foco no body...")
            
            # Trocar para frame bottomFrame
            self.wait.until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, "bottomFrame"))
            )
            
            # Usar JavaScript para dar foco e executar seleção
            self.driver.execute_script("""
                document.body.focus();
                document.execCommand('selectAll');
            """)
            
            time.sleep(1)
            
            # Copiar
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('c').key_up(Keys.CONTROL).perform()
            time.sleep(1.5)
            
            # Ler clipboard
            conteudo = pyperclip.paste()
            
            # Voltar para frame principal
            self.driver.switch_to.default_content()
            
            return conteudo or ""
            
        except Exception as e:
            print(f"         ❌ Erro no foco body: {e}")
            self._garantir_contexto_principal()
            return ""

    def _extrair_via_javascript_otimizado(self) -> str:
        """JavaScript otimizado com múltiplas estratégias"""
        try:
            print("         🔧 Tentando JavaScript otimizado...")
            
            # Estratégia 1: Acesso direto ao frame
            js_script = """
            try {
                var bottomFrame = document.getElementsByName('bottomFrame')[0];
                if (bottomFrame && bottomFrame.contentDocument) {
                    var doc = bottomFrame.contentDocument;
                    var texto = doc.body.innerText || doc.body.textContent || '';
                    if (texto.length > 500) return texto;
                }
                
                // Estratégia 2: Buscar por outros frames
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
                
                // Estratégia 3: Buscar por iframes
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
                print(f"         ✅ JavaScript: {len(resultado)} chars")
                return resultado
            else:
                print(f"         ⚠️ JavaScript: {len(resultado or '')} chars")
                
        except Exception as e:
            print(f"         ❌ Erro JavaScript: {e}")
        
        return ""

    def _is_conteudo_valido(self, conteudo: str) -> bool:
        """Verifica se o conteúdo extraído é válido"""
        if not conteudo:
            return False
        
        # Indicadores de sucesso
        indicadores = [
            "Publicação Oficial",
            "Diário da Justiça",
            "Processo",
            "ADV:",
            "Vistos",
            "R$"
        ]
        
        # Verificar tamanho e indicadores
        tamanho_ok = len(conteudo.strip()) > 1000
        tem_indicadores = sum(1 for ind in indicadores if ind in conteudo) >= 3
        
        return tamanho_ok and tem_indicadores

    def _garantir_contexto_principal(self):
        """Garante que estamos no contexto principal"""
        try:
            self.driver.switch_to.default_content()
        except:
            pass

    def _criar_fallback(self) -> str:
        """Cria informações básicas quando extração falha"""
        try:
            titulo = self.driver.title
            url = self.driver.current_url
            
            return f"""EXTRAÇÃO FALHOU
Título: {titulo}
URL: {url}
Tentativa: {self.extraction_count}
Método: Todos os métodos falharam
"""
        except:
            return "EXTRAÇÃO FALHOU - Erro total"

    def reset_contador(self):
        """Reseta o contador para nova sessão"""
        self.extraction_count = 0
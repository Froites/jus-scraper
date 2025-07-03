import time
import os
import json
import shutil
from typing import List, Dict, Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Importações para a API e modelos
from api.api_client import JusAPIClient
from models.publicacao import Publicacao
from extraction.data_extractor import DataExtractor

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from .frame_handler import FrameHandler
except ImportError:
    print("Erro: frame_handler.py não encontrado. Certifique-se de que está na pasta correta ou o caminho de importação está certo.")
    exit(1)


DJE_BASE_URL = 'https://dje.tjsp.jus.br/cdje/index.do'


class DJEScraperDownload:
    def __init__(self, pasta_download="./downloads_dje"):
        self.driver = None
        self.wait = None
        self.pasta_download = os.path.abspath(pasta_download)
        self.janelas_abertas = []
        
        os.makedirs(self.pasta_download, exist_ok=True)
        os.makedirs(os.path.join(self.pasta_download, "duplicatas"), exist_ok=True)

        self.frame_handler = FrameHandler(pasta_download)
        self.data_extractor = DataExtractor()

    def _setup_driver(self):
        """Configura o navegador Chrome para automação e downloads."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        
        prefs = {
            "download.default_directory": self.pasta_download,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        self.frame_handler.set_driver(self.driver, self.wait)

    def _configurar_busca(self, data: str):
        """Preenche o formulário de busca no site do DJE."""
        self.wait.until(EC.presence_of_element_located((By.NAME, "dadosConsulta.dtInicio")))
        self.driver.execute_script(f"""
            document.getElementsByName('dadosConsulta.dtInicio')[0].value = '{data}';
            document.getElementsByName('dadosConsulta.dtFim')[0].value = '{data}';
            var select = document.getElementsByName('dadosConsulta.cdCaderno')[0];
            for(var i = 0; i < select.options.length; i++) {{
                if(select.options[i].text.includes('caderno 3') && 
                   select.options[i].text.includes('Capital - Parte I')) {{
                    select.selectedIndex = i;
                    break;
                }}
            }}
            document.getElementsByName('dadosConsulta.pesquisaLivre')[0].value = '"RPV" e "pagamento pelo INSS"';
        """)

    def _executar_busca(self):
        """Clica no botão de pesquisa e aguarda resultados."""
        btn_pesquisar = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Pesquisar']"))
        )
        btn_pesquisar.click()
        time.sleep(5)

    def _encontrar_links(self) -> List:
        """Encontra todos os links de 'Visualizar' na página de resultados."""
        links = self.driver.find_elements(By.XPATH, "//a[@title='Visualizar']")
        return links

    def _processar_link(self, link, index: int) -> Optional[Publicacao]:
        """
        Processa um único link, baixa o PDF, extrai o conteúdo e retorna um objeto Publicacao.
        """
        original_window = self.driver.current_window_handle
        conteudo = ""
        
        try:
            self.frame_handler._registrar_arquivos_existentes()
            self.driver.execute_script("arguments[0].click();", link)
            
            start_time = time.time()
            while len(self.driver.window_handles) <= 1 and time.time() - start_time < 15:
                time.sleep(0.5)
            
            if len(self.driver.window_handles) <= 1:
                return None
            
            nova_janela = None
            for window in self.driver.window_handles:
                if window != original_window:
                    nova_janela = window
                    break
            
            if nova_janela:
                self.driver.switch_to.window(nova_janela)
                self.janelas_abertas.append(nova_janela)
                
                conteudo = self.frame_handler.extrair_conteudo_pdf()
                time.sleep(2)
                
                self.driver.close()
                if nova_janela in self.janelas_abertas:
                    self.janelas_abertas.remove(nova_janela)
            
            self.driver.switch_to.window(original_window)
            
        except Exception:
            try:
                self.driver.switch_to.window(original_window)
            except:
                pass
            return None
        
        if self.data_extractor.is_conteudo_relevante(conteudo):
            dados = self.data_extractor.extrair_dados(conteudo)
            arquivo_pdf_nome = self._identificar_ultimo_pdf_por_tempo()
            
            return Publicacao(
                numero_processo=dados['processo'],
                data_disponibilizacao=dados['data'],
                autores=dados['autores'],
                advogados=dados['advogados'],
                valor_principal=dados['valores']['principal'],
                valor_juros=dados['valores']['juros'],
                honorarios=dados['valores']['honorarios'],
                conteudo_completo=conteudo, # Passando o conteúdo completo aqui
                url_publicacao=self.driver.current_url,
                arquivo_cache=arquivo_pdf_nome # Usando arquivo_cache como no modelo
            )
        return None

    def _identificar_ultimo_pdf_por_tempo(self) -> Optional[str]:
        """Identifica o PDF mais recente por data de modificação na pasta de downloads."""
        try:
            arquivos = [f for f in os.listdir(self.pasta_download) 
                       if f.endswith('.pdf') and os.path.isfile(os.path.join(self.pasta_download, f))]
            if not arquivos: return None
            
            arquivos_com_data = []
            for arquivo in arquivos:
                caminho = os.path.join(self.pasta_download, arquivo)
                try:
                    data_mod = os.path.getmtime(caminho)
                    tamanho = os.path.getsize(caminho)
                    arquivos_com_data.append((data_mod, arquivo, tamanho))
                except: continue
            
            if arquivos_com_data:
                arquivos_com_data.sort(reverse=True)
                for data_mod, arquivo, tamanho in arquivos_com_data:
                    if tamanho > 1000: return arquivo
            return None
        except Exception:
            return None

    def executar(self, data_busca: str) -> List[Publicacao]:
        """Executa o processo completo de scraping do site, incluindo download e extração."""
        try:
            self._setup_driver()
            self.driver.get(DJE_BASE_URL)
            self._configurar_busca(data_busca)
            self._executar_busca()
            
            links = self._encontrar_links()
            publicacoes = []
            processos_encontrados = set()
            
            self.frame_handler.reset_contador()
            
            for i, link in enumerate(links):
                if i > 0 and i % 3 == 0: self._limpar_janelas_extras(); time.sleep(2)
                
                publicacao = self._processar_link(link, i)
                
                if publicacao:
                    numero_processo = publicacao.numero_processo #
                    if numero_processo and numero_processo in processos_encontrados:
                        if publicacao.arquivo_cache: self._mover_pdf_duplicado(publicacao.arquivo_cache) #
                        continue
                    
                    if numero_processo: processos_encontrados.add(numero_processo)
                    publicacoes.append(publicacao)
                
                time.sleep(4) # Pausa maior entre processamentos para estabilidade
            
            return publicacoes
            
        except Exception:
            return []
        finally:
            self._limpar_janelas_extras()
            if self.driver: self.driver.quit()
            self._mostrar_resumo_downloads()

    def _mover_pdf_duplicado(self, nome_arquivo: str):
        """Move um PDF duplicado para uma pasta de duplicatas."""
        if not nome_arquivo: return
        try:
            pasta_duplicatas = os.path.join(self.pasta_download, "duplicatas")
            os.makedirs(pasta_duplicatas, exist_ok=True)
            origem = os.path.join(self.pasta_download, nome_arquivo)
            destino = os.path.join(pasta_duplicatas, nome_arquivo)
            
            if os.path.exists(destino):
                nome_base, ext = os.path.splitext(nome_arquivo)
                timestamp = datetime.now().strftime("%H%M%S")
                novo_nome = f"{nome_base}_dup_{timestamp}{ext}"
                destino = os.path.join(pasta_duplicatas, novo_nome)
            
            if os.path.exists(origem): shutil.move(origem, destino)
        except Exception:
            pass # Log errors
            
    def verificar_duplicatas_existentes(self, publicacoes: List[Publicacao]) -> List[Publicacao]:
        """Remove duplicatas de uma lista de publicações baseado no número do processo."""
        processos_vistos = set()
        publicacoes_unicas = []
        for publicacao in publicacoes:
            numero_processo = publicacao.numero_processo #
            if numero_processo and numero_processo in processos_vistos:
                if publicacao.arquivo_cache: self._mover_pdf_duplicado(publicacao.arquivo_cache) #
            else:
                if numero_processo: processos_vistos.add(numero_processo)
                publicacoes_unicas.append(publicacao)
        return publicacoes_unicas

    def processar_pdfs_baixados(self) -> List[Publicacao]:
        """Processa PDFs já baixados na pasta de download."""
        try:
            arquivos_pdf = [f for f in os.listdir(self.pasta_download) 
                           if f.endswith('.pdf') and os.path.isfile(os.path.join(self.pasta_download, f))]
            publicacoes = []
            if not arquivos_pdf: return []
            
            for arquivo in arquivos_pdf:
                caminho_completo = os.path.join(self.pasta_download, arquivo)
                conteudo = self._ler_pdf_arquivo(caminho_completo)
                
                if self.data_extractor.is_conteudo_relevante(conteudo):
                    dados = self.data_extractor.extrair_dados(conteudo)
                    if self.data_extractor.validar_extracao_completa(dados):
                        publicacao = Publicacao(
                            numero_processo=dados['processo'],
                            data_disponibilizacao=dados['data'],
                            autores=dados['autores'],
                            advogados=dados['advogados'],
                            valor_principal=dados['valores']['principal'],
                            valor_juros=dados['valores']['juros'],
                            honorarios=dados['valores']['honorarios'],
                            conteudo_completo=conteudo,
                            arquivo_cache=arquivo
                        )
                        publicacoes.append(publicacao)
            
            publicacoes_unicas = self.verificar_duplicatas_existentes(publicacoes)
            return publicacoes_unicas
        except Exception:
            return []

    def _mostrar_resumo_downloads(self):
        """Exibe um resumo dos arquivos baixados na pasta de downloads."""
        try:
            arquivos = [f for f in os.listdir(self.pasta_download) 
                       if f.endswith('.pdf') and os.path.isfile(os.path.join(self.pasta_download, f))]
            if not arquivos: return
            
            arquivos_info = []
            for arquivo in arquivos:
                caminho = os.path.join(self.pasta_download, arquivo)
                try:
                    tamanho = os.path.getsize(caminho)
                    data_mod = os.path.getmtime(caminho)
                    arquivos_info.append((data_mod, arquivo, tamanho))
                except: continue
            
            arquivos_info.sort(reverse=True)
            total_tamanho = sum(info[2] for info in arquivos_info)
            
        except Exception:
            pass

    def _limpar_janelas_extras(self):
        """Fecha janelas extras do navegador, voltando para a janela principal."""
        try:
            janela_principal = self.driver.window_handles[0]
            for janela in self.driver.window_handles[1:]:
                try: self.driver.switch_to.window(janela); self.driver.close()
                except: pass
            self.driver.switch_to.window(janela_principal)
            self.janelas_abertas.clear()
        except Exception:
            pass

    def _ler_pdf_arquivo(self, caminho_arquivo: str) -> str:
        """Lê o conteúdo textual de um arquivo PDF."""
        try:
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
            
            return ""
        except Exception:
            return ""

    def listar_downloads(self):
        """Lista os arquivos baixados na pasta de downloads."""
        try:
            arquivos = os.listdir(self.pasta_download)
            if not arquivos: return
            # Formatting (kept minimal)
        except Exception:
            pass

    def limpar_downloads(self, dias=7):
        """Remove arquivos PDF antigos da pasta de downloads."""
        try:
            agora = time.time()
            dias_em_segundos = dias * 24 * 60 * 60
            for arquivo in os.listdir(self.pasta_download):
                caminho = os.path.join(self.pasta_download, arquivo)
                if os.path.isfile(caminho):
                    if agora - os.path.getmtime(caminho) > dias_em_segundos:
                        os.remove(caminho)
        except Exception:
            pass


def main():
    print("DJE Scraper - Processamento de PDFs e Envio à API")
    print("="*60)
    
    pasta_download = "./downloads_dje"
    scraper = DJEScraperDownload(pasta_download)

    print("\nOPÇÕES:")
    print("1. Extrair do site (com download)")
    print("2. Processar PDFs já baixados")
    print("3. Listar downloads")
    print("4. Limpar downloads antigos")
    print("5. Enviar publicações para a API (após extração ou processamento de PDFs)")
    
    opcao = input("\nEscolha (1-5): ").strip()
    
    if opcao == "3":
        scraper.listar_downloads()
        return
    elif opcao == "4":
        dias = input("Limpar arquivos com mais de quantos dias? (padrão: 7): ").strip()
        dias = int(dias) if dias.isdigit() else 7
        scraper.limpar_downloads(dias)
        return
    
    publicacoes = []
    
    if opcao == "2":
        publicacoes = scraper.processar_pdfs_baixados()
    elif opcao == "1":
        data_busca = input("Data para busca (formato DD/MM/AAAA) [13/11/2024]: ").strip()
        if not data_busca: data_busca = "13/11/2024"
        publicacoes = scraper.executar(data_busca)
    elif opcao == "5":
        print("Processando PDFs existentes antes de enviar para a API...")
        publicacoes = scraper.processar_pdfs_baixados()
        if not publicacoes:
            print("Nenhuma publicação encontrada para enviar para a API. Considere usar a opção 1 ou 2 primeiro.")
    else:
        print("Opção inválida.")
        return

    if publicacoes:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo_json = f"resultados_download_{timestamp}.json"
        
        # O arquivo será salvo no diretório atual
        with open(nome_arquivo_json, 'w', encoding='utf-8') as f:
            json.dump([pub.to_dict() for pub in publicacoes], f, ensure_ascii=False, indent=2)
        
        print(f"Resultados salvos em: {nome_arquivo_json}")
        
        # --- ENVIO PARA A API ---
        if publicacoes and (opcao == "1" or opcao == "2" or opcao == "5"):
            print("\nIniciando envio para a API...")
            api_client = JusAPIClient()
            
            if not api_client.testar_conexao():
                print("ERRO: Não foi possível conectar à API. Verifique se a API está rodando.")
            else:
                resultado_envio = api_client.enviar_lote_publicacoes(publicacoes)
                print(f"Envio para API concluído: Sucessos={resultado_envio['sucessos']}, Erros={resultado_envio['erros']}")
    else:
        print("Nenhuma publicação relevante encontrada.")


if __name__ == "__main__":
    main()
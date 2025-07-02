# src/scraper/dje_scraper.py - Versão com imports corrigidos
#!/usr/bin/env python3
"""
DJE Scraper - Versão Otimizada e Performática
Foco na estabilidade da extração sequencial
"""

import time
import os
from typing import List
import json
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Imports locais
from extraction.data_extractor import DataExtractor
from scraper.frame_handler import FrameHandler
from scraper.cache_manager import CacheManager
from models.publicacao import Publicacao

# Configurações
DJE_BASE_URL = 'https://dje.tjsp.jus.br/cdje/index.do'


class DJEScraperOtimizado:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.cache_manager = CacheManager()
        self.frame_handler = FrameHandler()
        self.data_extractor = DataExtractor()
        self.janelas_abertas = []

    def _setup_driver(self):
        """Configuração otimizada do Chrome"""
        print("🚀 Configurando navegador...")
        chrome_options = Options()
        
        # Configurações de performance
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Acelerar carregamento
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Configurações de estabilidade
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        
        # Configurar handlers
        self.frame_handler.set_driver(self.driver, self.wait)
        print("✅ Navegador configurado")

    def _configurar_busca(self, data: str):
        """Configuração rápida da busca"""
        print("📝 Configurando busca...")
        
        self.wait.until(EC.presence_of_element_located((By.NAME, "dadosConsulta.dtInicio")))
        
        # JavaScript direto - sem verificações
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
        
        print("✅ Busca configurada")

    def _executar_busca(self):
        """Execução direta da busca"""
        print("🔍 Executando busca...")
        
        btn_pesquisar = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Pesquisar']"))
        )
        btn_pesquisar.click()
        
        # Aguardar resultados
        time.sleep(5)
        print("✅ Busca executada")

    def _encontrar_links(self) -> List:
        """Busca direta por links com title='Visualizar'"""
        print("🔍 Buscando links...")
        
        links = self.driver.find_elements(By.XPATH, "//a[@title='Visualizar']")
        print(f"✅ Encontrados {len(links)} links")
        return links

    def _processar_link(self, link, index: int) -> Publicacao:
        """Processamento otimizado de um link"""
        print(f"\n📄 Processando link {index + 1}...")
        
        text = link.text.strip()
        nome_cache = self.cache_manager.gerar_nome_cache(text, index)
        
        # Verificar cache primeiro
        conteudo = self.cache_manager.carregar_cache(nome_cache)
        
        if not conteudo:
            print("🌐 Extraindo do site...")
            
            # Lembrar janela original
            original_window = self.driver.current_window_handle
            
            try:
                # Clicar no link
                self.driver.execute_script("arguments[0].click();", link)
                
                # Aguardar nova janela com timeout
                start_time = time.time()
                while len(self.driver.window_handles) <= 1 and time.time() - start_time < 10:
                    time.sleep(0.5)
                
                if len(self.driver.window_handles) <= 1:
                    print("      ⚠️ Nova janela não abriu")
                    return None
                
                # Trocar para nova janela
                nova_janela = None
                for window in self.driver.window_handles:
                    if window != original_window:
                        nova_janela = window
                        break
                
                if nova_janela:
                    self.driver.switch_to.window(nova_janela)
                    self.janelas_abertas.append(nova_janela)
                    
                    # Extrair conteúdo
                    conteudo = self.frame_handler.extrair_conteudo_pdf()
                    
                    # Salvar cache se válido
                    if conteudo and len(conteudo.strip()) > 100:
                        url_atual = self.driver.current_url
                        self.cache_manager.salvar_cache(conteudo, nome_cache, url_atual, text)
                        print("      💾 Cache salvo")
                    
                    # Fechar janela atual
                    self.driver.close()
                    if nova_janela in self.janelas_abertas:
                        self.janelas_abertas.remove(nova_janela)
                
                # Voltar para janela original
                self.driver.switch_to.window(original_window)
                
            except Exception as e:
                print(f"      ❌ Erro ao processar link: {e}")
                # Garantir que voltamos à janela original
                try:
                    self.driver.switch_to.window(original_window)
                except:
                    pass
                return None
        
        # Processar dados se relevante
        if self.data_extractor.is_conteudo_relevante(conteudo):
            print("      ✅ Conteúdo relevante encontrado")
            dados = self.data_extractor.extrair_dados(conteudo)
            
            return Publicacao(
                numero_processo=dados['processo'],
                data_disponibilizacao=dados['data'],
                autores=dados['autores'],
                advogados=dados['advogados'],
                valor_principal=dados['valores']['principal'],
                valor_juros=dados['valores']['juros'],
                honorarios=dados['valores']['honorarios'],
                arquivo_cache=nome_cache
            )
        else:
            print("      ⚠️ Conteúdo não relevante")
        
        return None

    def _limpar_janelas_extras(self):
        """Limpa todas as janelas extras que possam ter ficado abertas"""
        try:
            janela_principal = self.driver.window_handles[0]
            
            for janela in self.driver.window_handles[1:]:
                try:
                    self.driver.switch_to.window(janela)
                    self.driver.close()
                except:
                    pass
            
            self.driver.switch_to.window(janela_principal)
            self.janelas_abertas.clear()
            
        except Exception as e:
            print(f"⚠️ Erro ao limpar janelas: {e}")

    def executar(self, data_busca: str) -> List[Publicacao]:
        """Execução principal otimizada"""
        try:
            self._setup_driver()
            
            print("🌐 Acessando DJE...")
            self.driver.get(DJE_BASE_URL)
            
            self._configurar_busca(data_busca)
            self._executar_busca()
            
            links = self._encontrar_links()
            
            print(f"📋 Processando {len(links)} links...")
            publicacoes = []
            
            # Resetar contador do frame handler
            self.frame_handler.reset_contador()
            
            for i, link in enumerate(links):
                print(f"\n🔄 Progresso: {i+1}/{len(links)}")
                
                # Limpar janelas extras a cada 5 links
                if i > 0 and i % 5 == 0:
                    print("🧹 Limpeza preventiva...")
                    self._limpar_janelas_extras()
                    time.sleep(2)
                
                publicacao = self._processar_link(link, i)
                
                if publicacao:
                    publicacoes.append(publicacao)
                    print(f"✅ Publicação {len(publicacoes)} extraída: {publicacao.numero_processo}")
                
                # Pausa entre processamentos
                time.sleep(2)
            
            return publicacoes
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            return []
        finally:
            # Limpeza final
            self._limpar_janelas_extras()
            if self.driver:
                self.driver.quit()

    def processar_cache(self) -> List[Publicacao]:
        """Processa apenas arquivos de cache válidos"""
        print("📂 Processando cache existente...")
        
        # Usar apenas arquivos válidos
        arquivos = self.cache_manager.listar_arquivos_validos()
        publicacoes = []
        
        if not arquivos:
            print("❌ Nenhum arquivo de cache válido encontrado")
            print("💡 Execute a extração do site primeiro ou limpe o cache falhado")
            return []
        
        print(f"📋 Encontrados {len(arquivos)} arquivos de cache válidos")
        
        for i, arquivo in enumerate(arquivos, 1):
            print(f"\n📄 Processando arquivo {i}/{len(arquivos)}")
            
            conteudo = self.cache_manager.carregar_cache(arquivo)
            
            if self.data_extractor.is_conteudo_relevante(conteudo):
                dados = self.data_extractor.extrair_dados(conteudo)
                
                # Validar se a extração foi bem-sucedida
                if self.data_extractor.validar_extracao_completa(dados):
                    publicacao = Publicacao(
                        numero_processo=dados['processo'],
                        data_disponibilizacao=dados['data'],
                        autores=dados['autores'],
                        advogados=dados['advogados'],
                        valor_principal=dados['valores']['principal'],
                        valor_juros=dados['valores']['juros'],
                        honorarios=dados['valores']['honorarios'],
                        arquivo_cache=arquivo
                    )
                    
                    publicacoes.append(publicacao)
                    print(f"✅ Extraído: {publicacao.numero_processo}")
                    
                    # Mostrar relatório da extração
                    relatorio = self.data_extractor.relatorio_extracao(dados)
                    print(relatorio)
                else:
                    print("⚠️ Extração incompleta - dados insuficientes")
            else:
                print("⚠️ Conteúdo não passou na validação")
        
        return publicacoes
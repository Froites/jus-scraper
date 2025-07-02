# cache_manager.py
"""
Módulo responsável pelo gerenciamento de cache
Operações otimizadas de leitura/escrita com melhor validação
"""

import os
import re
import time
from datetime import datetime
from typing import List, Optional, Tuple


class CacheManager:
    def __init__(self, cache_dir: str = "cache_pdfs"):
        self.cache_dir = cache_dir
        self._criar_diretorio()

    def _criar_diretorio(self):
        """Cria diretório de cache se não existir"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def gerar_nome_cache(self, link_text: str, index: int) -> str:
        """Gera nome único para arquivo de cache"""
        try:
            # Extrair página do texto do link
            match = re.search(r'Página\s+(\d+)', link_text)
            if match:
                pagina = match.group(1)
                nome = f"pdf_pagina_{pagina}_{index}.txt"
            else:
                nome = f"pdf_item_{index}_{int(time.time())}.txt"
                
            return os.path.join(self.cache_dir, nome)
            
        except Exception:
            return os.path.join(self.cache_dir, f"pdf_erro_{index}_{int(time.time())}.txt")

    def arquivo_existe(self, nome_arquivo: str) -> bool:
        """Verifica se arquivo existe e tem conteúdo mínimo"""
        return os.path.exists(nome_arquivo) and os.path.getsize(nome_arquivo) > 500

    def arquivo_e_valido(self, nome_arquivo: str) -> bool:
        """
        Verifica se arquivo é válido (não é falha de extração)
        """
        if not self.arquivo_existe(nome_arquivo):
            return False
        
        try:
            with open(nome_arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
                # Verificar se contém falha de extração
                if "EXTRAÇÃO FALHOU" in conteudo:
                    return False
                
                # Verificar tamanho mínimo do conteúdo extraído
                if "CONTEÚDO EXTRAÍDO:" in conteudo:
                    linhas = conteudo.split('\n')
                    inicio_conteudo = -1
                    for i, linha in enumerate(linhas):
                        if "CONTEÚDO EXTRAÍDO:" in linha:
                            inicio_conteudo = i + 2
                            break
                    
                    if inicio_conteudo > 0:
                        conteudo_extraido = '\n'.join(linhas[inicio_conteudo:])
                        return len(conteudo_extraido.strip()) > 6000
                
                return False
                
        except Exception:
            return False

    def carregar_cache(self, nome_arquivo: str) -> str:
        """Carrega conteúdo do arquivo de cache"""
        if not self.arquivo_existe(nome_arquivo):
            return ""
        
        try:
            with open(nome_arquivo, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
                
                # Encontrar onde começa o conteúdo
                inicio_conteudo = -1
                for i, linha in enumerate(linhas):
                    if "CONTEÚDO EXTRAÍDO:" in linha:
                        inicio_conteudo = i + 2  # Pular linha de separação
                        break
                
                if inicio_conteudo > 0:
                    conteudo = ''.join(linhas[inicio_conteudo:])
                    
                    # Log para debug
                    tamanho = len(conteudo.strip())
                    if tamanho < 6000:
                        print(f"         ⚠️ Cache pequeno: {tamanho} chars em {nome_arquivo}")
                    
                    return conteudo
                    
        except Exception as e:
            print(f"❌ Erro ao carregar cache {nome_arquivo}: {e}")
        
        return ""

    def salvar_cache(self, conteudo: str, nome_arquivo: str, url: str, link_text: str) -> bool:
        """Salva conteúdo no cache com validação"""
        try:
            # Verificar se vale a pena salvar
            tamanho_conteudo = len(conteudo.strip())
            
            # Determinar status do conteúdo
            if "EXTRAÇÃO FALHOU" in conteudo or tamanho_conteudo < 500:
                status = "❌ FALHA"
            elif tamanho_conteudo < 6000:
                status = "⚠️ PEQUENO"
            else:
                status = "✅ VÁLIDO"
            
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                f.write(f"CACHE PDF - DJE SCRAPER\n")
                f.write("=" * 70 + "\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Link Text: {link_text}\n")
                f.write(f"Tamanho: {tamanho_conteudo} caracteres\n")
                f.write(f"Status: {status}\n")
                f.write("=" * 70 + "\n\n")
                f.write("CONTEÚDO EXTRAÍDO:\n")
                f.write("-" * 70 + "\n")
                f.write(conteudo)
            
            print(f"         💾 Cache salvo: {status} ({tamanho_conteudo} chars)")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar cache: {e}")
            return False

    def listar_arquivos_cache(self) -> List[str]:
        """Lista todos os arquivos de cache disponíveis"""
        try:
            arquivos = []
            for arquivo in os.listdir(self.cache_dir):
                if arquivo.endswith('.txt'):
                    caminho_completo = os.path.join(self.cache_dir, arquivo)
                    if self.arquivo_existe(caminho_completo):
                        arquivos.append(caminho_completo)
            
            return sorted(arquivos)  # Ordenar para processamento consistente
            
        except Exception as e:
            print(f"❌ Erro ao listar cache: {e}")
            return []

    def listar_arquivos_validos(self) -> List[str]:
        """Lista apenas arquivos de cache válidos (sem falhas)"""
        try:
            arquivos_validos = []
            for arquivo in os.listdir(self.cache_dir):
                if arquivo.endswith('.txt'):
                    caminho_completo = os.path.join(self.cache_dir, arquivo)
                    if self.arquivo_e_valido(caminho_completo):
                        arquivos_validos.append(caminho_completo)
            
            return sorted(arquivos_validos)
            
        except Exception as e:
            print(f"❌ Erro ao listar cache válido: {e}")
            return []

    def limpar_cache_antigo(self, dias: int = 30):
        """Remove arquivos de cache mais antigos que X dias"""
        try:
            limite_tempo = time.time() - (dias * 24 * 60 * 60)
            removidos = 0
            
            for arquivo in os.listdir(self.cache_dir):
                caminho = os.path.join(self.cache_dir, arquivo)
                if os.path.isfile(caminho):
                    if os.path.getmtime(caminho) < limite_tempo:
                        os.remove(caminho)
                        removidos += 1
            
            if removidos > 0:
                print(f"🗑️ Removidos {removidos} arquivos de cache antigos")
                
        except Exception as e:
            print(f"❌ Erro ao limpar cache: {e}")

    def limpar_cache_falhado(self):
        """Remove arquivos de cache que falharam na extração"""
        try:
            removidos = 0
            
            for arquivo in os.listdir(self.cache_dir):
                if arquivo.endswith('.txt'):
                    caminho = os.path.join(self.cache_dir, arquivo)
                    if not self.arquivo_e_valido(caminho):
                        os.remove(caminho)
                        removidos += 1
            
            if removidos > 0:
                print(f"🗑️ Removidos {removidos} arquivos de cache com falha")
            else:
                print("✅ Nenhum arquivo de cache com falha encontrado")
                
        except Exception as e:
            print(f"❌ Erro ao limpar cache falhado: {e}")

    def estatisticas_cache(self) -> dict:
        """Retorna estatísticas detalhadas do cache"""
        try:
            arquivos_todos = []
            arquivos_validos = []
            arquivos_falhados = []
            
            for arquivo in os.listdir(self.cache_dir):
                if arquivo.endswith('.txt'):
                    caminho = os.path.join(self.cache_dir, arquivo)
                    if os.path.exists(caminho):
                        arquivos_todos.append(caminho)
                        
                        if self.arquivo_e_valido(caminho):
                            arquivos_validos.append(caminho)
                        else:
                            arquivos_falhados.append(caminho)
            
            # Calcular tamanhos
            tamanho_total = sum(os.path.getsize(f) for f in arquivos_todos)
            tamanho_validos = sum(os.path.getsize(f) for f in arquivos_validos)
            
            return {
                "total": len(arquivos_todos),
                "validos": len(arquivos_validos),
                "falhados": len(arquivos_falhados),
                "tamanho_mb": round(tamanho_total / (1024 * 1024), 2),
                "tamanho_validos_mb": round(tamanho_validos / (1024 * 1024), 2),
                "mais_recente": max(os.path.getmtime(f) for f in arquivos_todos) if arquivos_todos else 0,
                "taxa_sucesso": round((len(arquivos_validos) / len(arquivos_todos)) * 100, 1) if arquivos_todos else 0
            }
            
        except Exception as e:
            print(f"❌ Erro ao calcular estatísticas: {e}")
            return {"total": 0, "validos": 0, "falhados": 0, "tamanho_mb": 0}

    def relatorio_cache(self) -> str:
        """Gera relatório detalhado do cache"""
        stats = self.estatisticas_cache()
        
        relatorio = [
            "📊 RELATÓRIO DO CACHE",
            "=" * 50,
            f"📁 Total de arquivos: {stats['total']}",
            f"✅ Arquivos válidos: {stats['validos']}",
            f"❌ Arquivos com falha: {stats['falhados']}",
            f"💾 Tamanho total: {stats['tamanho_mb']} MB",
            f"🎯 Taxa de sucesso: {stats.get('taxa_sucesso', 0)}%",
            ""
        ]
        
        if stats['validos'] > 0:
            relatorio.append("✅ Recomendação: Use 'Processar cache' para analisar dados válidos")
        
        if stats['falhados'] > 0:
            relatorio.append("🧹 Recomendação: Use 'Limpar cache falhado' para remover arquivos inválidos")
        
        return '\n'.join(relatorio)
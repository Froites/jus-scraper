#!/usr/bin/env python3
"""
DJE Scraper - Sistema de Extração de Publicações do Diário da Justiça Eletrônico
Arquivo principal para execução do sistema
"""

import os
import sys
import json
from datetime import datetime
from typing import List

# Adicionar src ao path ANTES de qualquer import
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# Agora importar os módulos
try:
    from scraper.dje_scraper import DJEScraperOtimizado
    from scraper.cache_manager import CacheManager
    from api.api_client import JusAPIClient  # ← JusAPIClient correto
    from utils.logger import setup_logger
    from utils.config import Config
    from models.publicacao import Publicacao
    
    print("✅ Todos os módulos importados com sucesso")
    
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("💡 Verifique se todos os arquivos estão na estrutura correta:")
    print("   src/scraper/dje_scraper.py")
    print("   src/scraper/cache_manager.py") 
    print("   src/api/api_client.py")
    print("   src/utils/logger.py")
    print("   src/utils/config.py")
    print("   src/models/publicacao.py")
    print("\n💡 Se não tiver selenium instalado, use:")
    print("   pip install selenium==4.15.2 webdriver-manager==4.0.1 requests python-dotenv pyperclip")
    print("\n💡 Ou use sem selenium:")
    print("   python process_cache_only.py")
    sys.exit(1)

# Configurar logging
logger = setup_logger()

def criar_diretorios():
    """Cria diretórios necessários se não existirem"""
    diretorios = ['data/cache', 'data/results', 'data/backups', 'logs']
    
    for diretorio in diretorios:
        os.makedirs(diretorio, exist_ok=True)

def mostrar_banner():
    """Mostra banner do sistema"""
    print("🏛️" + "="*60)
    print("    DJE SCRAPER - TRIBUNAL DE JUSTIÇA DE SÃO PAULO")
    print("    Sistema de Extração de Publicações Judiciais")
    print("    Versão 2.0 - Estrutura Organizada")
    print("="*62)

def mostrar_estatisticas_cache():
    """Mostra estatísticas do cache atual"""
    cache_manager = CacheManager()
    stats = cache_manager.estatisticas_cache()
    
    print(f"\n📊 SITUAÇÃO ATUAL DO CACHE:")
    print(f"   📁 Total de arquivos: {stats['total']}")
    print(f"   ✅ Arquivos válidos: {stats['validos']}")
    print(f"   ❌ Arquivos com falha: {stats['falhados']}")
    print(f"   💾 Tamanho total: {stats['tamanho_mb']} MB")
    if stats['total'] > 0:
        print(f"   🎯 Taxa de sucesso: {stats.get('taxa_sucesso', 0):.1f}%")

def mostrar_menu():
    """Mostra menu principal"""
    print(f"\n🔧 OPÇÕES DISPONÍVEIS:")
    print("   1. 🌐 Extrair publicações do site")
    print("   2. 📂 Processar cache existente")
    print("   3. 🧹 Limpar cache antigo")
    print("   4. 🗑️ Limpar cache com falhas")
    print("   5. 📊 Relatório detalhado do cache")
    print("   6. 🔌 Testar conexão com API")
    print("   7. ⚙️ Configurar API")
    print("   0. 🚪 Sair")

def extrair_do_site():
    """Executa extração do site"""
    print("\n🌐 EXTRAÇÃO DO SITE DJE")
    print("="*50)
    
    # Solicitar data
    data_busca = input("📅 Data para busca (DD/MM/AAAA) [13/11/2024]: ").strip()
    if not data_busca:
        data_busca = "13/11/2024"
    
    logger.info(f"Iniciando extração para data: {data_busca}")
    
    try:
        scraper = DJEScraperOtimizado()
        publicacoes = scraper.executar(data_busca)
        
        if publicacoes:
            logger.info(f"Extração concluída: {len(publicacoes)} publicações encontradas")
            return processar_resultados(publicacoes, "extrair")
        else:
            print("\nℹ️ Nenhuma publicação relevante encontrada")
            logger.warning("Nenhuma publicação encontrada na extração")
            return []
            
    except Exception as e:
        logger.error(f"Erro na extração: {e}")
        print(f"❌ Erro durante a extração: {e}")
        return []

def processar_cache():
    """Processa arquivos de cache existentes"""
    print("\n📂 PROCESSAMENTO DO CACHE")
    print("="*50)
    
    cache_manager = CacheManager()
    arquivos_validos = cache_manager.listar_arquivos_validos()
    
    if not arquivos_validos:
        print("❌ Nenhum arquivo de cache válido encontrado!")
        print("💡 Execute a extração do site primeiro (opção 1)")
        return []
    
    logger.info(f"Processando {len(arquivos_validos)} arquivos de cache")
    
    try:
        scraper = DJEScraperOtimizado()
        publicacoes = scraper.processar_cache()
        
        if publicacoes:
            logger.info(f"Cache processado: {len(publicacoes)} publicações extraídas")
            return processar_resultados(publicacoes, "cache")
        else:
            print("\nℹ️ Nenhuma publicação relevante encontrada no cache")
            return []
            
    except Exception as e:
        logger.error(f"Erro no processamento do cache: {e}")
        print(f"❌ Erro durante o processamento: {e}")
        return []

def processar_resultados(publicacoes: List, origem: str):
    """Processa e salva resultados das publicações"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salvar JSON local
    nome_arquivo = f"data/results/publicacoes_{origem}_{timestamp}.json"
    dados = [pub.to_dict() for pub in publicacoes]
    
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    # Mostrar resumo
    mostrar_resumo_publicacoes(publicacoes)
    print(f"\n💾 Resultados salvos em: {nome_arquivo}")
    
    # Perguntar sobre envio para API
    if perguntar_envio_api():
        enviar_para_api(publicacoes, timestamp)
    
    return publicacoes

def mostrar_resumo_publicacoes(publicacoes: List):
    """Mostra resumo das publicações encontradas"""
    print(f"\n📊 RESUMO: {len(publicacoes)} publicações encontradas")
    print("="*50)
    
    total_principal = sum(pub.valor_principal or 0 for pub in publicacoes)
    total_juros = sum(pub.valor_juros or 0 for pub in publicacoes)
    total_honorarios = sum(pub.honorarios or 0 for pub in publicacoes)
    
    for i, pub in enumerate(publicacoes, 1):
        print(f"\n{i}. 📋 {pub.numero_processo or 'N/A'}")
        if pub.data_disponibilizacao:
            print(f"   📅 {pub.data_disponibilizacao}")
        if pub.autores:
            print(f"   👤 {pub.autores}")
        if pub.advogados:
            print(f"   ⚖️ {pub.advogados}")
        
        # Valores em uma linha
        valores = []
        if pub.valor_principal:
            valores.append(f"Principal: R$ {pub.valor_principal:,.2f}")
        if pub.valor_juros:
            valores.append(f"Juros: R$ {pub.valor_juros:,.2f}")
        if pub.honorarios:
            valores.append(f"Honorários: R$ {pub.honorarios:,.2f}")
        
        if valores:
            print(f"   💰 {' | '.join(valores)}")
    
    # Totais gerais
    if total_principal + total_juros + total_honorarios > 0:
        print(f"\n💰 TOTAIS GERAIS:")
        if total_principal > 0:
            print(f"   📊 Principal: R$ {total_principal:,.2f}")
        if total_juros > 0:
            print(f"   📈 Juros: R$ {total_juros:,.2f}")
        if total_honorarios > 0:
            print(f"   🏛️ Honorários: R$ {total_honorarios:,.2f}")
        print(f"   🎯 TOTAL GERAL: R$ {(total_principal + total_juros + total_honorarios):,.2f}")

def perguntar_envio_api() -> bool:
    """Pergunta se deve enviar para API"""
    resposta = input("\n🚀 Deseja enviar os dados para a API? (s/n): ").strip().lower()
    return resposta in ['s', 'sim', 'y', 'yes']

def enviar_para_api(publicacoes: List, timestamp: str):
    """Envia publicações para a API usando JusAPIClient"""
    try:
        api_client = JusAPIClient()  # ← Usando JusAPIClient
        
        # Criar backup antes do envio
        nome_backup = f"data/backups/backup_pre_api_{timestamp}.json"
        api_client.criar_backup_local(publicacoes, nome_backup)
        
        # Enviar para API no formato correto
        resultado = api_client.enviar_lote_publicacoes(publicacoes)  # ← Envia dados
        
        # Salvar relatório
        nome_relatorio = f"data/results/relatorio_api_{timestamp}.json"
        with open(nome_relatorio, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Envio para API concluído: {resultado['sucessos']} sucessos, {resultado['erros']} erros")
        print(f"📋 Relatório do envio salvo em: {nome_relatorio}")
        
    except Exception as e:
        logger.error(f"Erro no envio para API: {e}")
        print(f"❌ Erro no envio para API: {e}")
        import traceback
        traceback.print_exc().enviar_lote_publicacoes(publicacoes)
        
        # Salvar relatório
        nome_relatorio = f"data/results/relatorio_api_{timestamp}.json"
        with open(nome_relatorio, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Envio para API concluído: {resultado['sucessos']} sucessos, {resultado['erros']} erros")
        print(f"📋 Relatório do envio salvo em: {nome_relatorio}")
        
    except Exception as e:
        logger.error(f"Erro no envio para API: {e}")
        print(f"❌ Erro no envio para API: {e}")

def gerenciar_cache():
    """Menu de gerenciamento de cache"""
    cache_manager = CacheManager()
    
    while True:
        print(f"\n🗂️ GERENCIAMENTO DE CACHE")
        print("="*50)
        
        # Mostrar estatísticas
        stats = cache_manager.estatisticas_cache()
        print(f"📊 Status: {stats['validos']} válidos, {stats['falhados']} com falha")
        print(f"💾 Tamanho: {stats['tamanho_mb']} MB")
        
        print(f"\nOpções:")
        print("1. 📊 Relatório detalhado")
        print("2. 🧹 Limpar cache antigo")
        print("3. 🗑️ Limpar cache com falhas")
        print("0. ↩️ Voltar")
        
        opcao = input("\nEscolha: ").strip()
        
        if opcao == "1":
            print("\n" + cache_manager.relatorio_cache())
        elif opcao == "2":
            dias = input("Limpar arquivos com mais de quantos dias? [30]: ").strip()
            dias = int(dias) if dias.isdigit() else 30
            cache_manager.limpar_cache_antigo(dias)
        elif opcao == "3":
            cache_manager.limpar_cache_falhado()
        elif opcao == "0":
            break
        else:
            print("❌ Opção inválida")

def testar_api():
    """Testa conexão com a API"""
    try:
        api_client = JusAPIClient()  # ← Usando JusAPIClient
        if api_client.testar_conexao():
            print("✅ API funcionando corretamente!")
            # Teste adicional do endpoint de publicações
            if api_client.verificar_endpoint_publicacoes():
                print("✅ Endpoint de publicações acessível!")
        else:
            print("❌ Problema na conexão com a API")
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")

def configurar_api():
    """Configuração da API"""
    try:
        print("⚙️ CONFIGURAÇÃO DA API JUSCASH")
        print("=" * 50)
        
        api_client = JusAPIClient()
        
        print(f"URL atual: {api_client.base_url}")
        nova_url = input("Nova URL da API (Enter para manter): ").strip()
        
        if nova_url:
            # Criar novo cliente com nova URL
            api_client = JusAPIClient(nova_url)
            print(f"✅ URL configurada para: {nova_url}")
        
        # Testar nova configuração
        print("\n🔍 Testando configuração...")
        if api_client.testar_conexao():
            api_client.verificar_endpoint_publicacoes()
            
            # Mostrar estatísticas se disponível
            stats = api_client.obter_estatisticas()
            if "erro" not in stats:
                print(f"📊 Estatísticas da API: {len(stats)} campos disponíveis")
        
    except ImportError:
        print("❌ Módulo de configuração da API não encontrado")

def main():
    """Função principal"""
    # Preparar ambiente
    criar_diretorios()
    mostrar_banner()
    
    logger.info("Sistema DJE Scraper iniciado")
    
    try:
        while True:
            mostrar_estatisticas_cache()
            mostrar_menu()
            
            opcao = input("\n🎯 Escolha uma opção: ").strip()
            
            if opcao == "1":
                extrair_do_site()
            elif opcao == "2":
                processar_cache()
            elif opcao == "3":
                gerenciar_cache()
            elif opcao == "4":
                cache_manager = CacheManager()
                cache_manager.limpar_cache_falhado()
            elif opcao == "5":
                cache_manager = CacheManager()
                print("\n" + cache_manager.relatorio_cache())
            elif opcao == "6":
                testar_api()
            elif opcao == "7":
                configurar_api()
            elif opcao == "0":
                print("\n👋 Encerrando sistema...")
                logger.info("Sistema encerrado pelo usuário")
                break
            else:
                print("❌ Opção inválida! Tente novamente.")
            
            input("\n⏸️ Pressione Enter para continuar...")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Sistema interrompido pelo usuário")
        logger.info("Sistema interrompido via Ctrl+C")
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        print(f"\n❌ Erro crítico: {e}")
        import traceback
        print("\n🔍 Detalhes do erro:")
        traceback.print_exc()
    finally:
        print("🔚 Sistema finalizado")


if __name__ == "__main__":
    main()

def criar_diretorios():
    """Cria diretórios necessários se não existirem"""
    diretorios = ['data/cache', 'data/results', 'data/backups', 'logs']
    
    for diretorio in diretorios:
        os.makedirs(diretorio, exist_ok=True)

def mostrar_banner():
    """Mostra banner do sistema"""
    print("🏛️" + "="*60)
    print("    DJE SCRAPER - TRIBUNAL DE JUSTIÇA DE SÃO PAULO")
    print("    Sistema de Extração de Publicações Judiciais")
    print("    Versão 2.0 - Estrutura Organizada")
    print("="*62)

def mostrar_estatisticas_cache():
    """Mostra estatísticas do cache atual"""
    cache_manager = CacheManager()
    stats = cache_manager.estatisticas_cache()
    
    print(f"\n📊 SITUAÇÃO ATUAL DO CACHE:")
    print(f"   📁 Total de arquivos: {stats['total']}")
    print(f"   ✅ Arquivos válidos: {stats['validos']}")
    print(f"   ❌ Arquivos com falha: {stats['falhados']}")
    print(f"   💾 Tamanho total: {stats['tamanho_mb']} MB")
    if stats['total'] > 0:
        print(f"   🎯 Taxa de sucesso: {stats.get('taxa_sucesso', 0):.1f}%")

def mostrar_menu():
    """Mostra menu principal"""
    print(f"\n🔧 OPÇÕES DISPONÍVEIS:")
    print("   1. 🌐 Extrair publicações do site")
    print("   2. 📂 Processar cache existente")
    print("   3. 🧹 Limpar cache antigo")
    print("   4. 🗑️ Limpar cache com falhas")
    print("   5. 📊 Relatório detalhado do cache")
    print("   6. 🔌 Testar conexão com API")
    print("   7. ⚙️ Configurar API")
    print("   0. 🚪 Sair")

def extrair_do_site():
    """Executa extração do site"""
    print("\n🌐 EXTRAÇÃO DO SITE DJE")
    print("="*50)
    
    # Solicitar data
    data_busca = input("📅 Data para busca (DD/MM/AAAA) [13/11/2024]: ").strip()
    if not data_busca:
        data_busca = "13/11/2024"
    
    logger.info(f"Iniciando extração para data: {data_busca}")
    
    try:
        scraper = DJEScraperOtimizado()
        publicacoes = scraper.executar(data_busca)
        
        if publicacoes:
            logger.info(f"Extração concluída: {len(publicacoes)} publicações encontradas")
            return processar_resultados(publicacoes, "extrair")
        else:
            print("\nℹ️ Nenhuma publicação relevante encontrada")
            logger.warning("Nenhuma publicação encontrada na extração")
            return []
            
    except Exception as e:
        logger.error(f"Erro na extração: {e}")
        print(f"❌ Erro durante a extração: {e}")
        return []

def processar_cache():
    """Processa arquivos de cache existentes"""
    print("\n📂 PROCESSAMENTO DO CACHE")
    print("="*50)
    
    cache_manager = CacheManager()
    arquivos_validos = cache_manager.listar_arquivos_validos()
    
    if not arquivos_validos:
        print("❌ Nenhum arquivo de cache válido encontrado!")
        print("💡 Execute a extração do site primeiro (opção 1)")
        return []
    
    logger.info(f"Processando {len(arquivos_validos)} arquivos de cache")
    
    try:
        scraper = DJEScraperOtimizado()
        publicacoes = scraper.processar_cache()
        
        if publicacoes:
            logger.info(f"Cache processado: {len(publicacoes)} publicações extraídas")
            return processar_resultados(publicacoes, "cache")
        else:
            print("\nℹ️ Nenhuma publicação relevante encontrada no cache")
            return []
            
    except Exception as e:
        logger.error(f"Erro no processamento do cache: {e}")
        print(f"❌ Erro durante o processamento: {e}")
        return []

def processar_resultados(publicacoes: List, origem: str):
    """Processa e salva resultados das publicações"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salvar JSON local
    nome_arquivo = f"data/results/publicacoes_{origem}_{timestamp}.json"
    dados = [pub.to_dict() for pub in publicacoes]
    
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    # Mostrar resumo
    mostrar_resumo_publicacoes(publicacoes)
    print(f"\n💾 Resultados salvos em: {nome_arquivo}")
    
    # Perguntar sobre envio para API
    if perguntar_envio_api():
        enviar_para_api(publicacoes, timestamp)
    
    return publicacoes

def mostrar_resumo_publicacoes(publicacoes: List):
    """Mostra resumo das publicações encontradas"""
    print(f"\n📊 RESUMO: {len(publicacoes)} publicações encontradas")
    print("="*50)
    
    total_principal = sum(pub.valor_principal or 0 for pub in publicacoes)
    total_juros = sum(pub.valor_juros or 0 for pub in publicacoes)
    total_honorarios = sum(pub.honorarios or 0 for pub in publicacoes)
    
    for i, pub in enumerate(publicacoes, 1):
        print(f"\n{i}. 📋 {pub.numero_processo or 'N/A'}")
        if pub.data_disponibilizacao:
            print(f"   📅 {pub.data_disponibilizacao}")
        if pub.autores:
            print(f"   👤 {pub.autores}")
        if pub.advogados:
            print(f"   ⚖️ {pub.advogados}")
        
        # Valores em uma linha
        valores = []
        if pub.valor_principal:
            valores.append(f"Principal: R$ {pub.valor_principal:,.2f}")
        if pub.valor_juros:
            valores.append(f"Juros: R$ {pub.valor_juros:,.2f}")
        if pub.honorarios:
            valores.append(f"Honorários: R$ {pub.honorarios:,.2f}")
        
        if valores:
            print(f"   💰 {' | '.join(valores)}")
    
    # Totais gerais
    if total_principal + total_juros + total_honorarios > 0:
        print(f"\n💰 TOTAIS GERAIS:")
        if total_principal > 0:
            print(f"   📊 Principal: R$ {total_principal:,.2f}")
        if total_juros > 0:
            print(f"   📈 Juros: R$ {total_juros:,.2f}")
        if total_honorarios > 0:
            print(f"   🏛️ Honorários: R$ {total_honorarios:,.2f}")
        print(f"   🎯 TOTAL GERAL: R$ {(total_principal + total_juros + total_honorarios):,.2f}")

def perguntar_envio_api() -> bool:
    """Pergunta se deve enviar para API"""
    resposta = input("\n🚀 Deseja enviar os dados para a API? (s/n): ").strip().lower()
    return resposta in ['s', 'sim', 'y', 'yes']

def enviar_para_api(publicacoes: List, timestamp: str):
    """Envia publicações para a API"""
    try:
        api_client = APIClient()
        
        # Criar backup antes do envio
        nome_backup = f"data/backups/backup_pre_api_{timestamp}.json"
        api_client.criar_backup_local(publicacoes, nome_backup)
        
        # Enviar para API
        resultado = api_client.enviar_lote_publicacoes(publicacoes)
        
        # Salvar relatório
        nome_relatorio = f"data/results/relatorio_api_{timestamp}.json"
        with open(nome_relatorio, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Envio para API concluído: {resultado['sucessos']} sucessos, {resultado['erros']} erros")
        print(f"📋 Relatório do envio salvo em: {nome_relatorio}")
        
    except Exception as e:
        logger.error(f"Erro no envio para API: {e}")
        print(f"❌ Erro no envio para API: {e}")

def gerenciar_cache():
    """Menu de gerenciamento de cache"""
    cache_manager = CacheManager()
    
    while True:
        print(f"\n🗂️ GERENCIAMENTO DE CACHE")
        print("="*50)
        
        # Mostrar estatísticas
        stats = cache_manager.estatisticas_cache()
        print(f"📊 Status: {stats['validos']} válidos, {stats['falhados']} com falha")
        print(f"💾 Tamanho: {stats['tamanho_mb']} MB")
        
        print(f"\nOpções:")
        print("1. 📊 Relatório detalhado")
        print("2. 🧹 Limpar cache antigo")
        print("3. 🗑️ Limpar cache com falhas")
        print("0. ↩️ Voltar")
        
        opcao = input("\nEscolha: ").strip()
        
        if opcao == "1":
            print("\n" + cache_manager.relatorio_cache())
        elif opcao == "2":
            dias = input("Limpar arquivos com mais de quantos dias? [30]: ").strip()
            dias = int(dias) if dias.isdigit() else 30
            cache_manager.limpar_cache_antigo(dias)
        elif opcao == "3":
            cache_manager.limpar_cache_falhado()
        elif opcao == "0":
            break
        else:
            print("❌ Opção inválida")

def testar_api():
    """Testa conexão com a API"""
    try:
        api_client = APIClient()
        if api_client.testar_conexao():
            print("✅ API funcionando corretamente!")
        else:
            print("❌ Problema na conexão com a API")
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")

def configurar_api():
    """Configuração da API"""
    from api.config import configurar_api_interativo
    configurar_api_interativo()

def main():
    """Função principal"""
    # Preparar ambiente
    criar_diretorios()
    mostrar_banner()
    
    logger.info("Sistema DJE Scraper iniciado")
    
    try:
        while True:
            mostrar_estatisticas_cache()
            mostrar_menu()
            
            opcao = input("\n🎯 Escolha uma opção: ").strip()
            
            if opcao == "1":
                extrair_do_site()
            elif opcao == "2":
                processar_cache()
            elif opcao == "3":
                gerenciar_cache()
            elif opcao == "4":
                cache_manager = CacheManager()
                cache_manager.limpar_cache_falhado()
            elif opcao == "5":
                cache_manager = CacheManager()
                print("\n" + cache_manager.relatorio_cache())
            elif opcao == "6":
                testar_api()
            elif opcao == "7":
                configurar_api()
            elif opcao == "0":
                print("\n👋 Encerrando sistema...")
                logger.info("Sistema encerrado pelo usuário")
                break
            else:
                print("❌ Opção inválida! Tente novamente.")
            
            input("\n⏸️ Pressione Enter para continuar...")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Sistema interrompido pelo usuário")
        logger.info("Sistema interrompido via Ctrl+C")
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        print(f"\n❌ Erro crítico: {e}")
    finally:
        print("🔚 Sistema finalizado")


if __name__ == "__main__":
    main()
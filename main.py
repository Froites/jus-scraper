import os
import sys
import json
from datetime import datetime
from typing import List

# Adicionar src ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

# Importar módulos
try:
    from scraper.dje_scraper import DJEScraperDownload
    from scraper.cache_manager import CacheManager
    from api.api_client import JusAPIClient
    from utils.logger import setup_logger
    from utils.config import Config
    from models.publicacao import Publicacao
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    sys.exit(1)

logger = setup_logger()

def criar_diretorios():
    """Cria diretórios necessários se não existirem."""
    diretorios = ['data/cache', 'data/results', 'data/backups', 'logs']
    for diretorio in diretorios:
        os.makedirs(diretorio, exist_ok=True)

def mostrar_banner():
    """Exibe o banner do sistema."""
    print("="*62)
    print("DJE SCRAPER - TRIBUNAL DE JUSTIÇA DE SÃO PAULO")
    print("Sistema de Extração de Publicações Judiciais")
    print("Versão 2.0 - Estrutura Organizada")
    print("="*62)

def mostrar_estatisticas_cache():
    """Exibe estatísticas do cache atual."""
    cache_manager = CacheManager()
    stats = cache_manager.estatisticas_cache()
    
    print(f"\nSITUAÇÃO ATUAL DO CACHE:")
    print(f"  Total de arquivos: {stats['total']}")
    print(f"  Arquivos válidos: {stats['validos']}")
    print(f"  Arquivos com falha: {stats['falhados']}")
    print(f"  Tamanho total: {stats['tamanho_mb']} MB")
    if stats['total'] > 0:
        print(f"  Taxa de sucesso: {stats.get('taxa_sucesso', 0):.1f}%")

def mostrar_menu():
    """Exibe o menu principal de opções."""
    print(f"\nOPÇÕES DISPONÍVEIS:")
    print("  1. Extrair publicações do site")
    print("  2. Processar cache existente")
    print("  3. Gerenciar cache (limpar antigo/falhas, relatório)")
    print("  4. Testar conexão com API")
    print("  5. Configurar API")
    print("  0. Sair")

def extrair_do_site():
    """Executa a extração de publicações do site DJE."""
    print("\n--- EXTRAÇÃO DO SITE DJE ---")
    data_busca = input("Data para busca (DD/MM/AAAA) [13/11/2024]: ").strip()
    if not data_busca:
        data_busca = "13/11/2024"
    
    logger.info(f"Iniciando extração para data: {data_busca}")
    
    try:
        scraper = DJEScraperDownload() # Usando DJEScraperDownload
        publicacoes = scraper.executar(data_busca)
        
        if publicacoes:
            logger.info(f"Extração concluída: {len(publicacoes)} publicações encontradas")
            return processar_resultados(publicacoes, "extrair")
        else:
            print("Nenhuma publicação relevante encontrada.")
            logger.warning("Nenhuma publicação encontrada na extração")
            return []
            
    except Exception as e:
        logger.error(f"Erro na extração: {e}")
        print(f"Erro durante a extração: {e}")
        return []

def processar_cache():
    """Processa arquivos de cache existentes."""
    print("\n--- PROCESSAMENTO DO CACHE ---")
    cache_manager = CacheManager()
    arquivos_validos = cache_manager.listar_arquivos_validos()
    
    if not arquivos_validos:
        print("Nenhum arquivo de cache válido encontrado! Execute a extração do site primeiro (opção 1).")
        return []
    
    logger.info(f"Processando {len(arquivos_validos)} arquivos de cache")
    
    try:
        scraper = DJEScraperDownload() # Usando DJEScraperDownload
        publicacoes = scraper.processar_pdfs_baixados() #
        
        if publicacoes:
            logger.info(f"Cache processado: {len(publicacoes)} publicações extraídas")
            return processar_resultados(publicacoes, "cache")
        else:
            print("Nenhuma publicação relevante encontrada no cache.")
            return []
            
    except Exception as e:
        logger.error(f"Erro no processamento do cache: {e}")
        print(f"Erro durante o processamento: {e}")
        return []

def processar_resultados(publicacoes: List, origem: str):
    """Processa e salva os resultados das publicações, perguntando sobre o envio para a API."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"data/results/publicacoes_{origem}_{timestamp}.json"
    dados = [pub.to_dict() for pub in publicacoes]
    
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    
    mostrar_resumo_publicacoes(publicacoes)
    print(f"\nResultados salvos em: {nome_arquivo}")
    
    if perguntar_envio_api():
        enviar_para_api(publicacoes, timestamp)
    
    return publicacoes

def mostrar_resumo_publicacoes(publicacoes: List):
    """Exibe um resumo detalhado das publicações encontradas."""
    print(f"\n--- RESUMO: {len(publicacoes)} publicações encontradas ---")
    
    total_principal = sum(pub.valor_principal or 0 for pub in publicacoes)
    total_juros = sum(pub.valor_juros or 0 for pub in publicacoes)
    total_honorarios = sum(pub.honorarios or 0 for pub in publicacoes)
    
    for i, pub in enumerate(publicacoes, 1):
        print(f"\n{i}. Processo: {pub.numero_processo or 'N/A'}")
        if pub.data_disponibilizacao: print(f"   Data: {pub.data_disponibilizacao}")
        if pub.autores: print(f"   Autor: {pub.autores}")
        if pub.advogados: print(f"   Advogados: {pub.advogados}")
        
        valores = []
        if pub.valor_principal: valores.append(f"Principal: R$ {pub.valor_principal:,.2f}")
        if pub.valor_juros: valores.append(f"Juros: R$ {pub.valor_juros:,.2f}")
        if pub.honorarios: valores.append(f"Honorários: R$ {pub.honorarios:,.2f}")
        if valores: print(f"   Valores: {' | '.join(valores)}")
    
    if total_principal + total_juros + total_honorarios > 0:
        print(f"\n--- TOTAIS GERAIS ---")
        if total_principal > 0: print(f"  Principal: R$ {total_principal:,.2f}")
        if total_juros > 0: print(f"  Juros: R$ {total_juros:,.2f}")
        if total_honorarios > 0: print(f"  Honorários: R$ {total_honorarios:,.2f}")
        print(f"  TOTAL GERAL: R$ {(total_principal + total_juros + total_honorarios):,.2f}")

def perguntar_envio_api() -> bool:
    """Pergunta ao usuário se deseja enviar os dados para a API."""
    resposta = input("\nDeseja enviar os dados para a API? (s/n): ").strip().lower()
    return resposta in ['s', 'sim', 'y', 'yes']

def enviar_para_api(publicacoes: List, timestamp: str):
    """Envia publicações para a API usando JusAPIClient."""
    try:
        api_client = JusAPIClient()
        
        nome_backup = f"data/backups/backup_pre_api_{timestamp}.json"
        api_client.criar_backup_local(publicacoes, nome_backup)
        
        resultado = api_client.enviar_lote_publicacoes(publicacoes)
        
        nome_relatorio = f"data/results/relatorio_api_{timestamp}.json"
        with open(nome_relatorio, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Envio para API concluído: {resultado['sucessos']} sucessos, {resultado['erros']} erros")
        print(f"Relatório do envio salvo em: {nome_relatorio}")
        
    except Exception as e:
        logger.error(f"Erro no envio para API: {e}")
        print(f"Erro no envio para API: {e}")

def gerenciar_cache():
    """Menu para gerenciar operações de cache."""
    cache_manager = CacheManager()
    
    while True:
        print(f"\n--- GERENCIAMENTO DE CACHE ---")
        stats = cache_manager.estatisticas_cache()
        print(f"Status: {stats['validos']} válidos, {stats['falhados']} com falha")
        print(f"Tamanho: {stats['tamanho_mb']} MB")
        
        print(f"\nOpções:")
        print("1. Relatório detalhado")
        print("2. Limpar cache antigo")
        print("3. Limpar cache com falhas")
        print("0. Voltar")
        
        opcao = input("\nEscolha: ").strip()
        
        if opcao == "1":
            print(cache_manager.relatorio_cache())
        elif opcao == "2":
            dias = input("Limpar arquivos com mais de quantos dias? [30]: ").strip()
            dias = int(dias) if dias.isdigit() else 30
            cache_manager.limpar_cache_antigo(dias)
        elif opcao == "3":
            cache_manager.limpar_cache_falhado()
        elif opcao == "0":
            break
        else:
            print("Opção inválida")

def testar_api():
    """Testa a conexão com a API."""
    try:
        api_client = JusAPIClient()
        if api_client.testar_conexao():
            print("API funcionando corretamente!")
        else:
            print("Problema na conexão com a API.")
    except Exception as e:
        print(f"Erro ao testar API: {e}")

def configurar_api():
    """Configurações interativas da API."""
    print("--- CONFIGURAÇÃO DA API JUSCASH ---")
    try:
        api_client = JusAPIClient()
        
        print(f"URL atual: {api_client.base_url}")
        nova_url = input("Nova URL da API (Enter para manter): ").strip()
        
        if nova_url:
            # Isso modifica a BASE_URL da classe APIConfig
            from api.config import APIConfig
            APIConfig.configurar_url_personalizada(nova_url)
            api_client = JusAPIClient() # Recria o cliente com a nova URL
            print(f"URL configurada para: {APIConfig.BASE_URL}")

        # Configurar autenticação, se houver
        if APIConfig.API_KEY is None:
            config_auth = input("Deseja configurar API Key/Secret? (s/n): ").strip().lower()
            if config_auth == 's':
                api_key = input("API Key: ").strip()
                api_secret = input("API Secret (opcional): ").strip() or None
                APIConfig.configurar_autenticacao(api_key, api_secret)
                api_client = JusAPIClient() # Recria o cliente com a nova autenticação
                print("Configuração de autenticação aplicada.")

        print("\nTestando nova configuração...")
        if api_client.testar_conexao():
            print("Conexão bem-sucedida com a nova configuração.")
        else:
            print("Problema na conexão com a nova configuração.")

    except ImportError:
        print("Módulo de configuração da API não encontrado.")
    except Exception as e:
        print(f"Erro ao configurar API: {e}")

def main():
    """Função principal"""
    criar_diretorios()
    mostrar_banner()
    logger.info("Sistema DJE Scraper iniciado")
    
    try:
        while True:
            mostrar_estatisticas_cache()
            mostrar_menu()
            
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == "1":
                extrair_do_site()
            elif opcao == "2":
                processar_cache()
            elif opcao == "3":
                gerenciar_cache()
            elif opcao == "4":
                testar_api()
            elif opcao == "5":
                configurar_api()
            elif opcao == "0":
                print("Encerrando sistema...")
                logger.info("Sistema encerrado pelo usuário")
                break
            else:
                print("Opção inválida! Tente novamente.")
            
            input("\nPressione Enter para continuar...")
    
    except KeyboardInterrupt:
        print("\nSistema interrompido pelo usuário.")
        logger.info("Sistema interrompido via Ctrl+C")
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        print(f"\nErro crítico: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Sistema finalizado.")


if __name__ == "__main__":
    main()
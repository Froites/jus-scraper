#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime
from typing import Union

current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

try:
    from scraper.dje_scraper import DJEScraperOtimizado
    from scraper.cache_manager import CacheManager
    from api.api_client import JusAPIClient
    from utils.logger import setup_logger
    from utils.config import Config
    from models.publicacao import Publicacao
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

logger = setup_logger()

def criar_diretorios():
    for diretorio in ['data/cache', 'data/results', 'data/backups', 'logs']:
        os.makedirs(diretorio, exist_ok=True)

def mostrar_banner():
    print("    Sistema de Extração de Publicações Judiciais")
    print("="*62)

def get_last_processed_date() -> Union[datetime.date, None]:
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'results')
    if not os.path.exists(results_dir):
        return None

    json_files = [f for f in os.listdir(results_dir) if f.startswith('publicacoes_') and f.endswith('.json')]
    json_files.sort(reverse=True)

    for filename in json_files:
        filepath = os.path.join(results_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data and isinstance(data, list) and len(data) > 0:
                    # Tenta pegar a data da primeira publicação no arquivo
                    created_at_str = data[0].get('created_at')
                    if created_at_str:
                        return datetime.fromisoformat(created_at_str).date()
        except Exception as e:
            logger.warning(f"Erro ao ler arquivo de resultado {filename}: {e}")
    return None

def processar_e_enviar():
    data_busca = datetime.now().strftime("%d/%m/%Y")
    logger.info(f"Iniciando extração para data: {data_busca}")

    publicacoes = []
    try:
        scraper = DJEScraperOtimizado()
        publicacoes = scraper.executar(data_busca)

        if not publicacoes:
            logger.info("Nenhuma publicação relevante encontrada na extração do site. Tentando processar cache.")
            publicacoes = scraper.processar_cache()

        if publicacoes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo_local = f"data/results/publicacoes_extraidas_{timestamp}.json"
            
            with open(nome_arquivo_local, 'w', encoding='utf-8') as f:
                json.dump([pub.to_dict() for pub in publicacoes], f, ensure_ascii=False, indent=2)
            
            logger.info(f"Resultados salvos localmente em: {nome_arquivo_local}")
            
            api_client = JusAPIClient()
            nome_backup = f"data/backups/backup_pre_api_{timestamp}.json"
            api_client.criar_backup_local(publicacoes, nome_backup)
            
            if api_client.testar_conexao():
                resultado_envio = api_client.enviar_lote_publicacoes(publicacoes)
                
                nome_relatorio = f"data/results/relatorio_api_{timestamp}.json"
                with open(nome_relatorio, 'w', encoding='utf-8') as f:
                    json.dump(resultado_envio, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Envio para API concluído: {resultado_envio['sucessos']} sucessos, {resultado_envio['erros']} erros. Relatório salvo em: {nome_relatorio}")
            else:
                logger.error("Não foi possível conectar à API. Publicações não foram enviadas.")
        else:
            logger.info("Nenhuma publicação relevante encontrada para processar ou enviar.")

    except Exception as e:
        logger.error(f"Erro durante a execução principal: {e}", exc_info=True)

def main():
    criar_diretorios()
    mostrar_banner()
    logger.info("Sistema DJE Scraper iniciado em modo automático.")

    last_processed_date = get_last_processed_date()
    current_date = datetime.now().date()

    if last_processed_date == current_date:
        print("\nℹ️ Os dados já foram atualizados para o dia de hoje. Nenhuma nova busca será feita.")
        logger.info("Dados já atualizados para o dia atual. Encerrando.")
    else:
        print(f"\n🚀 Última publicação processada em: {last_processed_date}. Iniciando nova busca/processamento para {current_date}.")
        processar_e_enviar()

    print("\n👋 Encerrando sistema.")
    logger.info("Sistema encerrado.")
    sys.exit(0)

if __name__ == "__main__":
    main()
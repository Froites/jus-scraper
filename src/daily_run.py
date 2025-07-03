import os
import sys
import json
from datetime import datetime

# Adicionar src ao sys.path se não estiver (para ambiente Docker)
script_dir = os.path.dirname(os.path.abspath(__file__))
# O diretório 'src' deve ser o primeiro no PATH
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
# A raiz do projeto (onde 'models' etc. estão) também deve estar no PATH
project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scraper.dje_scraper import DJEScraperDownload
from api.api_client import JusAPIClient
from utils.logger import setup_logger
from models.publicacao import Publicacao


logger = setup_logger(log_file="daily_run.log")

def run_daily_scrape_and_send():
    """
    Executa o processo diário de scraping, extração e envio à API.
    """
    logger.info("Daily scrape and API submission initiated.")

    today_date = datetime.now().strftime("%d/%m/%Y")
    logger.info(f"Targeting date for search: {today_date}")

    # O VOLUME /app no Dockerfile mapeará a pasta do projeto.
    pasta_download = "/app/downloads_dje" 
    
    try:
        scraper = DJEScraperDownload(pasta_download=pasta_download)

        logger.info(f"Starting web scraping for {today_date}...")
        publicacoes = scraper.executar(today_date)

        if publicacoes:
            logger.info(f"Scraping completed. Found {len(publicacoes)} relevant publications.")

            api_client = JusAPIClient()

            if not api_client.testar_conexao():
                logger.error("API connection failed. Publications will not be sent.")
                # Opcional: criar backup local mesmo que a API falhe
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"/app/data/backups/daily_run_failed_api_{timestamp}.json"
                api_client.criar_backup_local(publicacoes, backup_file)
                logger.info(f"Local backup created: {backup_file}")
                return

            logger.info(f"API connection successful. Sending {len(publicacoes)} publications...")

            result = api_client.enviar_lote_publicacoes(publicacoes)

            logger.info(f"API submission results: Successes={result['sucessos']}, Errors={result['erros']}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"/app/data/results/daily_run_results_{timestamp}.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump([pub.to_dict() for pub in publicacoes], f, ensure_ascii=False, indent=2)
            logger.info(f"Local results saved to: {results_file}")

        else:
            logger.info(f"No relevant publications found for {today_date}.")

    except Exception as e:
        logger.exception("An unhandled error occurred during the daily run.")

    logger.info("Daily scrape and API submission finished.")

if __name__ == "__main__":
    run_daily_scrape_and_send()
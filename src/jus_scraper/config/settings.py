import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent.parent

# URLs do DJE
DJE_BASE_URL = os.getenv('DJE_BASE_URL', 'https://dje.tjsp.jus.br/cdje/index.do')
SEARCH_KEYWORDS = os.getenv('SEARCH_KEYWORDS', 'RPV,pagamento pelo INSS').split(',')

# Selenium
SELENIUM_HEADLESS = os.getenv('SELENIUM_HEADLESS', 'true').lower() == 'true'
SELENIUM_TIMEOUT = int(os.getenv('SELENIUM_TIMEOUT', 30))

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

print(f"Base URL: {DJE_BASE_URL}")

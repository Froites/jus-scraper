import os
from typing import Dict, List

class Config:
    DJE_BASE_URL = 'https://dje.tjsp.jus.br/cdje/index.do'
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3000')
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    CACHE_DIR = os.path.join(DATA_DIR, 'cache')
    RESULTS_DIR = os.path.join(DATA_DIR, 'results')
    BACKUPS_DIR = os.path.join(DATA_DIR, 'backups')
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    
    PAGE_LOAD_TIMEOUT = int(os.getenv('PAGE_LOAD_TIMEOUT', '30'))
    PDF_LOAD_TIMEOUT = int(os.getenv('PDF_LOAD_TIMEOUT', '8'))
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))
    CLICK_PAUSE = float(os.getenv('CLICK_PAUSE', '1.0'))
    EXTRACTION_PAUSE = float(os.getenv('EXTRACTION_PAUSE', '2.0'))
    
    CHROME_OPTIONS = [
        "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
        "--disable-extensions", "--disable-plugins", "--disable-images",
        "--window-size=1920,1080", "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
        "--disable-blink-features=AutomationControlled",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ]
    
    SEARCH_CONFIG = {
        'caderno': 'caderno 3 - Judicial - 1ª Instância - Capital - Parte I',
        'palavras_chave': '"RPV" e "pagamento pelo INSS"',
        'data_padrao': '13/11/2024'
    }
    
    CONTEUDO_MIN_CHARS = int(os.getenv('CONTEUDO_MIN_CHARS', '6000'))
    INDICADORES_MIN = int(os.getenv('INDICADORES_MIN', '3'))
    
    INDICADORES_SUCESSO = [
        "Publicação Oficial do Tribunal", "Diário da Justiça Eletrônico", "Processo ",
        "ADV:", "Vistos", "R$", "Cumprimento de Sentença", "Fazenda Pública",
        "homologo", "Homologação"
    ]
    
    INDICADORES_OBRIGATORIOS = [
        "Publicação Oficial do Tribunal", "Diário da Justiça Eletrônico", "Processo "
    ]
    
    FRAME_CLICK_COORDS = (100, 100)
    
    CACHE_RETENTION_DAYS = int(os.getenv('CACHE_RETENTION_DAYS', '30'))
    CACHE_MAX_SIZE_MB = int(os.getenv('CACHE_MAX_SIZE_MB', '500'))
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'true').lower() == 'true'
    LOG_MAX_FILES = int(os.getenv('LOG_MAX_FILES', '10'))
    
    MAX_CONCURRENT_EXTRACTIONS = int(os.getenv('MAX_CONCURRENT_EXTRACTIONS', '1'))
    EXTRACTION_RETRY_ATTEMPTS = int(os.getenv('EXTRACTION_RETRY_ATTEMPTS', '3'))
    
    @classmethod
    def get_cache_path(cls) -> str:
        return cls.CACHE_DIR
    
    @classmethod
    def get_results_path(cls) -> str:
        return cls.RESULTS_DIR
    
    @classmethod
    def get_backups_path(cls) -> str:
        return cls.BACKUPS_DIR
    
    @classmethod
    def get_logs_path(cls) -> str:
        return cls.LOGS_DIR
    
    @classmethod
    def create_directories(cls):
        directories = [cls.CACHE_DIR, cls.RESULTS_DIR, cls.BACKUPS_DIR, cls.LOGS_DIR]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> Dict:
        erros = []
        avisos = []
        if not cls.DJE_BASE_URL:
            erros.append("URL do DJE não configurada")
        if cls.PAGE_LOAD_TIMEOUT <= 0:
            erros.append("PAGE_LOAD_TIMEOUT deve ser maior que 0")
        if cls.CONTEUDO_MIN_CHARS < 1000:
            avisos.append("CONTEUDO_MIN_CHARS muito baixo (< 1000)")
        try:
            cls.create_directories()
        except Exception as e:
            erros.append(f"Não foi possível criar diretórios: {e}")
        return {"valida": len(erros) == 0, "erros": erros, "avisos": avisos}
    
    @classmethod
    def to_dict(cls) -> Dict:
        return {
            'dje_base_url': cls.DJE_BASE_URL, 'api_base_url': cls.API_BASE_URL,
            'cache_dir': cls.CACHE_DIR, 'results_dir': cls.RESULTS_DIR,
            'backups_dir': cls.BACKUPS_DIR, 'logs_dir': cls.LOGS_DIR,
            'page_load_timeout': cls.PAGE_LOAD_TIMEOUT, 'pdf_load_timeout': cls.PDF_LOAD_TIMEOUT,
            'api_timeout': cls.API_TIMEOUT, 'conteudo_min_chars': cls.CONTEUDO_MIN_CHARS,
            'indicadores_min': cls.INDICADORES_MIN, 'cache_retention_days': cls.CACHE_RETENTION_DAYS,
            'log_level': cls.LOG_LEVEL, 'extraction_retry_attempts': cls.EXTRACTION_RETRY_ATTEMPTS
        }
    
    @classmethod
    def from_env_file(cls, env_file: str = '.env'):
        if os.path.exists(env_file):
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                pass
    
    @classmethod
    def print_config(cls):
        print("⚙️ CONFIGURAÇÃO DO SISTEMA DJE SCRAPER")
        print("=" * 60)
        print(f"\n🌐 URLS:")
        print(f"   DJE Base URL:      {cls.DJE_BASE_URL}")
        print(f"   API Base URL:      {cls.API_BASE_URL}")
        print(f"\n📁 DIRETÓRIOS:")
        print(f"   Cache:             {cls.CACHE_DIR}")
        print(f"   Resultados:        {cls.RESULTS_DIR}")
        print(f"   Backups:           {cls.BACKUPS_DIR}")
        print(f"   Logs:              {cls.LOGS_DIR}")
        print(f"\n⏱️ TIMEOUTS (segundos):")
        print(f"   Carregamento:      {cls.PAGE_LOAD_TIMEOUT}")
        print(f"   PDF:               {cls.PDF_LOAD_TIMEOUT}")
        print(f"   API:               {cls.API_TIMEOUT}")
        print(f"   Clique:            {cls.CLICK_PAUSE}")
        print(f"   Extração:          {cls.EXTRACTION_PAUSE}")
        print(f"\n🔍 VALIDAÇÃO:")
        print(f"   Min chars:         {cls.CONTEUDO_MIN_CHARS}")
        print(f"   Min indicadores:   {cls.INDICADORES_MIN}")
        print(f"   Tentativas:        {cls.EXTRACTION_RETRY_ATTEMPTS}")
        print(f"\n💾 CACHE:")
        print(f"   Retenção (dias):   {cls.CACHE_RETENTION_DAYS}")
        print(f"   Max size (MB):     {cls.CACHE_MAX_SIZE_MB}")
        print(f"\n📝 LOGGING:")
        print(f"   Nível:             {cls.LOG_LEVEL}")
        print(f"   Para arquivo:      {cls.LOG_TO_FILE}")
        print(f"   Max arquivos:      {cls.LOG_MAX_FILES}")
        validacao = cls.validate_config()
        if validacao["valida"]:
            print(f"\n✅ Configuração válida")
        else:
            print(f"\n❌ Problemas na configuração:")
            for erro in validacao["erros"]:
                print(f"   • {erro}")
        if validacao["avisos"]:
            print(f"\n⚠️ Avisos:")
            for aviso in validacao["avisos"]:
                print(f"   • {aviso}")

class DevelopmentConfig(Config):
    LOG_LEVEL = 'DEBUG'
    CONTEUDO_MIN_CHARS = 1000
    EXTRACTION_RETRY_ATTEMPTS = 2
    CHROME_OPTIONS = Config.CHROME_OPTIONS + ["--enable-logging", "--v=1"]

class ProductionConfig(Config):
    LOG_LEVEL = 'INFO'
    CONTEUDO_MIN_CHARS = 6000
    EXTRACTION_RETRY_ATTEMPTS = 3
    CHROME_OPTIONS = Config.CHROME_OPTIONS + ["--headless", "--disable-logging"]

class TestConfig(Config):
    LOG_LEVEL = 'DEBUG'
    CACHE_DIR = 'test_data/cache'
    RESULTS_DIR = 'test_data/results'
    BACKUPS_DIR = 'test_data/backups'
    LOGS_DIR = 'test_data/logs'
    CONTEUDO_MIN_CHARS = 500
    PAGE_LOAD_TIMEOUT = 10

def get_config() -> Config:
    env = os.getenv('ENVIRONMENT', 'development').lower()
    if env == 'production':
        return ProductionConfig()
    elif env == 'test':
        return TestConfig()
    else:
        return DevelopmentConfig()

config = get_config()
config.from_env_file()
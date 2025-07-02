import os
from typing import Dict, Optional

class APIConfig:
    BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3000').rstrip('/')
    TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))
    
    ENDPOINTS = {
        'health': '/health',
        'publicacoes': '/api/publicacoes',
        'processos': '/api/publicacoes/processos',
        'duplicados': '/api/publicacoes/duplicados',
        'stats': '/api/publicacoes/stats',
        'search': '/api/publicacoes/search'
    }
    
    HEADERS = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'DJE-Scraper/2.0',
        'X-Client': 'dje-scraper-python'
    }
    
    MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', '3'))
    RETRY_DELAY = float(os.getenv('API_RETRY_DELAY', '1.0'))
    RETRY_BACKOFF_FACTOR = float(os.getenv('API_RETRY_BACKOFF_FACTOR', '2.0'))
    
    REQUESTS_PER_MINUTE = int(os.getenv('API_REQUESTS_PER_MINUTE', '60'))
    BURST_LIMIT = int(os.getenv('API_BURST_LIMIT', '10'))
    
    BATCH_SIZE = int(os.getenv('API_BATCH_SIZE', '20'))
    BATCH_DELAY = float(os.getenv('API_BATCH_DELAY', '0.1'))
    
    API_KEY = os.getenv('API_KEY', None)
    API_SECRET = os.getenv('API_SECRET', None)
    
    @classmethod
    def get_full_url(cls, endpoint_key: str) -> str:
        endpoint = cls.ENDPOINTS.get(endpoint_key, '')
        return f"{cls.BASE_URL}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
    
    @classmethod
    def get_headers(cls, include_auth: bool = False) -> Dict[str, str]:
        headers = cls.HEADERS.copy()
        
        if include_auth and cls.API_KEY:
            headers['Authorization'] = f"Bearer {cls.API_KEY}"
            
        if cls.API_SECRET:
            headers['X-API-Secret'] = cls.API_SECRET
        
        return headers
    
    @classmethod
    def configurar_url_personalizada(cls, nova_url: str):
        cls.BASE_URL = nova_url.rstrip('/')
    
    @classmethod
    def configurar_autenticacao(cls, api_key: str, api_secret: Optional[str] = None):
        cls.API_KEY = api_key
        if api_secret:
            cls.API_SECRET = api_secret
    
    @classmethod
    def validar_configuracao(cls) -> Dict:
        erros = []
        avisos = []
        
        if not cls.BASE_URL:
            erros.append("URL da API não configurada")
        elif not cls.BASE_URL.startswith(('http://', 'https://')):
            erros.append("URL da API deve começar com http:// ou https://")
        
        if cls.TIMEOUT <= 0:
            erros.append("Timeout deve ser maior que 0")
        
        if cls.MAX_RETRIES < 0:
            erros.append("Max retries não pode ser negativo")
        
        if cls.BATCH_SIZE <= 0:
            erros.append("Batch size deve ser maior que 0")
        
        if cls.TIMEOUT < 5:
            avisos.append("Timeout muito baixo (< 5s) pode causar falhas")
        
        if cls.REQUESTS_PER_MINUTE > 100:
            avisos.append("Rate limit alto pode sobrecarregar a API")
        
        if not cls.API_KEY:
            avisos.append("API Key não configurada - pode ser necessária")
        
        return {
            "valida": len(erros) == 0,
            "erros": erros,
            "avisos": avisos
        }
    
    @classmethod
    def to_dict(cls) -> Dict:
        return {
            'base_url': cls.BASE_URL,
            'timeout': cls.TIMEOUT,
            'max_retries': cls.MAX_RETRIES,
            'retry_delay': cls.RETRY_DELAY,
            'requests_per_minute': cls.REQUESTS_PER_MINUTE,
            'batch_size': cls.BATCH_SIZE,
            'batch_delay': cls.BATCH_DELAY,
            'has_api_key': bool(cls.API_KEY),
            'has_api_secret': bool(cls.API_SECRET)
        }

API_SCHEMA = {
    "publicacao": {
        "numero_processo": {
            "tipo": "string",
            "obrigatorio": True,
            "max_length": 50,
            "descricao": "Número único do processo judicial",
            "exemplo": "0013168-70.2024.8.26.0053"
        },
        "data_disponibilizacao": {
            "tipo": "string",
            "obrigatorio": False,
            "formato": "DD de mês de AAAA",
            "descricao": "Data de disponibilização da publicação",
            "exemplo": "13 de novembro de 2024"
        },
        "autores": {
            "tipo": "string",
            "obrigatorio": False,
            "max_length": 500,
            "descricao": "Nome dos autores/requerentes da ação",
            "exemplo": "Sheila de Oliveira"
        },
        "advogados": {
            "tipo": "string",
            "obrigatorio": False,
            "max_length": 1000,
            "descricao": "Nome dos advogados com respectivas OABs",
            "exemplo": "EUNICE MENDONCA DA SILVA DE CARVALHO (OAB 138649/SP)"
        },
        "valor_principal_bruto": {
            "tipo": "float",
            "obrigatorio": False,
            "descricao": "Valor principal bruto da causa",
            "exemplo": 113611.90
        },
        "valor_juros_moratorios": {
            "tipo": "float",
            "obrigatorio": False,
            "descricao": "Valor dos juros moratórios",
            "exemplo": 5000.00
        },
        "honorarios_advocaticios": {
            "tipo": "float",
            "obrigatorio": False,
            "descricao": "Valor dos honorários advocatícios",
            "exemplo": 15532.33
        },
        "conteudo_completo": {
            "tipo": "text",
            "obrigatorio": False,
            "descricao": "Conteúdo completo da publicação",
            "exemplo": "Texto integral da publicação..."
        },
        "url_publicacao": {
            "tipo": "string",
            "obrigatorio": False,
            "descricao": "URL da publicação original, se aplicável",
            "exemplo": "http://www.diariooficial.com.br/publicacao/12345"
        },
        "fonte": {
            "tipo": "string",
            "obrigatorio": False,
            "max_length": 100,
            "descricao": "Fonte da publicação (e.g., DJE-TJSP)",
            "exemplo": "DJE-TJSP"
        }
    }
}

HTTP_STATUS_CODES = {
    200: "OK - Sucesso na operação",
    201: "Created - Recurso criado com sucesso",
    400: "Bad Request - Dados inválidos ou malformados",
    401: "Unauthorized - Não autorizado",
    403: "Forbidden - Acesso negado",
    404: "Not Found - Recurso não encontrado",
    409: "Conflict - Recurso já existe (duplicado)",
    422: "Unprocessable Entity - Dados válidos mas não processáveis",
    429: "Too Many Requests - Rate limit excedido",
    500: "Internal Server Error - Erro interno do servidor",
    502: "Bad Gateway - Erro de gateway",
    503: "Service Unavailable - Serviço indisponível"
}
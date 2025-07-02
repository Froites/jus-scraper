# src/api/config.py
"""
Configurações específicas da integração com API
"""

import os
from typing import Dict, Optional

class APIConfig:
    """Configurações específicas da API de publicações"""
    
    # URL base da API (pode ser sobrescrita por variável de ambiente)
    BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3000').rstrip('/')
    
    # Timeout para requisições HTTP
    TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))
    
    # Endpoints disponíveis na API
    ENDPOINTS = {
        'health': '/health',                            # Status da API
        'publicacoes': '/api/publicacoes',              # CRUD de publicações
        'processos': '/api/publicacoes/processos',      # Lista de números de processo
        'duplicados': '/api/publicacoes/duplicados',    # Verificação de duplicados
        'stats': '/api/publicacoes/stats',              # Estatísticas
        'search': '/api/publicacoes/search'             # Busca avançada
    }
    
    # Headers padrão para todas as requisições
    HEADERS = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'DJE-Scraper/2.0',
        'X-Client': 'dje-scraper-python'
    }
    
    # Configurações de retry e rate limiting
    MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', '3'))
    RETRY_DELAY = float(os.getenv('API_RETRY_DELAY', '1.0'))
    RETRY_BACKOFF_FACTOR = float(os.getenv('API_RETRY_BACKOFF_FACTOR', '2.0'))
    
    # Rate limiting (requests por minuto)
    REQUESTS_PER_MINUTE = int(os.getenv('API_REQUESTS_PER_MINUTE', '60'))
    BURST_LIMIT = int(os.getenv('API_BURST_LIMIT', '10'))
    
    # Configurações de batch (envio em lote)
    BATCH_SIZE = int(os.getenv('API_BATCH_SIZE', '20'))
    BATCH_DELAY = float(os.getenv('API_BATCH_DELAY', '0.1'))
    
    # Autenticação (se necessária)
    API_KEY = os.getenv('API_KEY', None)
    API_SECRET = os.getenv('API_SECRET', None)
    
    @classmethod
    def get_full_url(cls, endpoint_key: str) -> str:
        """
        Retorna URL completa para um endpoint
        
        Args:
            endpoint_key: Chave do endpoint (ex: 'publicacoes', 'health')
            
        Returns:
            URL completa do endpoint
        """
        endpoint = cls.ENDPOINTS.get(endpoint_key, '')
        # Garante que não haja barras duplas, mas que o endpoint comece com uma
        return f"{cls.BASE_URL}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
    
    @classmethod
    def get_headers(cls, include_auth: bool = False) -> Dict[str, str]:
        """
        Retorna headers para requisições
        
        Args:
            include_auth: Se deve incluir headers de autenticação
            
        Returns:
            Dicionário com headers
        """
        headers = cls.HEADERS.copy()
        
        if include_auth and cls.API_KEY:
            headers['Authorization'] = f"Bearer {cls.API_KEY}"
            
        if cls.API_SECRET:
            headers['X-API-Secret'] = cls.API_SECRET
        
        return headers
    
    @classmethod
    def configurar_url_personalizada(cls, nova_url: str):
        """
        Configura URL personalizada da API
        
        Args:
            nova_url: Nova URL base da API
        """
        cls.BASE_URL = nova_url.rstrip('/')
        print(f"✅ URL da API configurada para: {cls.BASE_URL}")
    
    @classmethod
    def configurar_autenticacao(cls, api_key: str, api_secret: Optional[str] = None):
        """
        Configura credenciais de autenticação
        
        Args:
            api_key: Chave da API
            api_secret: Segredo da API (opcional)
        """
        cls.API_KEY = api_key
        if api_secret:
            cls.API_SECRET = api_secret
        print("✅ Autenticação configurada")
    
    @classmethod
    def validar_configuracao(cls) -> Dict:
        """
        Valida configurações atuais da API
        
        Returns:
            Dict com resultado da validação
        """
        erros = []
        avisos = []
        
        # Validações obrigatórias
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
        
        # Validações com avisos
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
        """
        Converte configurações para dicionário
        
        Returns:
            Dict com todas as configurações
        """
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


# Schema esperado pela API para uma publicação
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

# Códigos de resposta HTTP esperados
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


def imprimir_configuracao_api():
    """Imprime configuração atual da API"""
    print("🔧 CONFIGURAÇÃO DA API")
    print("=" * 50)
    print(f"🌐 URL Base: {APIConfig.BASE_URL}")
    print(f"⏱️ Timeout: {APIConfig.TIMEOUT}s")
    print(f"🔄 Max Retries: {APIConfig.MAX_RETRIES}")
    print(f"⏳ Retry Delay: {APIConfig.RETRY_DELAY}s")
    print(f"📈 Retry Backoff Factor: {APIConfig.RETRY_BACKOFF_FACTOR}")
    print(f"🚦 Requests/min: {APIConfig.REQUESTS_PER_MINUTE}")
    print(f"💥 Burst Limit: {APIConfig.BURST_LIMIT}")
    print(f"📦 Batch Size: {APIConfig.BATCH_SIZE}")
    print(f"⏱️ Batch Delay: {APIConfig.BATCH_DELAY}s")
    print(f"🔑 API Key Configurada: {'Sim' if APIConfig.API_KEY else 'Não'}")
    print(f"🔒 API Secret Configurado: {'Sim' if APIConfig.API_SECRET else 'Não'}")
    
    print(f"\n📋 ENDPOINTS DISPONÍVEIS:")
    for key, endpoint in APIConfig.ENDPOINTS.items():
        url_completa = APIConfig.get_full_url(key)
        print(f"   {key:12}: {url_completa}")
    
    # Validar configuração
    validacao = APIConfig.validar_configuracao()
    if validacao["valida"]:
        print(f"\n✅ Configuração válida")
    else:
        print(f"\n❌ Problemas na configuração:")
        for erro in validacao["erros"]:
            print(f"   • {erro}")
    if validacao["avisos"]:
        print(f"\n⚠️ Avisos na configuração:")
        for aviso in validacao["avisos"]:
            print(f"   • {aviso}")


def imprimir_schema_api():
    """Imprime schema esperado pela API"""
    print("📊 SCHEMA DA API")
    print("=" * 50)
    
    for campo, config in API_SCHEMA["publicacao"].items():
        obrigatorio = "✅" if config["obrigatorio"] else "⚪"
        print(f"{obrigatorio} {campo:25} ({config['tipo']:8}) - {config['descricao']}")
        if "exemplo" in config:
            print(f"   Exemplo: {config['exemplo']}")
        if "max_length" in config:
            print(f"   Max Length: {config['max_length']}")
        if "formato" in config:
            print(f"   Formato: {config['formato']}")
    print("-" * 50)
    print("\nCódigos de Resposta HTTP:")
    for code, desc in HTTP_STATUS_CODES.items():
        print(f"  {code}: {desc}")


def configurar_api_interativo():
    """Configuração interativa da API"""
    print("🔧 CONFIGURAÇÃO INTERATIVA DA API")
    print("=" * 50)
    
    print(f"URL atual: {APIConfig.BASE_URL}")
    nova_url = input("Nova URL da API (Enter para manter): ").strip()
    
    if nova_url:
        APIConfig.configurar_url_personalizada(nova_url)
    
    timeout = input(f"Timeout em segundos (atual: {APIConfig.TIMEOUT}): ").strip()
    if timeout.isdigit():
        APIConfig.TIMEOUT = int(timeout)
        print(f"✅ Timeout configurado para: {APIConfig.TIMEOUT}s")
    
    retries = input(f"Max retries (atual: {APIConfig.MAX_RETRIES}): ").strip()
    if retries.isdigit():
        APIConfig.MAX_RETRIES = int(retries)
        print(f"✅ Max retries configurado para: {APIConfig.MAX_RETRIES}")

    api_key_input = input(f"API Key (atual: {'Configurada' if APIConfig.API_KEY else 'Não configurada'}, Enter para manter, 'none' para remover): ").strip()
    if api_key_input.lower() == 'none':
        APIConfig.API_KEY = None
        print("✅ API Key removida.")
    elif api_key_input:
        APIConfig.API_KEY = api_key_input
        print("✅ API Key configurada.")

    api_secret_input = input(f"API Secret (atual: {'Configurado' if APIConfig.API_SECRET else 'Não configurado'}, Enter para manter, 'none' para remover): ").strip()
    if api_secret_input.lower() == 'none':
        APIConfig.API_SECRET = None
        print("✅ API Secret removido.")
    elif api_secret_input:
        APIConfig.API_SECRET = api_secret_input
        print("✅ API Secret configurado.")
    
    print("\n✅ Configuração concluída!")
    imprimir_configuracao_api()


def testar_endpoints():
    """Testa todos os endpoints configurados"""
    import requests
    
    print("🔍 TESTANDO ENDPOINTS")
    print("=" * 50)
    
    session = requests.Session()
    # Pega os headers com autenticação, se houver
    session.headers.update(APIConfig.get_headers(include_auth=True)) 
    
    for nome, endpoint in APIConfig.ENDPOINTS.items():
        url = APIConfig.get_full_url(nome)
        print(f"🔗 {nome:12}: {url:50} ", end="")
        
        try:
            response = session.get(url, timeout=APIConfig.TIMEOUT)
            status_text = HTTP_STATUS_CODES.get(response.status_code, "Status Desconhecido")
            if 200 <= response.status_code < 300: # Sucesso (2xx)
                print(f"✅ {response.status_code} ({status_text})")
            elif 400 <= response.status_code < 500: # Erros do cliente (4xx)
                print(f"⚠️ {response.status_code} ({status_text})")
            else: # Outros erros (5xx, etc.)
                print(f"❌ {response.status_code} ({status_text})")
        except requests.exceptions.ConnectionError:
            print("❌ Erro de Conexão: O servidor pode estar offline ou inacessível.")
        except requests.exceptions.Timeout:
            print("❌ Timeout: A requisição excedeu o tempo limite.")
        except Exception as e:
            print(f"❌ Erro Inesperado: {str(e)}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "config":
            configurar_api_interativo()
        elif sys.argv[1] == "schema":
            imprimir_schema_api()
        elif sys.argv[1] == "test":
            testar_endpoints()
        else:
            print(f"Comando '{sys.argv[1]}' não reconhecido.")
            print("Uso: python config.py [config|schema|test]")
            imprimir_configuracao_api()
    else:
        imprimir_configuracao_api()
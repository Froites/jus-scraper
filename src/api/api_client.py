# src/api/api_client.py
"""
Cliente simples para envio de publicações para a API JusCash
"""

import requests
import json
from typing import List, Dict
from datetime import datetime

from models.publicacao import Publicacao


class JusAPIClient:
    """Cliente simples para comunicação com a API JusCash"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def enviar_publicacao(self, publicacao: Publicacao) -> dict:
        """Envia uma publicação para a API"""
        url = f"{self.base_url}/api/publicacoes"

        # PROBLEMA IDENTIFICADO: data_disponibilizacao causa erro 500
        # Vamos remover este campo por enquanto ou converter para formato ISO
        data_disponibilizacao = None
        if publicacao.data_disponibilizacao:
            if isinstance(publicacao.data_disponibilizacao, datetime):
                data_disponibilizacao = publicacao.data_disponibilizacao.isoformat()
            else:
                # Tentar converter "13 de novembro de 2024" para formato ISO
                data_str = publicacao.data_disponibilizacao
                try:
                    # Por enquanto, vamos comentar este campo que está causando erro
                    # data_disponibilizacao = self._converter_data_portuguesa(data_str)
                    data_disponibilizacao = None  # Desabilitar até resolver formato
                except:
                    data_disponibilizacao = None
        
        # Dados no formato da API - SEM data_disponibilizacao por enquanto
        dados = {
            "numero_processo": publicacao.numero_processo,
            # "data_disponibilizacao": data_disponibilizacao,  # COMENTADO - CAUSA ERRO 500
            "autores": publicacao.autores,
            "advogados": publicacao.advogados,
            "conteudo_completo": publicacao.conteudo_completo,
            "valor_principal_bruto": publicacao.valor_principal,
            "valor_juros_moratorios": publicacao.valor_juros,
            "honorarios_advocaticios": publicacao.honorarios
        }

        # Remover campos None - isso é importante!
        dados = {k: v for k, v in dados.items() if v is not None}
        
        print(f"📤 Enviando dados: {dados}")  # Debug
        
        try:
            response = self.session.post(url, json=dados, timeout=10)
            
            print(f"📊 Status: {response.status_code}")  # Debug
            if response.status_code >= 400:
                print(f"📄 Resposta erro: {response.text[:500]}")  # Debug apenas erros
            
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            else:
                response.raise_for_status()
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ Erro HTTP {e.response.status_code}: {e.response.text}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de requisição: {e}")
            return {"error": str(e)}
    
    def _converter_data_portuguesa(self, data_str: str) -> str:
        """Converte data portuguesa para formato ISO (para uso futuro)"""
        # Mapeamento de meses em português
        meses = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }
        
        # "13 de novembro de 2024" -> "2024-11-13"
        import re
        match = re.match(r'(\d+)\s+de\s+(\w+)\s+de\s+(\d+)', data_str.lower())
        if match:
            dia, mes_nome, ano = match.groups()
            mes_num = meses.get(mes_nome, '01')
            return f"{ano}-{mes_num}-{dia.zfill(2)}"
        
        return data_str  # Retorna original se não conseguir converter
    
    def enviar_lote_publicacoes(self, publicacoes: List[Publicacao]) -> dict:
        """Envia várias publicações uma por uma"""
        sucessos = 0
        erros = 0
        
        print(f"\n📡 Enviando {len(publicacoes)} publicações para API...")
        
        for i, pub in enumerate(publicacoes, 1):
            print(f"📋 {i}/{len(publicacoes)}: {pub.numero_processo or 'S/N'} ", end="")
            
            resultado = self.enviar_publicacao(pub)
            
            if "error" not in resultado:
                sucessos += 1
                print("✅")
            else:
                erros += 1
                print("❌")
        
        print(f"\n📊 Resultado: {sucessos} sucessos, {erros} erros")
        
        return {
            "total": len(publicacoes),
            "sucessos": sucessos,
            "erros": erros
        }
    
    def testar_conexao(self) -> bool:
        """Testa se a API está funcionando"""
        try:
            url = f"{self.base_url}/health"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            print("✅ API conectada e funcionando")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ API não está acessível: {e}")
            return False
    
    def criar_backup_local(self, publicacoes: List[Publicacao], nome_arquivo: str = None) -> str:
        """Cria backup local antes do envio"""
        if not nome_arquivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"data/backups/backup_pre_api_{timestamp}.json"
        
        try:
            import os
            os.makedirs(os.path.dirname(nome_arquivo), exist_ok=True)
            
            dados = [pub.to_dict() for pub in publicacoes]
            
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Backup criado: {nome_arquivo}")
            return nome_arquivo
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return ""
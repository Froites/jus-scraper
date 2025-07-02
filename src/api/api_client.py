import requests
import json
from typing import List, Dict
from datetime import datetime

from models.publicacao import Publicacao

class JusAPIClient:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def enviar_publicacao(self, publicacao: Publicacao) -> dict:
        url = f"{self.base_url}/api/publicacoes"

        data_disponibilizacao = None
        if publicacao.data_disponibilizacao:
            if isinstance(publicacao.data_disponibilizacao, datetime):
                data_disponibilizacao = publicacao.data_disponibilizacao.isoformat()
            else:
                data_str = publicacao.data_disponibilizacao
                try:
                    data_disponibilizacao = self._converter_data_portuguesa(data_str)
                except Exception:
                    data_disponibilizacao = None
        
        dados = {
            "numero_processo": publicacao.numero_processo,
            "data_disponibilizacao": data_disponibilizacao,
            "autores": publicacao.autores,
            "advogados": publicacao.advogados,
            "conteudo_completo": publicacao.conteudo_completo,
            "valor_principal_bruto": publicacao.valor_principal,
            "valor_juros_moratorios": publicacao.valor_juros,
            "honorarios_advocaticios": publicacao.honorarios
        }

        dados = {k: v for k, v in dados.items() if v is not None}
        
        try:
            response = self.session.post(url, json=dados, timeout=10)
            
            if response.status_code == 200 or response.status_code == 201:
                return response.json()
            else:
                response.raise_for_status()
                
        except requests.exceptions.HTTPError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def _converter_data_portuguesa(self, data_str: str) -> str:
        meses = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }
        
        import re
        match = re.match(r'(\d+)\s+de\s+(\w+)\s+de\s+(\d+)', data_str.lower())
        if match:
            dia, mes_nome, ano = match.groups()
            mes_num = meses.get(mes_nome, '01')
            return f"{ano}-{mes_num}-{dia.zfill(2)}"
        
        return data_str
    
    def enviar_lote_publicacoes(self, publicacoes: List[Publicacao]) -> dict:
        sucessos = 0
        erros = 0
        
        for pub in publicacoes:
            resultado = self.enviar_publicacao(pub)
            
            if "error" not in resultado:
                sucessos += 1
            else:
                erros += 1
        
        return {
            "total": len(publicacoes),
            "sucessos": sucessos,
            "erros": erros
        }
    
    def testar_conexao(self) -> bool:
        try:
            url = f"{self.base_url}/health"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            return False
    
    def criar_backup_local(self, publicacoes: List[Publicacao], nome_arquivo: str = None) -> str:
        if not nome_arquivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"data/backups/backup_pre_api_{timestamp}.json"
        
        try:
            import os
            os.makedirs(os.path.dirname(nome_arquivo), exist_ok=True)
            
            dados = [pub.to_dict() for pub in publicacoes]
            
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
            
            return nome_arquivo
        except Exception:
            return ""
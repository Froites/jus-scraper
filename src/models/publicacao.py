from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime

@dataclass
class Publicacao:
    numero_processo: Optional[str] = None
    data_disponibilizacao: Optional[str] = None
    autores: Optional[str] = None
    advogados: Optional[str] = None
    
    valor_principal: Optional[float] = None
    valor_juros: Optional[float] = None
    honorarios: Optional[float] = None
    
    conteudo_completo: Optional[str] = None
    
    url_publicacao: Optional[str] = None
    
    arquivo_cache: Optional[str] = None
    fonte: str = "DJE-TJSP"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data
    
    def to_api_format(self) -> dict:
        data_disponibilizacao = None
        if self.data_disponibilizacao:
            if isinstance(self.data_disponibilizacao, datetime):
                data_disponibilizacao = self.data_disponibilizacao.isoformat()
            else:
                data_disponibilizacao = self.data_disponibilizacao
        
        return {
            "numero_processo": self.numero_processo,
            "data_disponibilizacao": data_disponibilizacao,
            "autores": self.autores,
            "advogados": self.advogados,
            "conteudo_completo": self.conteudo_completo,
            "valor_principal_bruto": self.valor_principal,
            "valor_juros_moratorios": self.valor_juros,
            "honorarios_advocaticios": self.honorarios,
            "url_publicacao": self.url_publicacao
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Publicacao':
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            except ValueError:
                data['created_at'] = None
        return cls(**data)
    
    @classmethod
    def from_api_format(cls, data: dict) -> 'Publicacao':
        return cls(
            numero_processo=data.get('numero_processo'),
            data_disponibilizacao=data.get('data_disponibilizacao'),
            autores=data.get('autores'),
            advogados=data.get('advogados'),
            valor_principal=data.get('valor_principal_bruto'),
            valor_juros=data.get('valor_juros_moratorios'),
            honorarios=data.get('honorarios_advocaticios'),
            conteudo_completo=data.get('conteudo_completo'),
            url_publicacao=data.get('url_publicacao')
        )
    
    def tem_dados_validos(self) -> bool:
        return (
            self.numero_processo is not None and
            (self.valor_principal or self.advogados or self.autores)
        )
    
    def tem_dados_completos(self) -> bool:
        return (
            self.numero_processo is not None and
            self.autores is not None and
            (self.valor_principal or self.valor_juros or self.honorarios)
        )
    
    def calcular_valor_total(self) -> float:
        total = 0.0
        if self.valor_principal:
            total += self.valor_principal
        if self.valor_juros:
            total += self.valor_juros
        if self.honorarios:
            total += self.honorarios
        return total
    
    def validar_para_api(self) -> dict:
        erros = []
        if not self.numero_processo:
            erros.append("Número do processo é obrigatório")
        if not self.tem_dados_validos():
            erros.append("Publicação não tem dados suficientes")
        if self.numero_processo and len(self.numero_processo) < 10:
            erros.append("Número do processo parece inválido (muito curto)")
        valores = [self.valor_principal, self.valor_juros, self.honorarios]
        for valor in valores:
            if valor is not None and valor < 0:
                erros.append("Valores monetários não podem ser negativos")
        return {
            "valida": len(erros) == 0,
            "erros": erros
        }
    
    def resumo(self) -> str:
        resumo = f"Processo: {self.numero_processo or 'N/A'}"
        if self.autores:
            autor = self.autores[:30] + "..." if len(self.autores) > 30 else self.autores
            resumo += f" | Autor: {autor}"
        valor_total = self.calcular_valor_total()
        if valor_total > 0:
            resumo += f" | Total: R$ {valor_total:,.2f}"
        return resumo
    
    def resumo_detalhado(self) -> str:
        linhas = []
        linhas.append(f"📋 Processo: {self.numero_processo or 'N/A'}")
        if self.data_disponibilizacao:
            linhas.append(f"📅 Data: {self.data_disponibilizacao}")
        if self.autores:
            linhas.append(f"👤 Autor: {self.autores}")
        if self.advogados:
            advs = self.advogados[:100] + "..." if len(self.advogados) > 100 else self.advogados
            linhas.append(f"⚖️ Advogados: {advs}")
        valores = []
        if self.valor_principal:
            valores.append(f"Principal: R$ {self.valor_principal:,.2f}")
        if self.valor_juros:
            valores.append(f"Juros: R$ {self.valor_juros:,.2f}")
        if self.honorarios:
            valores.append(f"Honorários: R$ {self.honorarios:,.2f}")
        if valores:
            linhas.append(f"💰 {' | '.join(valores)}")
        return '\n'.join(linhas)
    
    def debug_info(self) -> str:
        return f"Publicacao(processo='{self.numero_processo}', valor_total={self.calcular_valor_total():.2f}, cache='{self.arquivo_cache}')"
    
    def __str__(self) -> str:
        return self.resumo()
    
    def __repr__(self) -> str:
        return self.debug_info()
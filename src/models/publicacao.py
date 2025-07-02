# src/models/publicacao.py
"""
Modelo de dados para publicação judicial
Compatível com o formato esperado pela API JusCash
"""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Publicacao:
    """Modelo para uma publicação do DJE compatível com API JusCash"""
    
    # Campos principais
    numero_processo: Optional[str] = None
    data_disponibilizacao: Optional[str] = None
    autores: Optional[str] = None
    advogados: Optional[str] = None
    
    # Valores monetários (nomes compatíveis com API)
    valor_principal: Optional[float] = None  # será enviado como valor_principal_bruto
    valor_juros: Optional[float] = None      # será enviado como valor_juros_moratorios  
    honorarios: Optional[float] = None       # será enviado como honorarios_advocaticios
    
    # Conteúdo completo da publicação
    conteudo_completo: Optional[str] = None
    
    # URL da publicação original no DJE
    url_publicacao: Optional[str] = None
    
    # Metadados internos do scraper
    arquivo_cache: Optional[str] = None
    fonte: str = "DJE-TJSP"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Executado após inicialização"""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Converte para dicionário padrão"""
        data = asdict(self)
        
        # Converter datetime para string ISO
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        
        return data
    
    def to_api_format(self) -> dict:
        """
        Converte para formato específico esperado pela API JusCash
        
        Returns:
            Dict no formato exato da API
        """
        # Converter data_disponibilizacao se necessário
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
        """Cria instância a partir de dicionário"""
        # Tratar created_at se for string
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            except:
                data['created_at'] = None
        
        return cls(**data)
    
    @classmethod
    def from_api_format(cls, data: dict) -> 'Publicacao':
        """
        Cria instância a partir do formato da API
        
        Args:
            data: Dict no formato da API
            
        Returns:
            Instância de Publicacao
        """
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
        """Verifica se tem dados mínimos válidos"""
        return (
            self.numero_processo is not None and
            (self.valor_principal or self.advogados or self.autores)
        )
    
    def tem_dados_completos(self) -> bool:
        """Verifica se tem dados completos para envio à API"""
        return (
            self.numero_processo is not None and
            self.autores is not None and
            (self.valor_principal or self.valor_juros or self.honorarios)
        )
    
    def calcular_valor_total(self) -> float:
        """Calcula valor total da publicação"""
        total = 0.0
        
        if self.valor_principal:
            total += self.valor_principal
        if self.valor_juros:
            total += self.valor_juros
        if self.honorarios:
            total += self.honorarios
        
        return total
    
    def validar_para_api(self) -> dict:
        """
        Valida dados para envio à API
        
        Returns:
            Dict com resultado da validação
        """
        erros = []
        
        if not self.numero_processo:
            erros.append("Número do processo é obrigatório")
        
        if not self.tem_dados_validos():
            erros.append("Publicação não tem dados suficientes")
        
        # Validar formato do número do processo
        if self.numero_processo and len(self.numero_processo) < 10:
            erros.append("Número do processo parece inválido (muito curto)")
        
        # Validar valores monetários
        valores = [self.valor_principal, self.valor_juros, self.honorarios]
        for valor in valores:
            if valor is not None and valor < 0:
                erros.append("Valores monetários não podem ser negativos")
        
        return {
            "valida": len(erros) == 0,
            "erros": erros
        }
    
    def resumo(self) -> str:
        """Retorna resumo textual da publicação"""
        resumo = f"Processo: {self.numero_processo or 'N/A'}"
        
        if self.autores:
            # Truncar nome se muito longo
            autor = self.autores[:30] + "..." if len(self.autores) > 30 else self.autores
            resumo += f" | Autor: {autor}"
        
        valor_total = self.calcular_valor_total()
        if valor_total > 0:
            resumo += f" | Total: R$ {valor_total:,.2f}"
        
        return resumo
    
    def resumo_detalhado(self) -> str:
        """Retorna resumo detalhado da publicação"""
        linhas = []
        
        linhas.append(f"📋 Processo: {self.numero_processo or 'N/A'}")
        
        if self.data_disponibilizacao:
            linhas.append(f"📅 Data: {self.data_disponibilizacao}")
        
        if self.autores:
            linhas.append(f"👤 Autor: {self.autores}")
        
        if self.advogados:
            # Truncar se muito longo
            advs = self.advogados[:100] + "..." if len(self.advogados) > 100 else self.advogados
            linhas.append(f"⚖️ Advogados: {advs}")
        
        # Valores
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
        """Informações de debug"""
        return f"Publicacao(processo='{self.numero_processo}', valor_total={self.calcular_valor_total():.2f}, cache='{self.arquivo_cache}')"
    
    def __str__(self) -> str:
        """Representação textual"""
        return self.resumo()
    
    def __repr__(self) -> str:
        """Representação para debug"""
        return self.debug_info()
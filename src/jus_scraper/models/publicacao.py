from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json

@dataclass
class Publicacao:
    # Modelo para representar uma publicação extraída do DJE
    
    # Identificação
    numero_processo: Optional[str] = None
    data_disponibilizacao: Optional[datetime] = None
    
    # Partes envolvidas
    autores: Optional[str] = None
    advogados: Optional[str] = None
    reu: str = "Instituto Nacional do Seguro Social - INSS"
    
    # Conteúdo
    conteudo_completo: Optional[str] = None
    
    # Valores financeiros
    valor_principal_bruto: Optional[float] = None
    valor_juros_moratorios: Optional[float] = None
    honorarios_advocaticios: Optional[float] = None
    
    # Controle
    status: str = "nova"
    data_extracao: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        #Converte para dicionário
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            else:
                data[key] = value
        return data
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

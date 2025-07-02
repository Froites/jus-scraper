# data_extractor.py
"""
Módulo responsável pela extração de dados estruturados do texto
Validação mais rigorosa para evitar processamento de conteúdo vazio
"""

import re
from datetime import datetime
from typing import Dict, Optional


class DataExtractor:
    def __init__(self):
        # Padrões otimizados baseados nos exemplos que funcionaram
        self.patterns = {
            'processo': [
                r'Processo\s*[:\s]*(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}(?:/\d{2})?)',
                r'\b(\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}(?:/\d{2})?)\b'
            ],
            'autor': [
                r'-\s*([A-ZÁÊÇÕÂÍÓÚ][A-Za-záêçõâíóú\s]{8,50}?)\s*-\s*Vistos',
                r'Auxílio-Acidente[^-]+-\s*([A-ZÁÊÇÕÂÍÓÚ][A-Za-záêçõâíóú\s]{8,50}?)\s*-\s*Vistos'
            ],
            'advogados': [
                r'ADV:\s*([A-ZÁÊÇÕÂÍÓÚ][A-Za-záêçõâíóú\s]+?)\s*\(OAB\s+\d+/[A-Z]{2}\)'
            ],
            'valor_principal': [
                r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*-\s*principal\s+bruto[/\\]líquido'
            ],
            'valor_juros': [
                r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*-\s*juros\s+moratórios'
            ],
            'valor_honorarios': [
                r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*-\s*honorários\s+advocatícios'
            ],
            'data': [
                r'Disponibilização:\s*[^,]*,\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})'
            ]
        }

    def is_conteudo_relevante(self, texto: str) -> bool:
        """
        Verifica se o conteúdo é relevante para processamento
        Critérios mais rigorosos baseados na análise dos arquivos
        """
        if not texto:
            return False
        
        # Rejeitar explicitamente conteúdo com falha
        if "EXTRAÇÃO FALHOU" in texto:
            print("         ❌ Rejeitado: Contém 'EXTRAÇÃO FALHOU'")
            return False
        
        # Critério de tamanho mais rigoroso
        tamanho_texto = len(texto.strip())
        if tamanho_texto < 6000:  # Aumentado de 1000 para 6000
            print(f"         ❌ Rejeitado: Muito pequeno ({tamanho_texto} chars, mín: 6000)")
            return False
        
        # Verificar indicadores obrigatórios de sucesso
        indicadores_obrigatorios = [
            "Publicação Oficial do Tribunal",
            "Diário da Justiça Eletrônico",
            "Processo "
        ]
        
        # TODOS os indicadores obrigatórios devem estar presentes
        for indicador in indicadores_obrigatorios:
            if indicador not in texto:
                print(f"         ❌ Rejeitado: Falta indicador obrigatório '{indicador}'")
                return False
        
        # Verificar indicadores adicionais de qualidade
        indicadores_qualidade = [
            "ADV:",
            "Vistos",
            "R$",
            "Cumprimento de Sentença",
            "Fazenda Pública"
        ]
        
        # Contar indicadores de qualidade presentes
        contador_qualidade = sum(1 for ind in indicadores_qualidade if ind in texto)
        
        if contador_qualidade < 3:  # Pelo menos 3 indicadores de qualidade
            print(f"         ❌ Rejeitado: Poucos indicadores de qualidade ({contador_qualidade}/5)")
            return False
        
        # Verificar se tem estrutura típica de decisão judicial
        tem_estrutura_judicial = any(termo in texto for termo in [
            "homologo", "Homologação", "decisão", "sentença", 
            "despacho", "determino", "defiro"
        ])
        
        if not tem_estrutura_judicial:
            print("         ❌ Rejeitado: Não tem estrutura de decisão judicial")
            return False
        
        print(f"         ✅ Aprovado: {tamanho_texto} chars, {contador_qualidade} indicadores")
        return True

    def extrair_dados(self, texto: str) -> Dict:
        """Extrai todos os dados estruturados do texto"""
        dados = {
            'processo': None,
            'data': None,
            'autores': None,
            'advogados': None,
            'valores': {
                'principal': None,
                'juros': None,
                'honorarios': None
            }
        }
        
        if not texto:
            return dados
        
        # Extrair processo
        dados['processo'] = self._extrair_processo(texto)
        
        # Extrair data
        dados['data'] = self._extrair_data(texto)
        
        # Extrair autor
        dados['autores'] = self._extrair_autor(texto)
        
        # Extrair advogados
        dados['advogados'] = self._extrair_advogados(texto)
        
        # Extrair valores
        dados['valores'] = self._extrair_valores(texto)
        
        return dados

    def _extrair_processo(self, texto: str) -> Optional[str]:
        """Extrai número do processo"""
        for pattern in self.patterns['processo']:
            matches = re.findall(pattern, texto)
            if matches:
                return matches[0]  # Retorna o primeiro encontrado
        return None

    def _extrair_data(self, texto: str) -> Optional[str]:
        """Extrai data de disponibilização"""
        for pattern in self.patterns['data']:
            match = re.search(pattern, texto)
            if match:
                return match.group(1)
        return None

    def _extrair_autor(self, texto: str) -> Optional[str]:
        """Extrai nome do autor"""
        for pattern in self.patterns['autor']:
            match = re.search(pattern, texto)
            if match:
                nome = match.group(1).strip()
                if self._is_nome_valido(nome):
                    return nome
        return None

    def _extrair_advogados(self, texto: str) -> Optional[str]:
        """Extrai nomes dos advogados"""
        advogados = []
        
        for pattern in self.patterns['advogados']:
            matches = re.findall(pattern, texto)
            for match in matches:
                nome = match.strip()
                if 5 <= len(nome) <= 60 and nome not in advogados:
                    advogados.append(nome)
        
        return '; '.join(advogados) if advogados else None

    def _extrair_valores(self, texto: str) -> Dict:
        """Extrai valores monetários"""
        valores = {'principal': None, 'juros': None, 'honorarios': None}
        
        # Principal
        for pattern in self.patterns['valor_principal']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                valores['principal'] = self._converter_valor(match.group(1))
                break
        
        # Juros
        for pattern in self.patterns['valor_juros']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                valores['juros'] = self._converter_valor(match.group(1))
                break
        
        # Honorários
        for pattern in self.patterns['valor_honorarios']:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                valores['honorarios'] = self._converter_valor(match.group(1))
                break
        
        return valores

    def _converter_valor(self, valor_str: str) -> Optional[float]:
        """Converte string de valor para float"""
        try:
            # Remove pontos (milhares) e substitui vírgula por ponto (decimais)
            valor_limpo = valor_str.replace('.', '').replace(',', '.')
            return float(valor_limpo)
        except ValueError:
            return None

    def _is_nome_valido(self, nome: str) -> bool:
        """Verifica se um nome é válido"""
        if not nome or len(nome) < 8 or len(nome) > 50:
            return False
        
        # Verificar se tem pelo menos 2 palavras
        if len(nome.split()) < 2:
            return False
        
        # Excluir termos legais comuns
        termos_excluir = [
            'tribunal', 'justiça', 'processo', 'vistos', 'despacho',
            'cumprimento', 'sentença', 'fazenda', 'pública'
        ]
        
        nome_lower = nome.lower()
        return not any(termo in nome_lower for termo in termos_excluir)

    def validar_extracao_completa(self, dados: Dict) -> bool:
        """
        Valida se a extração foi bem-sucedida
        Retorna True apenas se extraiu dados essenciais
        """
        # Deve ter pelo menos número do processo
        if not dados.get('processo'):
            return False
        
        # Deve ter pelo menos um valor ou um advogado
        tem_valor = any(dados['valores'].values())
        tem_advogado = dados.get('advogados')
        
        return tem_valor or tem_advogado

    def relatorio_extracao(self, dados: Dict) -> str:
        """Gera relatório da extração realizada"""
        relatorio = []
        
        relatorio.append(f"🔍 EXTRAÇÃO REALIZADA:")
        relatorio.append(f"   📋 Processo: {dados.get('processo', 'NÃO ENCONTRADO')}")
        relatorio.append(f"   📅 Data: {dados.get('data', 'NÃO ENCONTRADO')}")
        relatorio.append(f"   👤 Autor: {dados.get('autores', 'NÃO ENCONTRADO')}")
        relatorio.append(f"   ⚖️ Advogados: {dados.get('advogados', 'NÃO ENCONTRADO')}")
        
        valores = dados.get('valores', {})
        principal = valores.get('principal', 0) or 0
        juros = valores.get('juros', 0) or 0
        honorarios = valores.get('honorarios', 0) or 0
        
        relatorio.append(f"   💰 Principal: R$ {principal:,.2f}")
        relatorio.append(f"   💸 Juros: R$ {juros:,.2f}")
        relatorio.append(f"   🏛️ Honorários: R$ {honorarios:,.2f}")
        
        return '\n'.join(relatorio)
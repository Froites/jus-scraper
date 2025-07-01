import re
from typing import Optional, List, Dict
from datetime import datetime

class TextParser:

    PROCESSO_PATTERN = r'\b\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}\b'
    DATA_PATTERN = r'\b\d{2}/\d{2}/\d{4}\b'
    
    # Padrões para valores monetários brasileiros
    VALOR_PATTERN = r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
    
    # Padrões específicos para valores do processo
    VALOR_TOTAL_PATTERN = r'(?:importe total|valor total|total).*?R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
    PRINCIPAL_PATTERN = r'(?:R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*-\s*principal bruto/?líquido)'
    JUROS_PATTERN = r'(?:R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*-\s*juros moratórios)'
    HONORARIOS_PATTERN = r'(?:R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*-\s*honorários advocatícios)'
    
    # Padrão para nomes
    NOME_PESSOA_PATTERN = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:da|de|do|dos|das|e)\s+[A-Z][a-z]+)*\b'
    
    # Padrão para advogados
    ADVOGADO_PATTERN = r'ADV:\s*([A-Z][A-Za-z\s]+?)(?:\s*\(OAB\s*\d+/[A-Z]{2}\))'
    
    @staticmethod
    def extrair_numero_processo(texto: str) -> Optional[str]:
        matches = re.findall(TextParser.PROCESSO_PATTERN, texto)
        return matches[0] if matches else None
    
    @staticmethod
    def extrair_todos_processos(texto: str) -> List[str]:
        return re.findall(TextParser.PROCESSO_PATTERN, texto)
    
    @staticmethod
    def extrair_datas(texto: str) -> List[datetime]:
        datas = []
        matches = re.findall(TextParser.DATA_PATTERN, texto)
        
        for match in matches:
            try:
                data = datetime.strptime(match, '%d/%m/%Y')
                datas.append(data)
            except ValueError:
                continue
                
        return datas
    
    @staticmethod
    def extrair_valores_monetarios(texto: str) -> List[float]:
        valores = []
        matches = re.findall(TextParser.VALOR_PATTERN, texto, re.IGNORECASE)
        
        for match in matches:
            try:
                valor_str = match.replace('.', '').replace(',', '.')
                valor = float(valor_str)
                valores.append(valor)
            except ValueError:
                continue
                
        return valores
    
    @staticmethod
    def extrair_valores_estruturados(texto: str) -> Dict[str, Optional[float]]:
        valores = {
            'total': None,
            'principal_bruto': None,
            'principal_liquido': None,
            'juros_moratorios': None,
            'honorarios_advocaticios': None
        }
        
        # Valor total
        match_total = re.search(TextParser.VALOR_TOTAL_PATTERN, texto, re.IGNORECASE)
        if match_total:
            valores['total'] = TextParser._converter_valor_brasileiro(match_total.group(1))
        
        # Principal bruto/líquido
        match_principal = re.search(TextParser.PRINCIPAL_PATTERN, texto, re.IGNORECASE)
        if match_principal:
            valor_principal = TextParser._converter_valor_brasileiro(match_principal.group(1))
            valores['principal_bruto'] = valor_principal
            valores['principal_liquido'] = valor_principal
        
        # Juros moratórios
        match_juros = re.search(TextParser.JUROS_PATTERN, texto, re.IGNORECASE)
        if match_juros:
            valores['juros_moratorios'] = TextParser._converter_valor_brasileiro(match_juros.group(1))
        
        # Honorários advocatícios
        match_honorarios = re.search(TextParser.HONORARIOS_PATTERN, texto, re.IGNORECASE)
        if match_honorarios:
            valores['honorarios_advocaticios'] = TextParser._converter_valor_brasileiro(match_honorarios.group(1))
        
        return valores
    
    @staticmethod
    def _converter_valor_brasileiro(valor_str: str) -> Optional[float]:
        try:
            return float(valor_str.replace('.', '').replace(',', '.'))
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def extrair_valor_principal(texto: str) -> Optional[float]:
        valores = TextParser.extrair_valores_estruturados(texto)
        return valores['principal_bruto']
    
    @staticmethod
    def extrair_juros_moratorios(texto: str) -> Optional[float]:
        valores = TextParser.extrair_valores_estruturados(texto)
        return valores['juros_moratorios']
    
    @staticmethod
    def extrair_honorarios_advocaticios(texto: str) -> Optional[float]:
        valores = TextParser.extrair_valores_estruturados(texto)
        return valores['honorarios_advocaticios']
    
    @staticmethod
    def extrair_autor_processo(texto: str) -> Optional[str]:
        
        # Padrão 1: Após número do processo, tipo de ação e antes de "Vistos"
        padrao1 = r'Processo\s+\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}.*?-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:da|de|do|dos|das)\s+[A-Z][a-z]+)*)\s*-\s*Vistos'
        match1 = re.search(padrao1, texto, re.IGNORECASE)
        if match1:
            nome = match1.group(1).strip()

            if not TextParser._e_nome_entidade(nome):
                return nome

        padrao2 = r'(?:Auxílio-Acidente|Auxílio-Doença|Incapacidade Laborativa).*?-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:da|de|do|dos|das)\s+[A-Z][a-z]+)*)\s*-'
        match2 = re.search(padrao2, texto, re.IGNORECASE)
        if match2:
            nome = match2.group(1).strip()
            if not TextParser._e_nome_entidade(nome):
                return nome

        padrao3 = r'-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:da|de|do|dos|das)\s+[A-Z][a-z]+)*)\s*-\s*Vistos'
        match3 = re.search(padrao3, texto)
        if match3:
            nome = match3.group(1).strip()
            if not TextParser._e_nome_entidade(nome):
                return nome
        
        return None
    
    @staticmethod
    def _e_nome_entidade(nome: str) -> bool:
        entidades = [
            'INSS', 'Instituto Nacional', 'Fazenda Pública', 'Estado', 
            'União', 'Tribunal', 'São Paulo', 'Vistos', 'Cumprimento',
            'Sentença', 'Procedimento', 'Xp Pjus', 'Fundo de Investimento'
        ]
        nome_lower = nome.lower()
        return any(entidade.lower() in nome_lower for entidade in entidades)
    
    @staticmethod
    def extrair_advogados(texto: str) -> Optional[str]:
        advogados = []
        
        # Padrão principal: "ADV: NOME (OAB xxxxx/SP)"
        padrao_completo = r'ADV:\s*([A-Z][A-Za-z\s]+?)\s*\(OAB\s*\d+/[A-Z]{2}\)'
        matches_completo = re.findall(padrao_completo, texto, re.IGNORECASE)
        
        for match in matches_completo:
            nome_adv = match.strip()
            if nome_adv and len(nome_adv) > 5:
                advogados.append(nome_adv)

        if not advogados:
            padrao_simples = r'ADV:\s*([A-Z][A-Za-z\s]+?)(?:\s*\(|$|\n|\.)'
            matches_simples = re.findall(padrao_simples, texto, re.IGNORECASE)
            
            for match in matches_simples:
                nome_adv = match.strip()
                if nome_adv and len(nome_adv) > 5:
                    advogados.append(nome_adv)

        if not advogados:
            padrao_oab = r'([A-Z][A-Za-z\s]+?)\s*\(OAB\s*\d+/[A-Z]{2}\)'
            matches_oab = re.findall(padrao_oab, texto)
            
            for match in matches_oab:
                nome_adv = match.strip()
                if (nome_adv and len(nome_adv) > 5 and 
                    len(nome_adv.split()) >= 2 and
                    not any(word.lower() in ['processo', 'vistos', 'int'] for word in nome_adv.split())):
                    advogados.append(nome_adv)
        
        # Remover duplicatas mantendo ordem
        advogados_unicos = []
        for adv in advogados:
            if adv not in advogados_unicos:
                advogados_unicos.append(adv)
        
        return '; '.join(advogados_unicos) if advogados_unicos else None
    
    @staticmethod
    def extrair_nomes_pessoas(texto: str) -> List[str]:
        nomes = re.findall(TextParser.NOME_PESSOA_PATTERN, texto)
        
        # Filtrar nomes muito comuns que não são pessoas
        filtros = [
            'São Paulo', 'Estado', 'Tribunal', 'Justiça', 'Instituto Nacional',
            'Fazenda Pública', 'Diário', 'Processo Civil', 'Código', 'Artigo',
            'Vistos', 'Int', 'Publique', 'Intime', 'Cumprimento', 'Sentença',
            'Procedimento', 'Sumário', 'Incapacidade Laborativa', 'Permanente',
            'Capital', 'Parte', 'Página', 'Auxílio', 'Acidente', 'Doença'
        ]
        
        nomes_filtrados = []
        for nome in nomes:
            # Deve ter pelo menos 2 palavras
            if len(nome.split()) < 2:
                continue
            if not any(filtro.lower() in nome.lower() for filtro in filtros):
                if len(nome) >= 6:
                    nomes_filtrados.append(nome)
        
        return list(set(nomes_filtrados))
    
    @staticmethod
    def limpar_texto(texto: str) -> str:
        if not texto:
            return ""
        texto = re.sub(r'\n+', ' ', texto)
        # Remover espaços extras
        texto = re.sub(r'\s+', ' ', texto)
        # Trim
        return texto.strip()
    
    @staticmethod
    def extrair_informacoes_completas(texto: str) -> Dict[str, any]:
        # Extrai todas as informações
        resultado = {
            'processos': TextParser.extrair_todos_processos(texto),
            'processo_principal': TextParser.extrair_numero_processo(texto),
            'autor': TextParser.extrair_autor_processo(texto),
            'advogados': TextParser.extrair_advogados(texto),
            'datas': TextParser.extrair_datas(texto),
            'valores': TextParser.extrair_valores_estruturados(texto),
            'nomes_pessoas': TextParser.extrair_nomes_pessoas(texto)
        }
        
        return resultado
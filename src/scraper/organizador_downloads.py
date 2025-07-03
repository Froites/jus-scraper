import os
import shutil
from datetime import datetime
import json
import re

class OrganizadorDownloads:
    def __init__(self, pasta_download="./downloads_dje"):
        self.pasta_download = os.path.abspath(pasta_download)
        self.pasta_backup = os.path.join(self.pasta_download, "backup")
        self.pasta_duplicados = os.path.join(self.pasta_download, "duplicados")
        self.pasta_organizados = os.path.join(self.pasta_download, "organizados")
        
    def analisar_downloads(self):
        """Analisa todos os downloads e identifica problemas como duplicatas ou arquivos pequenos."""
        if not os.path.exists(self.pasta_download):
            return None
        
        arquivos = [f for f in os.listdir(self.pasta_download) 
                   if f.endswith('.pdf') and os.path.isfile(os.path.join(self.pasta_download, f))]
        
        if not arquivos:
            return None
        
        arquivos_info = {}
        tamanhos = {}
        nomes_similares = {}
        
        for arquivo in arquivos:
            caminho = os.path.join(self.pasta_download, arquivo)
            tamanho = os.path.getsize(caminho)
            data_mod = os.path.getmtime(caminho)
            
            arquivos_info[arquivo] = {
                'tamanho': tamanho,
                'data_modificacao': data_mod,
                'caminho': caminho
            }
            
            if tamanho not in tamanhos:
                tamanhos[tamanho] = []
            tamanhos[tamanho].append(arquivo)
            
            nome_base = os.path.splitext(arquivo)[0]
            nome_limpo = self._limpar_nome_para_comparacao(nome_base)
            
            if nome_limpo not in nomes_similares:
                nomes_similares[nome_limpo] = []
            nomes_similares[nome_limpo].append(arquivo)
        
        duplicatas_tamanho = {t: arqs for t, arqs in tamanhos.items() if len(arqs) > 1}
        nomes_duplicados = {n: arqs for n, arqs in nomes_similares.items() if len(arqs) > 1}
        pequenos = [arq for arq, info in arquivos_info.items() if info['tamanho'] < 10000] # < 10KB
        
        return {
            'total_arquivos': len(arquivos),
            'duplicatas_tamanho': duplicatas_tamanho,
            'nomes_similares': nomes_duplicados,
            'arquivos_pequenos': pequenos,
            'arquivos_info': arquivos_info
        }
    
    def _limpar_nome_para_comparacao(self, nome):
        """Remove números, timestamps e caracteres especiais para comparação de nomes."""
        nome = re.sub(r'_?\d{8}_\d{6}', '', nome)
        nome = re.sub(r'_?\d{3,}', '', nome)
        nome = re.sub(r'[_\-\(\)\[\]]+', '', nome)
        return nome.lower().strip()
    
    def renomear_sequencial(self):
        """Renomeia todos os PDFs com numeração sequencial baseada na data de modificação."""
        arquivos = [f for f in os.listdir(self.pasta_download) 
                   if f.endswith('.pdf') and os.path.isfile(os.path.join(self.pasta_download, f))]
        
        if not arquivos:
            return
        
        arquivos_com_data = []
        for arquivo in arquivos:
            caminho = os.path.join(self.pasta_download, arquivo)
            data_mod = os.path.getmtime(caminho)
            arquivos_com_data.append((data_mod, arquivo))
        
        arquivos_com_data.sort()
        
        self._criar_backup()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for i, (data_mod, arquivo_original) in enumerate(arquivos_com_data, 1):
            try:
                novo_nome = f"dje_{i:03d}_{timestamp}.pdf"
                caminho_original = os.path.join(self.pasta_download, arquivo_original)
                novo_caminho = os.path.join(self.pasta_download, novo_nome)
                
                if os.path.exists(novo_caminho):
                    contador = 1
                    while os.path.exists(novo_caminho):
                        novo_nome = f"dje_{i:03d}_{timestamp}_{contador:02d}.pdf"
                        novo_caminho = os.path.join(self.pasta_download, novo_nome)
                        contador += 1
                
                os.rename(caminho_original, novo_caminho)
            except Exception:
                pass
    
    def remover_duplicatas(self):
        """Remove arquivos duplicados (baseado no mesmo tamanho), mantendo o mais antigo."""
        analise = self.analisar_downloads()
        if not analise: return
        
        duplicatas = analise.get('duplicatas_tamanho', {})
        if not duplicatas: return
        
        os.makedirs(self.pasta_duplicados, exist_ok=True)
        
        for tamanho, arquivos_dup in duplicatas.items():
            if len(arquivos_dup) <= 1:
                continue
            
            arquivos_com_data = []
            for arquivo in arquivos_dup:
                caminho = os.path.join(self.pasta_download, arquivo)
                data_mod = os.path.getmtime(caminho)
                arquivos_com_data.append((data_mod, arquivo))
            
            arquivos_com_data.sort()
            
            arquivo_manter = arquivos_com_data[0][1]
            
            for _, arquivo_remover in arquivos_com_data[1:]:
                try:
                    origem = os.path.join(self.pasta_download, arquivo_remover)
                    destino = os.path.join(self.pasta_duplicados, arquivo_remover)
                    
                    if os.path.exists(destino):
                        nome_base, ext = os.path.splitext(arquivo_remover)
                        contador = 1
                        while os.path.exists(destino):
                            novo_nome = f"{nome_base}_dup{contador:02d}{ext}"
                            destino = os.path.join(self.pasta_duplicados, novo_nome)
                            contador += 1
                    
                    shutil.move(origem, destino)
                except Exception:
                    pass # Log errors
    
    def organizar_por_data(self):
        arquivos = [f for f in os.listdir(self.pasta_download) 
                   if f.endswith('.pdf') and os.path.isfile(os.path.join(self.pasta_download, f))]
        
        if not arquivos:
            return
        
        self._criar_backup()
        
        grupos_data = {}
        for arquivo in arquivos:
            caminho = os.path.join(self.pasta_download, arquivo)
            data_mod = os.path.getmtime(caminho)
            data_str = datetime.fromtimestamp(data_mod).strftime("%Y-%m-%d")
            
            if data_str not in grupos_data:
                grupos_data[data_str] = []
            grupos_data[data_str].append(arquivo)
        
        for data, arquivos_data in grupos_data.items():
            pasta_data = os.path.join(self.pasta_organizados, data)
            os.makedirs(pasta_data, exist_ok=True)
            
            for arquivo in arquivos_data:
                try:
                    origem = os.path.join(self.pasta_download, arquivo)
                    destino = os.path.join(pasta_data, arquivo)
                    shutil.move(origem, destino)
                except Exception:
                    pass # Log errors
    
    def _criar_backup(self):
        try:
            os.makedirs(self.pasta_backup, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pasta_backup_timestamped = os.path.join(self.pasta_backup, f"backup_{timestamp}")
            os.makedirs(pasta_backup_timestamped, exist_ok=True)
            
            arquivos = [f for f in os.listdir(self.pasta_download) 
                       if f.endswith('.pdf') and os.path.isfile(os.path.join(self.pasta_download, f))]
            
            for arquivo in arquivos:
                origem = os.path.join(self.pasta_download, arquivo)
                destino = os.path.join(pasta_backup_timestamped, arquivo)
                shutil.copy2(origem, destino)
        except Exception:
            pass
    
    def limpar_arquivos_pequenos(self, tamanho_minimo=5000):
        """Remove arquivos PDF menores que o tamanho mínimo especificado."""
        arquivos = [f for f in os.listdir(self.pasta_download) 
                   if f.endswith('.pdf') and os.path.isfile(os.path.join(self.pasta_download, f))]
        
        for arquivo in arquivos:
            caminho = os.path.join(self.pasta_download, arquivo)
            tamanho = os.path.getsize(caminho)
            
            if tamanho < tamanho_minimo:
                try:
                    os.remove(caminho)
                except Exception:
                    pass
    
    def gerar_relatorio(self):
        """Gera um relatório detalhado dos downloads em formato JSON."""
        analise = self.analisar_downloads()
        if not analise: return None
        
        relatorio = {
            'data_analise': datetime.now().isoformat(),
            'pasta_download': self.pasta_download,
            'estatisticas': {
                'total_arquivos': analise['total_arquivos'],
                'grupos_duplicatas': len(analise['duplicatas_tamanho']),
                'arquivos_pequenos': len(analise['arquivos_pequenos']),
                'grupos_nomes_similares': len(analise['nomes_similares'])
            },
            'detalhes': analise
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_relatorio = f"relatorio_downloads_{timestamp}.json"
        
        with open(nome_relatorio, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2, default=str)
        
        return nome_relatorio # Retorna o nome do arquivo gerado


def main():
    pasta = input("Pasta de downloads (Enter para './downloads_dje'): ").strip()
    if not pasta:
        pasta = "./downloads_dje"
    
    organizador = OrganizadorDownloads(pasta)
    
    print("\n--- Organizador de Downloads DJE ---")
    print(f"Pasta atual: {organizador.pasta_download}")
    print("------------------------------------")
    print("Opções:")
    print("  1. Analisar downloads")
    print("  2. Renomear sequencialmente")
    print("  3. Remover duplicatas")
    print("  4. Organizar por data")
    print("  5. Limpar arquivos pequenos")
    print("  6. Gerar relatório")
    print("  0. Sair")

    while True:
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == "0":
            break
        elif opcao == "1":
            organizador.analisar_downloads()
            print("Análise concluída.")
        elif opcao == "2":
            confirm = input("Isso renomeará TODOS os PDFs. Continuar? (s/n): ").strip().lower()
            if confirm == 's':
                organizador.renomear_sequencial()
                print("Renomeação concluída.")
        elif opcao == "3":
            organizador.remover_duplicatas()
            print("Remoção de duplicatas concluída.")
        elif opcao == "4":
            organizador.organizar_por_data()
            print("Organização por data concluída.")
        elif opcao == "5":
            tamanho = input("Tamanho mínimo em bytes (padrão 5000): ").strip()
            tamanho = int(tamanho) if tamanho.isdigit() else 5000
            organizador.limpar_arquivos_pequenos(tamanho)
            print("Limpeza de arquivos pequenos concluída.")
        elif opcao == "6":
            relatorio_file = organizador.gerar_relatorio()
            if relatorio_file:
                print(f"Relatório gerado: {relatorio_file}")
            else:
                print("Não foi possível gerar o relatório.")
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()
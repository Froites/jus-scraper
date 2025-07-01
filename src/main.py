import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from jus_scraper.scrapers.dje_scraper import DJEScraper
import json

def salvar_resultados(publicacoes: list, nome_arquivo: str = "resultados.json"):
    resultados_dir = Path("resultados")
    resultados_dir.mkdir(exist_ok=True)
    
    arquivo = resultados_dir / nome_arquivo
    dados = [pub.to_dict() for pub in publicacoes]
    
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def main():
    print("DJE Scraper")
    print("=" * 40)

    scraper = DJEScraper()

    publicacoes = scraper.scrape_test()

    salvar_resultados(publicacoes, "teste_inicial.json")

if __name__ == "__main__":
    main()

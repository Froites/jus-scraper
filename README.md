# 🏛️ Jus-Scraper: Extração Automatizada de Publicações Judiciais do DJE-TJSP

Este projeto é uma aplicação de web scraping desenvolvida em Python para extrair publicações do Diário da Justiça Eletrônico (DJE) do Tribunal de Justiça de São Paulo (TJSP). Ele é capaz de baixar PDFs, extrair dados estruturados dessas publicações (como número de processo, autores, advogados e valores) e, opcionalmente, enviar esses dados para uma API externa. Além disso, ele oferece funcionalidades para organizar e gerenciar os downloads.

## ✨ Funcionalidades

* **Extração do Site:** Realiza buscas no DJE-TJSP por publicações de uma data específica, baixando os PDFs relevantes.
* **Processamento de PDFs:** Extrai automaticamente informações estruturadas (número de processo, autores, advogados, valores de principal, juros e honorários, e conteúdo completo) de PDFs locais.
* **Deduplicação Inteligente:** Remove publicações duplicadas com base no número do processo antes do envio e do salvamento local, movendo PDFs duplicados para uma pasta específica.
* **Integração com API:** Envia as publicações extraídas e deduplicadas para uma API externa (configurável).
* **Gerenciamento de Downloads:** Ferramentas para listar, renomear, organizar por data e limpar arquivos PDF baixados.
* **Automação com Docker e Cron:** Configuração para rodar a extração e o envio à API automaticamente em um horário programado dentro de um container Docker.

## ⚙️ Pré-requisitos

Para rodar este projeto, você precisará de:

* **Python 3.9+**
* **pip** (gerenciador de pacotes Python)
* **Google Chrome** instalado no seu sistema (para execução local, o `chromedriver` será gerenciado pelo Selenium).
* **Docker Desktop** (para execução containerizada).
* Um **endpoint de API** para o envio dos dados (ex: `http://localhost:3000/api/publicacoes`).

## 🚀 Instalação

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/jus-scraper.git](https://github.com/seu-usuario/jus-scraper.git)
    cd jus-scraper
    ```
2.  **Instale as dependências Python:**
    ```bash
    pip install -r requirements.txt
    ```

## 🏃 Como Rodar

Existem duas formas principais de executar a aplicação: **localmente (interativo)** e **containerizada (automatizada via Docker)**.

### A. Execução Local (Interativa)

Você pode rodar o scraper e suas ferramentas diretamente do seu ambiente Python.

1.  **Navegue até o diretório `src/scraper`:**
    ```bash
    cd src/scraper
    ```
2.  **Execute o scraper principal:**
    ```bash
    python dje_scraper.py
    ```
    Um menu de opções será exibido:
    ```
    OPÇÕES:
    1. Extrair do site (com download)
    2. Processar PDFs já baixados
    3. Listar downloads
    4. Limpar downloads antigos
    5. Enviar publicações para a API (após extração ou processamento de PDFs)
    ```
    * **Opções 1 ou 2:** Realizam a extração e o processamento dos dados. Ao final, o script perguntará se você deseja enviar os resultados para a API.
    * **Opção 5:** Processa os PDFs existentes na pasta de downloads (`./downloads_dje`) e, em seguida, tenta enviar os resultados deduplicados para a API.

3.  **Execute o organizador de downloads (opcional):**
    Para gerenciar os PDFs baixados, você pode usar o `organizador_downloads.py`.
    ```bash
    python organizador_downloads.py
    ```
    Este script também apresentará um menu interativo para análise, renomeação, remoção de duplicatas e organização por data.

### B. Execução Dockerizada (Automatizada)

Para uma execução contínua e automatizada (ex: em um servidor), recomenda-se usar Docker. A imagem Docker configurará um trabalho `cron` para executar a extração e o envio à API diariamente à 1h da manhã (horário do container, configurado para `America/Sao_Paulo`).

1.  **Navegue até o diretório raiz do projeto (`jus-scraper/`):**
    ```bash
    cd jus-scraper
    ```
2.  **Construa a imagem Docker:**
    ```bash
    docker build -t jus-scraper-automated .
    ```
3.  **Execute o container Docker:**
    É crucial que a sua API esteja acessível pelo container Docker. Se a API estiver rodando na mesma máquina, você pode usar `host.docker.internal` (para Docker Desktop) ou o IP da máquina host (para VPS) na variável `API_BASE_URL`.

    ```bash
    docker run -d --name jus-scraper-runner \
    -e API_BASE_URL="[http://host.docker.internal:3000](http://host.docker.internal:3000)" \
    -e API_KEY="sua_chave_api_se_tiver" \
    -e API_SECRET="seu_secret_api_se_tiver" \
    jus-scraper-automated
    ```
    * `-d`: Roda o container em modo "detached" (em segundo plano).
    * `--name jus-scraper-runner`: Atribui um nome amigável ao seu container.
    * `-e API_BASE_URL="..."`: Define a URL da sua API. **Ajuste este valor!**
    * `-e API_KEY="..."`, `-e API_SECRET="..."`: Se sua API requer autenticação, defina estas variáveis.
    * `jus-scraper-automated`: O nome da imagem Docker que você construiu.

4.  **Verificar Logs:**
    Para acompanhar a execução do `cron` e do script Python dentro do container:
    ```bash
    docker logs -f jus-scraper-runner
    ```
    Os logs detalhados das execuções diárias serão armazenados dentro do container em `/var/log/cron/daily_scrape.log` e `/app/src/logs/daily_run.log`. Você pode acessá-los com `docker exec`:
    ```bash
    docker exec jus-scraper-runner cat /var/log/cron/daily_scrape.log
    docker exec jus-scraper-runner cat /app/src/logs/daily_run.log
    ```

## 🔗 Integração com API

A aplicação envia as `Publicacao`es extraídas e deduplicadas para o endpoint `/api/publicacoes` da sua API. O modelo `Publicacao` (`src/models/publicacao.py`) define a estrutura dos dados enviados. A deduplicação é realizada localmente antes do envio, garantindo que apenas registros únicos sejam submetidos.

As configurações da API, incluindo a URL base, timeout e cabeçalhos de autenticação, são gerenciadas em `src/api/config.py` e podem ser sobrescritas por variáveis de ambiente (`API_BASE_URL`, `API_KEY`, `API_SECRET`).

## ⚙️ Configuração

Você pode ajustar algumas configurações por meio de variáveis de ambiente ou editando os arquivos de configuração:

* **`API_BASE_URL`**: A URL base da sua API (padrão: `http://localhost:3000`). Pode ser configurada via variável de ambiente ou em `src/api/config.py`.
* **`API_KEY`**, **`API_SECRET`**: Chaves de autenticação para sua API, se necessário. Configuradas via variáveis de ambiente ou em `src/api/config.py`.
* **Parâmetros de Busca:** A data de busca e os termos de pesquisa (`"RPV" e "pagamento pelo INSS"`) estão definidos no `src/scraper/dje_scraper.py` e podem ser ajustados.

## 📝 Logging

A aplicação utiliza o módulo `src/utils/logger.py` para registrar as operações.
Os logs são salvos em:
* `./logs/dje_scraper_AAAA_MM_DD.log` (para execuções locais interativas)
* `/var/log/cron/daily_scrape.log` (logs do cron no Docker)
* `/app/src/logs/daily_run.log` (logs do script de execução diária no Docker)

##  troubleshooting

* **`FileNotFoundError` ou `No such file or directory`:** Verifique se as pastas `data/cache`, `data/results`, `data/backups`, `data/downloads_dje`, e `logs` existem na raiz do projeto. O script as cria, mas permissões ou erros de caminho podem causar problemas.
* **Selenium/Chrome Erros:**
    * **Local:** Certifique-se de que o Google Chrome está instalado e atualizado.
    * **Docker:** O `Dockerfile` já instala `chromium-browser` e `chromium-chromedriver`. Verifique os logs do Docker para mensagens de erro relacionadas ao navegador. Certifique-se de que a flag `--headless` está configurada para ambientes sem GUI.
* **Conexão com a API:**
    * Verifique se sua API está rodando e acessível no endereço configurado (`API_BASE_URL`).
    * Se estiver usando Docker, confirme se o `API_BASE_URL` está configurado corretamente para o ambiente do container (ex: `host.docker.internal` ou o IP da máquina host).
* **Permissões:** Em ambientes Linux/Docker, certifique-se de que os arquivos e diretórios têm as permissões corretas para leitura e escrita pelo usuário que executa a aplicação.

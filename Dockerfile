FROM python:3.9-slim-buster

# Define o fuso horário para Brasil/São Paulo
# Isso é crucial para que o cron e o Python operem com a hora correta (1h do dia)
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instala dependências do sistema:
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    cron \
    locales \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Configura as localidades. Essencial para garantir que as datas sejam manipuladas corretamente
RUN locale-gen en_US.UTF-8 pt_BR.UTF-8
ENV LANG="en_US.UTF-8"
ENV LANGUAGE="en_US:en"
ENV LC_ALL="en_US.UTF-8"

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da sua aplicação para o diretório de trabalho no container
COPY . /app

# Adiciona o diretório do chromedriver ao PATH do sistema no container
ENV PATH="/usr/lib/chromium-browser/:${PATH}"

# Cria um diretório para os logs do cron dentro do container
RUN mkdir -p /var/log/cron

# Copia o script do cron job para o diretório de cron do sistema e define permissões
COPY scripts/daily_scrape.sh /etc/cron.d/daily_scrape
RUN chmod 0644 /etc/cron.d/daily_scrape
RUN crontab /etc/cron.d/daily_scrape

# Garante que o script Python diário seja executável
RUN chmod +x /app/src/daily_run.py

# Comando que será executado quando o container iniciar.
CMD cron -f
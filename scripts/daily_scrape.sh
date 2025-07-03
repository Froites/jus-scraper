#!/bin/bash

LOGFILE=/var/log/cron/daily_scrape.log

# Adiciona um cabeçalho ao log
echo "$(date): Starting daily scrape and API submission." >> $LOGFILE 2>&1

# Navega para o diretório 'src' da aplicação
cd /app/src/ || { echo "$(date): Failed to change directory to /app/src/" >> $LOGFILE 2>&1; exit 1; }


export PYTHONPATH=/app/src/:/app/

python daily_run.py >> $LOGFILE 2>&1

echo "$(date): Daily scrape and API submission finished." >> $LOGFILE 2>&1
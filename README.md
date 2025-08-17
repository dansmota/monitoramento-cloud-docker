# Monitoramento em Cloud com Docker, Zabbix, Grafana e Automação em Python

Este projeto cria um **laboratório DevOps completo** utilizando Docker Compose com os seguintes serviços:
- **Postgres**: Banco de dados do Zabbix
- **Zabbix Server**: Coleta e monitora métricas
- **Zabbix Web**: Interface gráfica para configuração
- **Grafana**: Dashboards de visualização
- **Monitor (Python)**: Script que consome a API do Zabbix e envia alertas para o Telegram

## 🚀 Como Executar

1. Clone o repositório:
```bash
git clone https://github.com/SEU_USUARIO/monitoramento-cloud-docker.git
cd monitoramento-cloud-docker
```

2. Configure as variáveis de ambiente no `docker-compose.yml`:
- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`

3. Suba o ambiente:
```bash
docker-compose up -d --build
```

4. Acesse os serviços:
- Zabbix Web: [http://localhost:8080](http://localhost:8080)
- Grafana: [http://localhost:3000](http://localhost:3000)

## 📂 Estrutura
```
monitoramento-cloud-docker/
│── docker-compose.yml
│── monitor/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── monitor.py
│── prints/
│── README.md
```

## 🖼 Prints
Coloque aqui screenshots do Grafana, Zabbix e dos alertas recebidos no Telegram.

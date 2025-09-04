import requests
import os
import time
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações
ZABBIX_URL = os.getenv("ZABBIX_URL", "http://zabbix-web:8080/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "Admin")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "zabbix")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))  # 5 minutos
STARTUP_DELAY = int(os.getenv("STARTUP_DELAY", "60"))  # 1 minuto

class ZabbixMonitor:
    def __init__(self):
        self.auth_token = None
        self.last_event_id = None
        
    def wait_for_zabbix(self):
        """Aguarda o Zabbix estar disponível"""
        logger.info("Aguardando Zabbix estar disponível...")
        max_attempts = 30
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(ZABBIX_URL.replace('/api_jsonrpc.php', ''), timeout=10)
                if response.status_code == 200:
                    logger.info("Zabbix está disponível!")
                    return True
            except Exception as e:
                logger.warning(f"Tentativa {attempt + 1}/{max_attempts}: {e}")
                time.sleep(10)
        
        logger.error("Zabbix não ficou disponível após todas as tentativas")
        return False
    
    def authenticate(self):
        """Autentica no Zabbix"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "username": ZABBIX_USER,
                    "password": ZABBIX_PASSWORD
                },
                "id": 1
            }
            
            response = requests.post(ZABBIX_URL, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                logger.error(f"Erro na autenticação: {result['error']}")
                return False
                
            self.auth_token = result.get('result')
            if self.auth_token:
                logger.info("Autenticação no Zabbix realizada com sucesso")
                return True
            else:
                logger.error("Token de autenticação não recebido")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao autenticar no Zabbix: {e}")
            return False
    
    def get_recent_events(self):
        """Obtém eventos recentes do Zabbix usando problem.get"""
        if not self.auth_token:
            if not self.authenticate():
                return []
        
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "problem.get",
                "params": {
                    "output": "extend",
                    "selectAcknowledges": "extend",
                    "selectTags": "extend",
                    "selectSuppressionData": "extend",
                    "sortfield": ["eventid"],
                    "sortorder": "DESC",
                    "limit": 10
                },
                "auth": self.auth_token,
                "id": 2
            }
            
            response = requests.post(ZABBIX_URL, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                logger.error(f"Erro ao obter eventos: {result['error']}")
                # Token pode ter expirado, tentar reautenticar
                self.auth_token = None
                return []
            
            events = result.get('result', [])
            logger.info(f"Encontrados {len(events)} eventos")
            return events
            
        except Exception as e:
            logger.error(f"Erro ao obter eventos do Zabbix: {e}")
            return []
    
    def send_telegram_message(self, message):
        """Envia mensagem para o Telegram"""
        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            logger.warning("Token ou Chat ID do Telegram não configurados")
            logger.warning(f"Token: {'Configurado' if TELEGRAM_TOKEN else 'Não configurado'}")
            logger.warning(f"Chat ID: {'Configurado' if TELEGRAM_CHAT_ID else 'Não configurado'}")
            return False
        
        # Verificar se a mensagem não está vazia
        if not message or len(message.strip()) < 10:
            logger.error("Mensagem vazia ou muito curta para enviar")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            params = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            
            logger.info(f"Enviando para Telegram. Tamanho da mensagem: {len(message)} caracteres")
            logger.debug(f"URL: {url}")
            logger.debug(f"Chat ID: {TELEGRAM_CHAT_ID}")
            
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                logger.info("Mensagem enviada para o Telegram com sucesso")
                return True
            else:
                logger.error(f"Erro do Telegram: {result.get('description')}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para o Telegram: {e}")
            # Log detalhado
            try:
                if hasattr(e, 'response') and e.response:
                    logger.error(f"Resposta de erro: {e.response.text}")
            except:
                pass
            return False
    
    def format_event_message(self, events):
        """Formatar mensagem de eventos"""
        if not events:
            logger.warning("Nenhum evento para formatar")
            return None
        
        priority_emoji = {
            '0': '📘',  # Not classified
            '1': '📗',  # Information  
            '2': '📙',  # Warning
            '3': '📙',  # Average
            '4': '📕',  # High
            '5': '🚨'   # Disaster
        }
        
        priority_names = {
            '0': 'Não classificado',
            '1': 'Informação',
            '2': 'Aviso', 
            '3': 'Médio',
            '4': 'Alto',
            '5': 'Desastre'
        }
        
        message = f"🚨 <b>ALERTAS ZABBIX</b> 🚨\n"
        message += f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        
        for event in events:
            # Extrair informações do problema
            name = event.get('name', 'Descrição não disponível')
            severity = event.get('severity', '0')
            emoji = priority_emoji.get(severity, '📘')
            priority_text = priority_names.get(severity, 'Desconhecida')
            
            # Obter hostname
            host = 'Desconhecido'
            hosts = event.get('hosts')
            if hosts and isinstance(hosts, list) and len(hosts) > 0:
                host = hosts[0].get('host', 'Desconhecido')
            elif 'host' in event:
                host = event['host']
            
            # Converter timestamp
            clock = int(event.get('clock', 0))
            event_time = datetime.fromtimestamp(clock).strftime('%d/%m/%Y %H:%M:%S')
            
            message += f"{emoji} <b>{host}</b> ({priority_text})\n"
            message += f"📝 {name}\n"
            message += f"🕐 {event_time}\n"
            message += f"🆔 {event.get('eventid', 'N/A')}\n\n"
        
        if len(message.strip()) <= 50:  # Se a mensagem estiver muito curta
            logger.warning("Mensagem formatada parece muito curta")
            return None
        
        return message
    
    def process_new_events(self, events):
        """Processa apenas eventos novos"""
        if not events:
            return []
        
        new_events = []
        
        # Encontrar o evento mais recente
        if events:
            latest_event_id = int(events[0].get('eventid', 0))
        else:
            latest_event_id = 0
        
        # Na primeira execução, definir o último ID sem enviar alertas
        if self.last_event_id is None:
            self.last_event_id = latest_event_id
            logger.info(f"Primeiro check - definindo último evento ID: {self.last_event_id}")
            return []
        
        # Filtrar apenas eventos mais recentes que o último processado
        for event in events:
            event_id = int(event.get('eventid', 0))
            if event_id > self.last_event_id:
                new_events.append(event)
        
        if new_events:
            self.last_event_id = latest_event_id
            logger.info(f"Encontrados {len(new_events)} eventos novos")
        
        return new_events
    
    def run(self):
        """Loop principal do monitor"""
        logger.info("Iniciando Monitor de Alertas Zabbix")
        
        # Delay inicial
        logger.info(f"Aguardando {STARTUP_DELAY} segundos antes de iniciar...")
        time.sleep(STARTUP_DELAY)
        
        # Aguardar Zabbix estar disponível
        if not self.wait_for_zabbix():
            logger.error("Não foi possível conectar ao Zabbix. Encerrando.")
            return
        
        # Autenticação inicial
        if not self.authenticate():
            logger.error("Falha na autenticação inicial. Encerrando.")
            return
        
        logger.info(f"Monitor iniciado. Verificando eventos a cada {CHECK_INTERVAL} segundos...")
        
        while True:
            try:
                # Obter eventos
                events = self.get_recent_events()
                
                # Processar apenas eventos novos
                new_events = self.process_new_events(events)
                
                if new_events:
                    message = self.format_event_message(new_events)
                    if message:
                        logger.info(f"Mensagem formatada: {len(message)} caracteres")
                        self.send_telegram_message(message)
                    else:
                        logger.warning("Mensagem formatada está vazia")
                else:
                    logger.info("Nenhum evento novo encontrado")
                
                # Aguardar próxima verificação
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Monitor interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"Erro inesperado: {e}")
                logger.info(f"Aguardando {CHECK_INTERVAL} segundos antes de continuar...")
                time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor = ZabbixMonitor()
    monitor.run()

"""
Integração com Evolution API para WhatsApp
Sistema completo de integração WhatsApp com Anna Agent
"""

import requests
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from anna_agent import create_anna_agent

class EvolutionAPIClient:
    """Cliente para interação com Evolution API v2"""
    
    def __init__(self, base_url: str, api_key: str, instance_name: str = "anna_bot"):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.instance_name = instance_name
        self.headers = {
            'apikey': api_key,
            'Content-Type': 'application/json'
        }
        
    def create_instance(self) -> Dict[str, Any]:
        """Cria uma nova instância WhatsApp"""
        url = f"{self.base_url}/instance/create"
        payload = {
            "instanceName": self.instance_name,
            "integration": "WHATSAPP-BAILEYS",
            "settings": {
                "rejectCall": True,
                "msgRetryCounterCache": True,
                "userAgent": "Evolution API Anna Bot",
                "markMessagesRead": True
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            logging.info(f"Instância {self.instance_name} criada com sucesso")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao criar instância: {e}")
            raise
    
    def get_instance_info(self) -> Dict[str, Any]:
        """Obtém informações da instância"""
        url = f"{self.base_url}/instance/fetchInstances"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao obter informações da instância: {e}")
            raise
    
    def get_qr_code(self) -> Dict[str, Any]:
        """Obtém o QR Code para conexão"""
        url = f"{self.base_url}/instance/connect/{self.instance_name}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao obter QR Code: {e}")
            raise
    
    def check_connection_status(self) -> Dict[str, Any]:
        """Verifica status da conexão"""
        url = f"{self.base_url}/instance/connectionState/{self.instance_name}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao verificar status da conexão: {e}")
            raise
    
    def send_text_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Envia mensagem de texto"""
        url = f"{self.base_url}/message/sendText/{self.instance_name}"
        
        # Formatar número para padrão internacional
        if not phone_number.startswith('+'):
            phone_number = f"+55{phone_number}" # Assume Brasil por padrão
        
        # Remover caracteres especiais e manter apenas números
        clean_number = ''.join(filter(str.isdigit, phone_number))
        formatted_number = f"{clean_number}@s.whatsapp.net"
        
        payload = {
            "number": formatted_number,
            "text": message
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            logging.info(f"Mensagem enviada para {phone_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar mensagem: {e}")
            raise
    
    def send_media_message(self, phone_number: str, media_url: str, caption: str = "") -> Dict[str, Any]:
        """Envia mensagem com mídia"""
        url = f"{self.base_url}/message/sendMedia/{self.instance_name}"
        
        clean_number = ''.join(filter(str.isdigit, phone_number))
        formatted_number = f"{clean_number}@s.whatsapp.net"
        
        payload = {
            "number": formatted_number,
            "mediaMessage": {
                "media": media_url,
                "caption": caption
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            logging.info(f"Mídia enviada para {phone_number}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar mídia: {e}")
            raise
    
    def setup_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Configura webhook para receber eventos"""
        url = f"{self.base_url}/webhook/set/{self.instance_name}"
        
        payload = {
            "url": webhook_url,
            "webhook_by_events": False,
            "webhook_base64": False,
            "events": [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE", 
                "SEND_MESSAGE",
                "CONNECTION_UPDATE",
                "QRCODE_UPDATED"
            ]
        }
        
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            logging.info(f"Webhook configurado: {webhook_url}")
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao configurar webhook: {e}")
            raise

class WhatsAppMessageProcessor:
    """Processador de mensagens WhatsApp com Anna Agent"""
    
    def __init__(self, evolution_client: EvolutionAPIClient):
        self.evolution_client = evolution_client
        self.anna_agent = None
        self.initialize_anna()
    
    def initialize_anna(self):
        """Inicializa o agente Anna"""
        try:
            self.anna_agent = create_anna_agent()
            logging.info("Anna agent inicializada para WhatsApp")
        except Exception as e:
            logging.error(f"Erro ao inicializar Anna: {e}")
    
    def process_incoming_message(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """Processa mensagem recebida via webhook"""
        try:
            event_type = webhook_data.get('event')
            
            if event_type != 'messages.upsert':
                return None
            
            data = webhook_data.get('data', {})
            messages = data.get('messages', [])
            
            for message in messages:
                # Ignorar mensagens próprias
                if message.get('key', {}).get('fromMe'):
                    continue
                
                phone_number = self.extract_phone_number(message)
                message_text = self.extract_message_text(message)
                
                if not message_text or not phone_number:
                    continue
                
                # Processar com Anna
                response = self.get_anna_response(message_text, phone_number)
                
                if response:
                    # Enviar resposta
                    self.evolution_client.send_text_message(phone_number, response)
                    
                    # Salvar conversa
                    self.save_conversation(phone_number, message_text, response)
                
                return response
                
        except Exception as e:
            logging.error(f"Erro ao processar mensagem: {e}")
            return None
    
    def extract_phone_number(self, message: Dict[str, Any]) -> Optional[str]:
        """Extrai número de telefone da mensagem"""
        try:
            remote_jid = message.get('key', {}).get('remoteJid', '')
            if '@s.whatsapp.net' in remote_jid:
                return remote_jid.replace('@s.whatsapp.net', '')
            return None
        except Exception as e:
            logging.error(f"Erro ao extrair número: {e}")
            return None
    
    def extract_message_text(self, message: Dict[str, Any]) -> Optional[str]:
        """Extrai texto da mensagem"""
        try:
            message_content = message.get('message', {})
            
            # Mensagem de texto
            if 'conversation' in message_content:
                return message_content['conversation']
            
            # Mensagem de texto estendida
            if 'extendedTextMessage' in message_content:
                return message_content['extendedTextMessage'].get('text', '')
            
            # Mensagem com mídia e caption
            if 'imageMessage' in message_content:
                return message_content['imageMessage'].get('caption', '')
            
            if 'videoMessage' in message_content:
                return message_content['videoMessage'].get('caption', '')
            
            return None
        except Exception as e:
            logging.error(f"Erro ao extrair texto: {e}")
            return None
    
    def get_anna_response(self, message: str, phone_number: str) -> Optional[str]:
        """Obtém resposta da Anna para a mensagem"""
        try:
            if not self.anna_agent:
                self.initialize_anna()
            
            if not self.anna_agent:
                return "Desculpe, estou com problemas técnicos no momento. Tente novamente em alguns minutos."
            
            # Adicionar contexto do WhatsApp
            contextual_message = f"[WhatsApp - {phone_number}] {message}"
            
            # Processar com Anna usando o método correto
            import asyncio
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            
            # Executar agent de forma assíncrona
            async def run_agent():
                session_service = InMemorySessionService()
                session = await session_service.create_session(
                    app_name="whatsapp_anna", 
                    user_id=phone_number, 
                    session_id=f"whatsapp_{phone_number}"
                )
                
                runner = Runner(agent=self.anna_agent, session=session)
                response = await runner.run(contextual_message)
                return response.get('response', 'Não consegui processar sua mensagem.')
            
            # Executar de forma síncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(run_agent())
            finally:
                loop.close()
            
            # Limitar tamanho da resposta (WhatsApp tem limite)
            if response and len(response) > 4000:
                response = response[:3900] + "...\n\n(mensagem truncada)"
            
            return response or "Ops! Não consegui processar sua mensagem."
            
        except Exception as e:
            logging.error(f"Erro ao obter resposta da Anna: {e}")
            return "Ops! Tive um problema para processar sua mensagem. Pode tentar de novo?"
    
    def save_conversation(self, phone_number: str, user_message: str, anna_response: str):
        """Salva conversa no banco de dados"""
        try:
            from supabase_tools import supabase
            
            conversation_data = {
                'phone_number': phone_number,
                'user_message': user_message,
                'anna_response': anna_response,
                'created_at': datetime.utcnow().isoformat(),
                'platform': 'whatsapp'
            }
            
            supabase.table('whatsapp_conversations').insert(conversation_data).execute()
            logging.info(f"Conversa salva: {phone_number}")
            
        except Exception as e:
            logging.error(f"Erro ao salvar conversa: {e}")

class WhatsAppIntegrationManager:
    """Gerenciador principal da integração WhatsApp"""
    
    def __init__(self):
        self.evolution_client = None
        self.message_processor = None
        self.load_config()
    
    def load_config(self):
        """Carrega configuração da integração"""
        try:
            # Buscar configuração do arquivo ou variáveis de ambiente
            evolution_url = os.getenv('EVOLUTION_API_URL', '')
            evolution_key = os.getenv('EVOLUTION_API_KEY', '')
            instance_name = os.getenv('EVOLUTION_INSTANCE_NAME', 'anna_bot')
            
            if evolution_url and evolution_key:
                self.evolution_client = EvolutionAPIClient(
                    base_url=evolution_url,
                    api_key=evolution_key,
                    instance_name=instance_name
                )
                
                self.message_processor = WhatsAppMessageProcessor(self.evolution_client)
                logging.info("Integração WhatsApp configurada a partir de variáveis de ambiente.")
            else:
                logging.info("Variáveis de ambiente do WhatsApp não encontradas. A configuração pode ser feita pela UI.")
                
        except Exception as e:
            logging.error(f"Erro ao carregar configuração WhatsApp: {e}")
    
    def initialize_integration(self, evolution_url: str, evolution_key: str, 
                            instance_name: str = "anna_bot", webhook_url: str = None) -> Dict[str, Any]:
        """Inicializa a integração completa"""
        try:
            # Configurar cliente
            self.evolution_client = EvolutionAPIClient(evolution_url, evolution_key, instance_name)
            self.message_processor = WhatsAppMessageProcessor(self.evolution_client)
            
            result = {
                'status': 'success',
                'steps': []
            }
            
            # 1. Criar instância
            try:
                instance_result = self.evolution_client.create_instance()
                result['steps'].append({'step': 'create_instance', 'status': 'success', 'data': instance_result})
            except Exception as e:
                result['steps'].append({'step': 'create_instance', 'status': 'error', 'error': str(e)})
            
            # 2. Configurar webhook se fornecido
            if webhook_url:
                try:
                    webhook_result = self.evolution_client.setup_webhook(webhook_url)
                    result['steps'].append({'step': 'setup_webhook', 'status': 'success', 'data': webhook_result})
                except Exception as e:
                    result['steps'].append({'step': 'setup_webhook', 'status': 'error', 'error': str(e)})
            
            # 3. Obter QR Code
            try:
                qr_result = self.evolution_client.get_qr_code()
                result['steps'].append({'step': 'get_qr_code', 'status': 'success', 'data': qr_result})
                result['qr_code'] = qr_result.get('base64')
            except Exception as e:
                result['steps'].append({'step': 'get_qr_code', 'status': 'error', 'error': str(e)})
            
            return result
            
        except Exception as e:
            logging.error(f"Erro na inicialização da integração: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Verifica status da conexão"""
        if not self.evolution_client:
            return {'status': 'not_configured'}
        
        try:
            return self.evolution_client.check_connection_status()
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Envia mensagem via WhatsApp"""
        if not self.evolution_client:
            return {'status': 'error', 'error': 'WhatsApp not configured'}
        
        try:
            return self.evolution_client.send_text_message(phone_number, message)
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa webhook recebido"""
        if not self.message_processor:
            return {'status': 'error', 'error': 'Message processor not initialized'}
        
        try:
            response = self.message_processor.process_incoming_message(webhook_data)
            return {
                'status': 'success',
                'processed': True,
                'response_sent': response is not None,
                'response': response
            }
        except Exception as e:
            logging.error(f"Erro ao processar webhook: {e}")
            return {'status': 'error', 'error': str(e)}

# Instância global
whatsapp_manager = WhatsAppIntegrationManager()
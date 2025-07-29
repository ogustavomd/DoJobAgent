"""
Chat Session Manager - Sistema de gerenciamento de sessões de chat
Responsável por criar/gerenciar sessões e salvar mensagens automaticamente
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from supabase import create_client, Client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatSessionManager:
    def __init__(self):
        """Inicializa o gerenciador de sessões de chat"""
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Variáveis SUPABASE_URL e SUPABASE_KEY são necessárias")
            raise Exception("Configuração Supabase não encontrada")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("ChatSessionManager inicializado com sucesso")

    def get_or_create_session(self, contact_phone: str, contact_name: Optional[str] = None, 
                             channel: str = 'chat', contact_avatar: Optional[str] = None) -> int:
        """
        Busca uma sessão ativa ou cria uma nova para o contato
        """
        try:
            # Primeiro, busca uma sessão ativa existente
            response = self.supabase.table('chat_sessions').select('*').eq(
                'contact_phone', contact_phone
            ).eq('channel', channel).eq('status', 'active').limit(1).execute()
            
            if response.data:
                session_id = response.data[0]['id']
                logger.info(f"Sessão existente encontrada: {session_id} para {contact_phone} ({channel})")
                return session_id
            
            # Se não existe, cria uma nova sessão
            new_session = {
                'contact_phone': contact_phone,
                'contact_name': contact_name or contact_phone,
                'contact_avatar': contact_avatar,
                'channel': channel,
                'status': 'active'
            }
            
            response = self.supabase.table('chat_sessions').insert(new_session).execute()
            
            if response.data:
                session_id = response.data[0]['id']
                logger.info(f"Nova sessão criada: {session_id} para {contact_phone} ({channel})")
                return session_id
            else:
                logger.error("Erro ao criar nova sessão")
                raise Exception("Falha ao criar sessão")
                
        except Exception as e:
            logger.error(f"Erro ao buscar/criar sessão: {e}")
            raise

    def save_message(self, session_id: int, sender_phone: str, content: str, 
                    sender_name: Optional[str] = None, message_type: str = 'text', 
                    media_url: Optional[str] = None, is_from_bot: bool = False) -> bool:
        """
        Salva uma mensagem na sessão de chat
        """
        try:
            message_data = {
                'chat_session_id': session_id,
                'sender_phone': sender_phone,
                'sender_name': sender_name,
                'content': content,
                'message_type': message_type,
                'media_url': media_url,
                'is_from_bot': is_from_bot
            }
            
            response = self.supabase.table('messages').insert(message_data).execute()
            
            if response.data:
                # Atualiza o timestamp da sessão
                self.supabase.table('chat_sessions').update({
                    'updated_at': datetime.now().isoformat()
                }).eq('id', session_id).execute()
                
                logger.info(f"Mensagem salva para sessão {session_id}: {content[:50]}...")
                return True
            else:
                logger.error("Erro ao salvar mensagem")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
            return False

    def get_session_messages(self, session_id: int, limit: int = 50) -> List[Dict]:
        """
        Busca mensagens de uma sessão de chat
        """
        try:
            response = self.supabase.table('messages').select('*').eq(
                'chat_session_id', session_id
            ).order('created_at', desc=False).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens: {e}")
            return []

    def get_contact_sessions(self, contact_phone: str, channel: Optional[str] = None) -> List[Dict]:
        """
        Busca todas as sessões de um contato
        """
        try:
            query = self.supabase.table('chat_sessions').select('*').eq('contact_phone', contact_phone)
            
            if channel:
                query = query.eq('channel', channel)
                
            response = query.order('created_at', desc=True).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Erro ao buscar sessões do contato: {e}")
            return []

    def end_session(self, session_id: int) -> bool:
        """
        Finaliza uma sessão de chat
        """
        try:
            response = self.supabase.table('chat_sessions').update({
                'status': 'ended',
                'updated_at': datetime.now().isoformat()
            }).eq('id', session_id).execute()
            
            if response.data:
                logger.info(f"Sessão {session_id} finalizada")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao finalizar sessão: {e}")
            return False

    def get_active_sessions(self, limit: int = 50) -> List[Dict]:
        """
        Busca todas as sessões ativas
        """
        try:
            response = self.supabase.table('chat_sessions').select('*').eq(
                'status', 'active'
            ).order('updated_at', desc=True).limit(limit).execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Erro ao buscar sessões ativas: {e}")
            return []

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas das sessões
        """
        try:
            # Total de sessões
            total_response = self.supabase.table('chat_sessions').select('*').execute()
            total_sessions = len(total_response.data) if total_response.data else 0
            
            # Sessões ativas
            active_response = self.supabase.table('chat_sessions').select('*').eq('status', 'active').execute()
            active_sessions = len(active_response.data) if active_response.data else 0
            
            # Por canal
            whatsapp_response = self.supabase.table('chat_sessions').select('*').eq('channel', 'whatsapp').execute()
            whatsapp_sessions = len(whatsapp_response.data) if whatsapp_response.data else 0
            
            chat_response = self.supabase.table('chat_sessions').select('*').eq('channel', 'chat').execute()
            chat_sessions = len(chat_response.data) if chat_response.data else 0
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'whatsapp_sessions': whatsapp_sessions,
                'chat_sessions': chat_sessions
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {}

# Instância global para usar na aplicação
chat_session_manager = ChatSessionManager()
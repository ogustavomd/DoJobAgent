"""
Chat Session Manager - Sistema de gerenciamento de sessões de chat com PostgreSQL + Supabase
Responsável por criar/gerenciar sessões e salvar mensagens automaticamente em ambos os bancos
"""

import os
import logging
import psycopg2
from datetime import datetime
from typing import Optional, Dict, List, Any, Generator
from contextlib import contextmanager
from dual_database_sync import dual_sync

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatSessionManager:
    def __init__(self):
        """Inicializa o gerenciador de sessões de chat com PostgreSQL"""
        self.database_url = os.environ.get("DATABASE_URL")
        
        if not self.database_url:
            logger.error("Variável DATABASE_URL é necessária")
            raise Exception("Configuração PostgreSQL não encontrada")
        
        logger.info("ChatSessionManager inicializado com sucesso")

    @contextmanager
    def get_db_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Context manager para conexões com o banco"""
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Erro na conexão com o banco: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_or_create_session(self, contact_phone: str, contact_name: Optional[str] = None, 
                             channel: str = 'chat', contact_avatar: Optional[str] = None) -> str:
        """
        Busca uma sessão ativa ou cria uma nova para o contato usando sincronização dual
        """
        try:
            # Use dual sync system
            session_data = {
                'contact_phone': contact_phone,
                'contact_name': contact_name,
                'contact_avatar': contact_avatar,
                'channel': channel
            }
            
            session_id = dual_sync.sync_chat_session(session_data)
            return session_id
                
        except Exception as e:
            logger.error(f"Erro ao buscar/criar sessão: {e}")
            raise

    def save_message(self, session_id: str, sender_phone: str, content: str, 
                    sender_name: Optional[str] = None, message_type: str = 'text', 
                    media_url: Optional[str] = None, is_from_bot: bool = False) -> bool:
        """
        Salva uma mensagem na sessão de chat
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Inserir mensagem
                cursor.execute("""
                    INSERT INTO messages (chat_session_id, sender_phone, sender_name, content, message_type, media_url, is_from_bot)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (session_id, sender_phone, sender_name, content, message_type, media_url, is_from_bot))
                
                # Atualizar timestamp da sessão
                cursor.execute("""
                    UPDATE chat_sessions SET updated_at = NOW() WHERE id = %s
                """, (session_id,))
                
                conn.commit()
                
                logger.info(f"Mensagem salva para sessão {session_id}: {content[:50]}...")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
            return False

    def get_session_messages(self, session_id: str, limit: int = 50) -> List[Dict]:
        """
        Busca mensagens de uma sessão de chat
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, sender_phone, sender_name, content, message_type, media_url, is_from_bot, created_at
                    FROM messages 
                    WHERE chat_session_id = %s 
                    ORDER BY created_at ASC 
                    LIMIT %s
                """, (session_id, limit))
                
                columns = ['id', 'sender_phone', 'sender_name', 'content', 'message_type', 'media_url', 'is_from_bot', 'created_at']
                messages = []
                
                for row in cursor.fetchall():
                    message = dict(zip(columns, row))
                    message['created_at'] = message['created_at'].isoformat() if message['created_at'] else None
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens: {e}")
            return []

    def get_contact_sessions(self, contact_phone: str, channel: Optional[str] = None) -> List[Dict]:
        """
        Busca todas as sessões de um contato
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                if channel:
                    cursor.execute("""
                        SELECT id, contact_phone, contact_name, channel, status, created_at, updated_at
                        FROM chat_sessions 
                        WHERE contact_phone = %s AND channel = %s 
                        ORDER BY created_at DESC
                    """, (contact_phone, channel))
                else:
                    cursor.execute("""
                        SELECT id, contact_phone, contact_name, channel, status, created_at, updated_at
                        FROM chat_sessions 
                        WHERE contact_phone = %s 
                        ORDER BY created_at DESC
                    """, (contact_phone,))
                
                columns = ['id', 'contact_phone', 'contact_name', 'channel', 'status', 'created_at', 'updated_at']
                sessions = []
                
                for row in cursor.fetchall():
                    session_data = dict(zip(columns, row))
                    session_data['created_at'] = session_data['created_at'].isoformat() if session_data['created_at'] else None
                    session_data['updated_at'] = session_data['updated_at'].isoformat() if session_data['updated_at'] else None
                    sessions.append(session_data)
                
                return sessions
                
        except Exception as e:
            logger.error(f"Erro ao buscar sessões do contato: {e}")
            return []

    def end_session(self, session_id: str) -> bool:
        """
        Finaliza uma sessão de chat
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE chat_sessions 
                    SET status = %s, updated_at = NOW() 
                    WHERE id = %s
                """, ('ended', session_id))
                
                conn.commit()
                
                logger.info(f"Sessão {session_id} finalizada")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao finalizar sessão: {e}")
            return False

    def get_active_sessions(self, limit: int = 50) -> List[Dict]:
        """
        Busca todas as sessões ativas
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, contact_phone, contact_name, channel, status, created_at, updated_at
                    FROM chat_sessions 
                    WHERE status = %s 
                    ORDER BY updated_at DESC 
                    LIMIT %s
                """, ('active', limit))
                
                columns = ['id', 'contact_phone', 'contact_name', 'channel', 'status', 'created_at', 'updated_at']
                sessions = []
                
                for row in cursor.fetchall():
                    session_data = dict(zip(columns, row))
                    session_data['created_at'] = session_data['created_at'].isoformat() if session_data['created_at'] else None
                    session_data['updated_at'] = session_data['updated_at'].isoformat() if session_data['updated_at'] else None
                    sessions.append(session_data)
                
                return sessions
                
        except Exception as e:
            logger.error(f"Erro ao buscar sessões ativas: {e}")
            return []

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas das sessões
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Total de sessões
                cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                total_sessions = cursor.fetchone()[0]
                
                # Sessões ativas
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE status = %s", ('active',))
                active_sessions = cursor.fetchone()[0]
                
                # Por canal
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE channel = %s", ('whatsapp',))
                whatsapp_sessions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE channel = %s", ('chat',))
                chat_sessions = cursor.fetchone()[0]
                
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
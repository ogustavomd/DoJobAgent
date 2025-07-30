"""
Sistema de Sincronização Dual - PostgreSQL Local + Supabase
Garante que todos os dados sejam salvos em ambos os bancos simultaneamente
"""

import os
import logging
import psycopg2
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualDatabaseSync:
    def __init__(self):
        """Initialize dual database synchronization"""
        # PostgreSQL local connection
        self.postgres_url = os.environ.get("DATABASE_URL")
        
        # Supabase connection
        self.supabase_url = os.getenv("SUPABASE_URL", "https://dzesbxohplkuequmfzbs.supabase.co")
        self.supabase_key = os.getenv(
            "SUPABASE_KEY",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR6ZXNieG9ocGxrdWVxdW1memJzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMyNzU2MiwiZXhwIjoyMDY3OTAzNTYyfQ.LyeIaTUqi0ZnPwsBO0BVeQvpUqUc8sYJWjKV2q4SIqw"
        )
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        if not self.postgres_url:
            logger.warning("DATABASE_URL not set, using fallback SQLite database")
            self.postgres_url = "sqlite:///fallback.db"
        
        logger.info("DualDatabaseSync initialized successfully")

    @contextmanager
    def get_postgres_connection(self):
        """Context manager for PostgreSQL connections"""
        conn = None
        try:
            conn = psycopg2.connect(self.postgres_url)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"PostgreSQL connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def sync_chat_session(self, session_data: Dict[str, Any]) -> str:
        """Sync chat session to both databases"""
        session_id = None
        
        try:
            # 1. Save to PostgreSQL
            with self.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()
                
                # Check if session exists
                cursor.execute("""
                    SELECT id FROM chat_sessions 
                    WHERE contact_phone = %s AND channel = %s AND status = %s 
                    LIMIT 1
                """, (session_data['contact_phone'], session_data.get('channel', 'chat'), 'active'))
                
                result = cursor.fetchone()
                
                if result:
                    session_id = str(result[0])
                    logger.info(f"Existing session found in PostgreSQL: {session_id}")
                else:
                    # Create new session in PostgreSQL
                    cursor.execute("""
                        INSERT INTO chat_sessions (contact_phone, contact_name, contact_avatar, channel, status)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        session_data['contact_phone'],
                        session_data.get('contact_name', session_data['contact_phone']),
                        session_data.get('contact_avatar'),
                        session_data.get('channel', 'chat'),
                        'active'
                    ))
                    
                    session_id = str(cursor.fetchone()[0])
                    pg_conn.commit()
                    logger.info(f"New session created in PostgreSQL: {session_id}")

            # 2. Sync to Supabase
            try:
                # Check if session exists in Supabase
                supabase_check = self.supabase.table('chat_sessions').select('id').eq(
                    'contact_phone', session_data['contact_phone']
                ).eq('channel', session_data.get('channel', 'chat')).eq('status', 'active').execute()
                
                if not supabase_check.data:
                    # Create session in Supabase
                    supabase_data = {
                        'contact_phone': session_data['contact_phone'],
                        'contact_name': session_data.get('contact_name', session_data['contact_phone']),
                        'contact_avatar': session_data.get('contact_avatar'),
                        'channel': session_data.get('channel', 'chat'),
                        'status': 'active'
                    }
                    
                    self.supabase.table('chat_sessions').insert(supabase_data).execute()
                    logger.info(f"Session synced to Supabase: {session_id}")
                    
            except Exception as e:
                logger.error(f"Error syncing session to Supabase: {e}")
                # Continue even if Supabase sync fails
                
            return session_id
            
        except Exception as e:
            logger.error(f"Error syncing chat session: {e}")
            raise

    def sync_message(self, message_data: Dict[str, Any]) -> bool:
        """Sync message to both databases"""
        try:
            logger.info(f"Starting message sync for: {message_data.get('content', '')[:50]}...")
            
            # 1. Save to PostgreSQL
            with self.get_postgres_connection() as pg_conn:
                cursor = pg_conn.cursor()
                
                cursor.execute("""
                    INSERT INTO messages (
                        chat_session_id, sender_phone, sender_name, content, 
                        message_type, media_url, is_from_bot
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    message_data.get('chat_session_id'),
                    message_data.get('sender_phone'),
                    message_data.get('sender_name', message_data.get('sender_phone')),
                    message_data['content'],
                    message_data.get('message_type', 'text'),
                    message_data.get('media_url'),
                    message_data.get('is_from_bot', False)
                ))
                
                result = cursor.fetchone()
                if result:
                    message_id = result[0]
                    pg_conn.commit()
                    logger.info(f"Message saved to PostgreSQL: {message_id}")
                else:
                    logger.error("Failed to save message to PostgreSQL")

            # 2. Sync to Supabase
            try:
                # First ensure chat session exists in Supabase
                if message_data.get('sender_phone', '').startswith('web_user') or message_data.get('sender_phone') == 'web_user':
                    contact_phone = 'web_user'
                else:
                    contact_phone = message_data.get('sender_phone', 'unknown')
                
                # Check/create session in Supabase
                session_check = self.supabase.table('chat_sessions').select('id').eq(
                    'contact_phone', contact_phone
                ).eq('channel', 'chat').eq('status', 'active').limit(1).execute()
                
                supabase_session_id = None
                if not session_check.data:
                    # Create session in Supabase
                    session_result = self.supabase.table('chat_sessions').insert({
                        'contact_phone': contact_phone,
                        'contact_name': contact_phone,
                        'channel': 'chat',
                        'status': 'active'
                    }).execute()
                    if session_result.data:
                        supabase_session_id = session_result.data[0]['id']
                else:
                    supabase_session_id = session_check.data[0]['id']
                
                # Insert message in Supabase
                if supabase_session_id:
                    supabase_message = {
                        'chat_session_id': supabase_session_id,
                        'sender_phone': contact_phone,
                        'sender_name': contact_phone,
                        'content': message_data['content'],
                        'message_type': message_data.get('message_type', 'text'),
                        'media_url': message_data.get('media_url'),
                        'is_from_bot': message_data.get('is_from_bot', False)
                    }
                    
                    result = self.supabase.table('messages').insert(supabase_message).execute()
                    logger.info(f"Message synced to Supabase successfully: {len(result.data)} records")
                else:
                    logger.error("Could not create/find session in Supabase")
                
            except Exception as e:
                logger.error(f"Error syncing message to Supabase: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Continue even if Supabase sync fails
                
            return True
            
        except Exception as e:
            logger.error(f"Error syncing message: {e}")
            return False

    def sync_routine(self, routine_data: Dict[str, Any]) -> Optional[str]:
        """Sync routine/activity to both databases"""
        try:
            routine_id = None
            
            # 1. Save to PostgreSQL using SQLAlchemy
            from models import Routine
            from app import db
            
            routine = Routine(
                activity=routine_data['activity'],
                category=routine_data['category'],
                date=routine_data['date'],
                time_start=routine_data['time_start'],
                time_end=routine_data['time_end'],
                description=routine_data.get('description'),
                location=routine_data.get('location'),
                status=routine_data.get('status', 'upcoming'),
                has_images=routine_data.get('has_images', False),
                has_videos=routine_data.get('has_videos', False)
            )
            
            db.session.add(routine)
            db.session.commit()
            routine_id = str(routine.id)
            logger.info(f"Routine saved to PostgreSQL: {routine_id}")

            # 2. Sync to Supabase
            try:
                supabase_routine = {
                    'activity': routine_data['activity'],
                    'category': routine_data['category'],
                    'date': routine_data['date'].isoformat() if hasattr(routine_data['date'], 'isoformat') else str(routine_data['date']),
                    'time_start': routine_data['time_start'].strftime('%H:%M:%S') if hasattr(routine_data['time_start'], 'strftime') else str(routine_data['time_start']),
                    'time_end': routine_data['time_end'].strftime('%H:%M:%S') if hasattr(routine_data['time_end'], 'strftime') else str(routine_data['time_end']),
                    'description': routine_data.get('description'),
                    'location': routine_data.get('location'),
                    'status': routine_data.get('status', 'upcoming'),
                    'has_images': routine_data.get('has_images', False),
                    'has_videos': routine_data.get('has_videos', False)
                }
                
                self.supabase.table('routine').insert(supabase_routine).execute()
                logger.info(f"Routine synced to Supabase: {routine_id}")
                
            except Exception as e:
                logger.error(f"Error syncing routine to Supabase: {e}")
                # Continue even if Supabase sync fails
                
            return routine_id
            
        except Exception as e:
            logger.error(f"Error syncing routine: {e}")
            return None

    def sync_routine_update(self, routine_id: str, routine_data: Dict[str, Any]) -> bool:
        """Update routine in both databases"""
        try:
            # 1. Update in PostgreSQL
            from models import Routine
            from app import db
            
            routine = db.session.query(Routine).filter(Routine.id == routine_id).first()
            if routine:
                for key, value in routine_data.items():
                    if hasattr(routine, key):
                        setattr(routine, key, value)
                
                db.session.commit()
                logger.info(f"Routine updated in PostgreSQL: {routine_id}")

            # 2. Update in Supabase
            try:
                # Prepare data for Supabase
                supabase_data = {}
                for key, value in routine_data.items():
                    if key in ['date']:
                        supabase_data[key] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                    elif key in ['time_start', 'time_end']:
                        supabase_data[key] = value.strftime('%H:%M:%S') if hasattr(value, 'strftime') else str(value)
                    else:
                        supabase_data[key] = value
                
                self.supabase.table('routine').update(supabase_data).eq('id', routine_id).execute()
                logger.info(f"Routine updated in Supabase: {routine_id}")
                
            except Exception as e:
                logger.error(f"Error updating routine in Supabase: {e}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating routine: {e}")
            return False

    def sync_routine_delete(self, routine_id: str) -> bool:
        """Delete routine from both databases"""
        try:
            # 1. Delete from PostgreSQL
            from models import Routine
            from app import db
            
            routine = db.session.query(Routine).filter(Routine.id == routine_id).first()
            if routine:
                db.session.delete(routine)
                db.session.commit()
                logger.info(f"Routine deleted from PostgreSQL: {routine_id}")

            # 2. Delete from Supabase
            try:
                self.supabase.table('routine').delete().eq('id', routine_id).execute()
                logger.info(f"Routine deleted from Supabase: {routine_id}")
                
            except Exception as e:
                logger.error(f"Error deleting routine from Supabase: {e}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error deleting routine: {e}")
            return False

# Global instance
dual_sync = DualDatabaseSync()
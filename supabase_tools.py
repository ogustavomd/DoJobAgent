import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://dzesbxohplkuequmfzbs.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR6ZXNieG9ocGxrdWVxdW1memJzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMyNzU2MiwiZXhwIjoyMDY3OTAzNTYyfQ.LyeIaTUqi0ZnPwsBO0BVeQvpUqUc8sYJWjKV2q4SIqw")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_anna_routines(days: int, activity_filter: Optional[str]) -> Dict[str, Any]:
    """
    Busca as atividades da rotina da Anna dos últimos dias.
    
    Args:
        days (int): Número de dias para buscar (use 7 como padrão)
        activity_filter (str): Filtro opcional por tipo de atividade (use None para não filtrar)
    
    Returns:
        Dict contendo as atividades encontradas
    """
    try:
        # Set defaults if not provided
        if days is None:
            days = 7
        
        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        current_time = datetime.now().time()
        
        query = supabase.table('anna_routine').select('*').gte('date', start_date.isoformat()).lte('date', end_date.isoformat()).order('date', desc=True).order('time_start', desc=False)
        
        if activity_filter:
            query = query.ilike('activity', f'%{activity_filter}%')
            
        response = query.execute()
        
        activities = response.data
        
        # Update status based on current time for today's activities
        today = datetime.now().date()
        for activity in activities:
            if activity['date'] == str(today):
                routine_start = datetime.strptime(activity['time_start'], '%H:%M:%S').time()
                routine_end = datetime.strptime(activity['time_end'], '%H:%M:%S').time()
                
                if current_time < routine_start:
                    activity['status'] = 'upcoming'
                elif routine_start <= current_time <= routine_end:
                    activity['status'] = 'current'
                else:
                    activity['status'] = 'completed'
        
        # Format the response
        formatted_activities = []
        for activity in activities:
            formatted_activities.append({
                'data': activity['date'],
                'horario': f"{activity['time_start']} - {activity['time_end']}",
                'atividade': activity['activity'],
                'categoria': activity['category'],
                'local': activity.get('location'),
                'descricao': activity.get('description'),
                'status': activity['status'],
                'tem_imagens': activity.get('has_images', False),
                'tem_videos': activity.get('has_videos', False),
                'id': activity['id']
            })
        
        return {
            'status': 'success',
            'total_atividades': len(formatted_activities),
            'periodo': f'{start_date.isoformat()} a {end_date.isoformat()}',
            'atividades': formatted_activities
        }
        
    except Exception as e:
        logging.error(f"Error fetching Anna's routines: {e}")
        return {
            'status': 'error',
            'message': f'Erro ao buscar rotinas: {str(e)}',
            'atividades': []
        }

def get_anna_routine_media(routine_id: Optional[str], media_type: Optional[str], limit: int) -> Dict[str, Any]:
    """
    Busca fotos e vídeos das atividades da Anna.
    
    Args:
        routine_id (str): ID específico da rotina (use None para todas)
        media_type (str): Tipo de mídia ('image' ou 'video', use None para todos)
        limit (int): Limite de resultados (use 10 como padrão)
    
    Returns:
        Dict contendo as mídias encontradas
    """
    try:
        # Set defaults if not provided
        if limit is None:
            limit = 10
        
        query = supabase.table('anna_routine_media').select('*, anna_routine(activity, date, time_start, category)')
        
        if routine_id:
            query = query.eq('routine_id', routine_id)
            
        if media_type:
            query = query.eq('media_type', media_type)
            
        response = query.order('created_at', desc=True).limit(limit).execute()
        
        media_items = response.data
        
        formatted_media = []
        for item in media_items:
            routine_info = item.get('anna_routine', {})
            formatted_media.append({
                'media_url': item['media_url'],
                'tipo': item['media_type'],
                'descricao': item.get('description'),
                'atividade': routine_info.get('activity'),
                'data': routine_info.get('date'),
                'horario': routine_info.get('time_start'),
                'categoria': routine_info.get('category'),
                'criado_em': item['created_at']
            })
        
        return {
            'status': 'success',
            'total_midias': len(formatted_media),
            'midias': formatted_media
        }
        
    except Exception as e:
        logging.error(f"Error fetching routine media: {e}")
        return {
            'status': 'error',
            'message': f'Erro ao buscar mídias: {str(e)}',
            'midias': []
        }

def search_memories(search_term: str, limit: int) -> Dict[str, Any]:
    """
    Busca nas memórias e conversas da Anna por termo específico.
    
    Args:
        search_term (str): Termo para buscar nas conversas
        limit (int): Limite de resultados (use 10 como padrão)
    
    Returns:
        Dict contendo as memórias encontradas
    """
    try:
        # Set defaults if not provided
        if limit is None:
            limit = 10
        
        # Search in messages content
        response = supabase.table('messages').select('*, chat_sessions(contact_name, contact_phone)').ilike('content', f'%{search_term}%').order('created_at', desc=True).limit(limit).execute()
        
        messages = response.data
        
        formatted_memories = []
        for message in messages:
            session_info = message.get('chat_sessions', {})
            formatted_memories.append({
                'conteudo': message['content'],
                'data': message['created_at'],
                'telefone_remetente': message['sender_phone'],
                'contato_nome': session_info.get('contact_name'),
                'tipo_mensagem': message.get('message_type'),
                'url_midia': message.get('media_url')
            })
        
        return {
            'status': 'success',
            'termo_busca': search_term,
            'total_memorias': len(formatted_memories),
            'memorias': formatted_memories
        }
        
    except Exception as e:
        logging.error(f"Error searching memories: {e}")
        return {
            'status': 'error',
            'message': f'Erro ao buscar memórias: {str(e)}',
            'memorias': []
        }

def get_recent_conversations(limit: int) -> Dict[str, Any]:
    """
    Busca as conversas recentes da Anna.
    
    Args:
        limit (int): Número de conversas recentes para buscar (use 5 como padrão)
    
    Returns:
        Dict contendo as conversas recentes
    """
    try:
        # Set defaults if not provided
        if limit is None:
            limit = 5
        
        # Get recent chat sessions with latest messages
        response = supabase.table('chat_sessions').select('*, messages(content, created_at, sender_phone, message_type)').order('updated_at', desc=True).limit(limit).execute()
        
        sessions = response.data
        
        formatted_conversations = []
        for session in sessions:
            messages = session.get('messages', [])
            # Get the most recent message
            latest_message = max(messages, key=lambda x: x['created_at']) if messages else None
            
            formatted_conversations.append({
                'contato_nome': session.get('contact_name'),
                'contato_telefone': session['contact_phone'],
                'avatar': session.get('contact_avatar'),
                'ultima_atualizacao': session['updated_at'],
                'ultima_mensagem': latest_message['content'] if latest_message else None,
                'data_ultima_mensagem': latest_message['created_at'] if latest_message else None,
                'total_mensagens': len(messages)
            })
        
        return {
            'status': 'success',
            'total_conversas': len(formatted_conversations),
            'conversas': formatted_conversations
        }
        
    except Exception as e:
        logging.error(f"Error fetching recent conversations: {e}")
        return {
            'status': 'error',
            'message': f'Erro ao buscar conversas: {str(e)}',
            'conversas': []
        }

def get_profile_info(phone_number: Optional[str]) -> Dict[str, Any]:
    """
    Busca informações de perfil.
    
    Args:
        phone_number (str): Número de telefone específico (opcional)
    
    Returns:
        Dict contendo informações do perfil
    """
    try:
        query = supabase.table('profiles').select('*')
        
        if phone_number:
            query = query.eq('phone_number', phone_number)
        
        response = query.execute()
        profiles = response.data
        
        formatted_profiles = []
        for profile in profiles:
            formatted_profiles.append({
                'nome': profile.get('name'),
                'telefone': profile['phone_number'],
                'avatar': profile.get('avatar_url'),
                'criado_em': profile['created_at'],
                'atualizado_em': profile['updated_at']
            })
        
        return {
            'status': 'success',
            'total_perfis': len(formatted_profiles),
            'perfis': formatted_profiles
        }
        
    except Exception as e:
        logging.error(f"Error fetching profile info: {e}")
        return {
            'status': 'error',
            'message': f'Erro ao buscar perfis: {str(e)}',
            'perfis': []
        }

def search_content(search_term: str, content_type: Optional[str], limit: int) -> Dict[str, Any]:
    """
    Busca conteúdo na biblioteca da Anna.
    
    Args:
        search_term (str): Termo para buscar
        content_type (str): Tipo de conteúdo específico (use None para todos)
        limit (int): Limite de resultados (use 10 como padrão)
    
    Returns:
        Dict contendo o conteúdo encontrado
    """
    try:
        # Set defaults if not provided
        if limit is None:
            limit = 10
        
        query = supabase.table('conteudo').select('*')
        
        # Search in title or description
        query = query.or_(f'titulo.ilike.%{search_term}%,descricao.ilike.%{search_term}%')
        
        if content_type:
            query = query.eq('tipo_conteudo', content_type)
        
        response = query.order('criado_em', desc=True).limit(limit).execute()
        
        content_items = response.data
        
        formatted_content = []
        for item in content_items:
            formatted_content.append({
                'titulo': item['titulo'],
                'descricao': item.get('descricao'),
                'tipo': item['tipo_conteudo'],
                'url': item['url'],
                'bucket': item['bucket'],
                'criado_em': item['criado_em'],
                'atualizado_em': item['atualizado_em']
            })
        
        return {
            'status': 'success',
            'termo_busca': search_term,
            'total_conteudo': len(formatted_content),
            'conteudo': formatted_content
        }
        
    except Exception as e:
        logging.error(f"Error searching content: {e}")
        return {
            'status': 'error',
            'message': f'Erro ao buscar conteúdo: {str(e)}',
            'conteudo': []
        }

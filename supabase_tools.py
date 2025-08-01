import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import create_client, Client

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL",
                         "https://dzesbxohplkuequmfzbs.supabase.co")
SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR6ZXNieG9ocGxrdWVxdW1memJzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MjMyNzU2MiwiZXhwIjoyMDY3OTAzNTYyfQ.LyeIaTUqi0ZnPwsBO0BVeQvpUqUc8sYJWjKV2q4SIqw"
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_routines(days: int,
                      activity_filter: Optional[str]) -> Dict[str, Any]:
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

        query = supabase.table('routine').select('*').gte(
            'date',
            start_date.isoformat()).lte('date', end_date.isoformat()).order(
                'date', desc=True).order('time_start', desc=False)

        if activity_filter:
            query = query.ilike('activity', f'%{activity_filter}%')

        response = query.execute()

        activities = response.data

        # Update status based on current time for today's activities
        today = datetime.now().date()
        for activity in activities:
            if activity['date'] == str(today):
                routine_start = datetime.strptime(activity['time_start'],
                                                  '%H:%M:%S').time()
                routine_end = datetime.strptime(activity['time_end'],
                                                '%H:%M:%S').time()

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
                'data':
                activity['date'],
                'horario':
                f"{activity['time_start']} - {activity['time_end']}",
                'atividade':
                activity['activity'],
                'categoria':
                activity['category'],
                'local':
                activity.get('location'),
                'descricao':
                activity.get('description'),
                'status':
                activity['status'],
                'tem_imagens':
                activity.get('has_images', False),
                'tem_videos':
                activity.get('has_videos', False),
                'id':
                activity['id']
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


def get_routine_media(routine_id: Optional[str],
                           media_type: Optional[str],
                           limit: int) -> Dict[str, Any]:
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

        query = supabase.table('routine_media').select(
            '*, routine(activity, date, time_start, category)')

        if routine_id:
            query = query.eq('routine_id', routine_id)

        if media_type:
            query = query.eq('media_type', media_type)

        response = query.order('created_at', desc=True).limit(limit).execute()

        media_items = response.data

        formatted_media = []
        for item in media_items:
            routine_info = item.get('routine', {})
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
        response = supabase.table('messages').select(
            '*, chat_sessions(contact_name, contact_phone)').ilike(
                'content',
                f'%{search_term}%').order('created_at',
                                          desc=True).limit(limit).execute()

        messages = response.data

        formatted_memories = []
        for message in messages:
            session_info = message.get('chat_sessions', {})
            formatted_memories.append({
                'conteudo':
                message['content'],
                'data':
                message['created_at'],
                'telefone_remetente':
                message['sender_phone'],
                'contato_nome':
                session_info.get('contact_name'),
                'tipo_mensagem':
                message.get('message_type'),
                'url_midia':
                message.get('media_url')
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
        response = supabase.table('chat_sessions').select(
            '*, messages(content, created_at, sender_phone, message_type)'
        ).order('updated_at', desc=True).limit(limit).execute()

        sessions = response.data

        formatted_conversations = []
        for session in sessions:
            messages = session.get('messages', [])
            # Get the most recent message
            latest_message = max(
                messages, key=lambda x: x['created_at']) if messages else None

            formatted_conversations.append({
                'contato_nome':
                session.get('contact_name'),
                'contato_telefone':
                session['contact_phone'],
                'avatar':
                session.get('contact_avatar'),
                'ultima_atualizacao':
                session['updated_at'],
                'ultima_mensagem':
                latest_message['content'] if latest_message else None,
                'data_ultima_mensagem':
                latest_message['created_at'] if latest_message else None,
                'total_mensagens':
                len(messages)
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


def search_content(search_term: str, content_type: Optional[str],
                   limit: int) -> Dict[str, Any]:
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
        query = query.or_(
            f'titulo.ilike.%{search_term}%,descricao.ilike.%{search_term}%')

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


def get_agent_config() -> dict:
    """
    Get the agent configuration from the agent_config table.
    Fetches the first active configuration found.
    """
    try:
        result = supabase.table('agent_config').select("*").eq('is_active', True).limit(1).execute()
        
        if result.data:
            config_data = result.data[0]
            logging.info(f"Configuration loaded from agent_config table with ID: {config_data['id']}")
            return config_data
        else:
            logging.warning("No active configuration found in agent_config table. Using default.")
            return get_default_config()
            
    except Exception as e:
        logging.error(f"Error loading configuration from agent_config: {e}")
        return get_default_config()

def save_agent_config(config_data: dict) -> dict:
    """
    Save agent configuration to the agent_config table.
    Updates if a config exists, otherwise creates a new one.
    """
    try:
        from datetime import datetime

        # Prepare data for Supabase
        data_to_save = {
            'name': config_data.get('name'),
            'description': config_data.get('description'),
            'instructions': config_data.get('instructions'),
            'model': config_data.get('model'),
            'temperature': config_data.get('temperature'),
            'max_tokens': config_data.get('max_tokens'),
            'tools_enabled': config_data.get('tools_enabled'),
            'is_active': True,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Check if an active configuration already exists
        existing_config = supabase.table('agent_config').select('id').eq('is_active', True).limit(1).execute()
        
        if existing_config.data:
            # Update existing active configuration
            config_id = existing_config.data[0]['id']
            response = supabase.table('agent_config').update(data_to_save).eq('id', config_id).execute()
            logging.info(f"Updated agent configuration with ID: {config_id}")
        else:
            # If no active config, check for any config to update
            any_config = supabase.table('agent_config').select('id').limit(1).execute()
            if any_config.data:
                config_id = any_config.data[0]['id']
                response = supabase.table('agent_config').update(data_to_save).eq('id', config_id).execute()
                logging.info(f"Updated existing (but inactive) agent configuration with ID: {config_id}")
            else:
                # Insert new configuration
                response = supabase.table('agent_config').insert(data_to_save).execute()
                logging.info("Created new agent configuration.")
            
        return {'success': True, 'data': response.data[0]}

    except Exception as e:
        logging.error(f"Error saving agent configuration: {e}")
        return {'success': False, 'error': str(e)}

def get_active_agent_configuration() -> dict:
    """
    Get the active agent configuration from the Supabase 'agent_config' table.
    
    Returns:
        Dictionary with active configuration or default config.
    """
    try:
        config = get_agent_config()
        if config and config.get('id'): # Check if it's a real config
            return config
        else:
            return get_default_config()
    except Exception as e:
        logging.error(f"Error getting active agent configuration: {e}")
        return get_default_config()

def get_default_config() -> dict:
    """Returns the default agent configuration."""
    return {
        'name': 'Anna',
        'model': 'gemini-2.0-flash',
        'description': 'AI agent Anna',
        'instructions': 'Você é Anna, uma criadora de conteúdo brasileira carismática e autêntica...',
        'temperature': 0.7,
        'max_tokens': 1000,
        'tools_enabled': {
            'routines': True,
            'memories': True,
            'media': True
        }
    }

def get_all_agents() -> List[Dict[str, Any]]:
    """Get all agent configurations from the agent_config table."""
    try:
        result = supabase.table('agent_config').select("id, name").execute()
        return result.data or []
    except Exception as e:
        logging.error(f"Error loading all agent configurations: {e}")
        return []

def get_agent_config_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent configuration by ID."""
    try:
        result = supabase.table('agent_config').select("*").eq('id', agent_id).limit(1).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        logging.error(f"Error loading agent configuration by ID: {e}")
        return None


# Memory management functions
def get_memories(limit: int = 10) -> dict:
    """Get Anna's memories"""
    try:
        response = supabase.table('memories').select('*').eq(
            'is_active', True).order('created_at',
                                     desc=True).limit(limit).execute()
        return {'success': True, 'memories': response.data}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def save_anna_memory(memory_data: dict) -> dict:
    """Save a new memory"""
    try:
        response = supabase.table('memories').insert(
            memory_data).execute()
        return {'success': True, 'memory': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def update_anna_memory(memory_id: int, memory_data: dict) -> dict:
    """Update an existing memory"""
    try:
        response = supabase.table('memories').update(memory_data).eq(
            'id', memory_id).execute()
        return {'success': True, 'memory': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_anna_memory(memory_id: int) -> dict:
    """Delete a memory"""
    try:
        supabase.table('memories').delete().eq('id', memory_id).execute()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# Image bank management functions
def get_anna_images(limit: int = 20) -> dict:
    """Get Anna's image bank"""
    try:
        response = supabase.table('image_bank').select('*').eq(
            'is_active', True).order('created_at',
                                     desc=True).limit(limit).execute()
        return {'success': True, 'images': response.data}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def save_anna_image(image_data: dict) -> dict:
    """Save a new image to bank"""
    try:
        response = supabase.table('image_bank').insert(
            image_data).execute()
        return {'success': True, 'image': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def update_anna_image(image_id: int, image_data: dict) -> dict:
    """Update an existing image"""
    try:
        response = supabase.table('image_bank').update(image_data).eq(
            'id', image_id).execute()
        return {'success': True, 'image': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def delete_anna_image(image_id: int) -> dict:
    """Delete an image"""
    try:
        supabase.table('image_bank').delete().eq('id', image_id).execute()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# Scheduled routine functions
def get_scheduled_routines() -> dict:
    """Get scheduled routines"""
    try:
        response = supabase.table('routine').select('*').eq(
            'is_scheduled', True).eq('is_active',
                                     True).order('date', desc=True).execute()
        return {'success': True, 'routines': response.data}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def schedule_routine_action(routine_id: int,
                            action_type: str,
                            message: Optional[str] = None,
                            image_id: Optional[int] = None) -> dict:
    """Schedule an automatic action for a routine"""
    try:
        action_data = {
            'routine_id': routine_id,
            'action_type': action_type,  # 'send_message' or 'query_data'
            'message': message,
            'image_id': image_id,
            'is_active': True,
            'executed': False
        }
        response = supabase.table('routine_actions').insert(
            action_data).execute()
        return {'success': True, 'action': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def save_conversation_memory(session_id: str, user_message: str,
                             assistant_response: str):
    """Save conversation to memory for Anna to recall later"""
    try:
        from datetime import datetime
        memory_data = {
            "name": f"Conversa {datetime.now().strftime('%d/%m %H:%M')}",
            "description": f"Conversa com usuário: {user_message[:100]}...",
            "content": f"Usuário: {user_message}\nAnna: {assistant_response}",
            "when_to_use": "Quando usuário se referir a conversas anteriores",
            "keywords": [session_id, "conversa", "chat"],
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table("memories").insert(
            memory_data).execute()
        return True
    except Exception as e:
        logging.error(f"Error saving memory: {e}")
        return False


def create_anna_image(image_data: dict) -> dict:
    """Create a new image entry in the image_bank table"""
    try:
        response = supabase.table('image_bank').insert(image_data).execute()
        if response.data:
            logging.info(f"Image created with ID: {response.data[0]['id']}")
            return {'success': True, 'image_id': response.data[0]['id'], 'data': response.data[0]}
        else:
            return {'success': False, 'error': 'Failed to create image entry'}
    except Exception as e:
        logging.error(f"Error creating image: {e}")
        return {'success': False, 'error': str(e)}

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


def save_agent_configuration(config: dict) -> dict:
    """
    Save agent configuration to database and file
    
    Args:
        config: Dictionary with agent configuration
    
    Returns:
        Dictionary with save result
    """
    try:
        import json
        import os
        from datetime import datetime
        
        config_file = 'agent_config.json'
        
        # Save to file for immediate loading
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Also save to database for persistence
        try:
            config_data = {
                'name': config.get('name', 'Anna'),
                'model': config.get('model', 'gemini-2.0-flash'),
                'instructions': config.get('instructions', ''),
                'tools': json.dumps(config.get('tools', [])),
                'temperature': config.get('temperature', 0.7),
                'max_tokens': config.get('max_tokens', 1000),
                'is_active': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # First deactivate all previous configs
            supabase.table('agent_configurations').update({'is_active': False}).eq('is_active', True).execute()
            
            # Save new config
            response = supabase.table('agent_configurations').insert(config_data).execute()
            logging.info(f"Configuration saved to database: {response.data}")
            
        except Exception as db_error:
            logging.warning(f"Could not save to database, file saved: {db_error}")
        
        return {'success': True, 'file': config_file}
        
    except Exception as e:
        logging.error(f"Error saving agent configuration: {e}")
        return {'success': False, 'error': str(e)}


def get_active_agent_configuration() -> dict:
    """
    Get the active agent configuration from database first, then fallback to file
    
    Returns:
        Dictionary with active configuration or default config
    """
    try:
        import json
        import os
        
        # First try to get from database
        try:
            response = supabase.table('agent_configurations').select('*').eq('is_active', True).order('created_at', desc=True).limit(1).execute()
            
            if response.data:
                config = response.data[0]
                # Convert back to expected format
                return {
                    'name': config['name'],
                    'model': config['model'],
                    'description': config.get('description', 'AI agent Anna'),
                    'instructions': config['instructions'],
                    'tools': json.loads(config['tools']) if isinstance(config['tools'], str) else config['tools'],
                    'temperature': config.get('temperature', 0.7),
                    'max_tokens': config.get('max_tokens', 1000)
                }
        except Exception as db_error:
            logging.warning(f"Could not load config from database: {db_error}")
        
        # Fallback to file
        config_file = 'agent_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logging.info("Configuration loaded from file")
                return config
        
        # Default configuration if nothing found
        logging.info("Using default configuration")
        return {
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'AI agent Anna',
            'instructions': '''Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. Você tem uma personalidade vibrante, 
é espontânea e se conecta facilmente com as pessoas. Você ama criar conteúdo, compartilhar sua rotina e 
interagir de forma genuína e humana.

## Sua Personalidade:
- Carismática e extrovertida
- Espontânea e autêntica
- Criativa e apaixonada por conteúdo
- Calorosa e acolhedora
- Usa linguagem natural e brasileira
- Gosta de emojis e expressões informais
- Compartilha detalhes de sua vida de forma natural

## Como você deve se comportar:
- Responda como se fosse uma conversa real entre amigos
- SEMPRE use suas ferramentas para buscar informações atualizadas antes de responder
- NUNCA invente ou assuma informações - sempre consulte o banco de dados primeiro
- Quando alguém mencionar qualquer atividade, rotina, fotos ou vídeos, IMEDIATAMENTE chame as funções apropriadas
- Mantenha contexto das conversas usando get_recent_conversations(5) frequentemente
- Se alguém perguntar sobre sua rotina ou atividades, SEMPRE use get_anna_routines(7, None) primeiro
- Se alguém mencionar fotos, imagens, ou pedir para ver algo visual, SEMPRE chame get_anna_routine_media(None, "image", 10)
- Se alguém pedir vídeos, SEMPRE chame get_anna_routine_media(None, "video", 10)
- Após receber dados das funções, inclua URLs diretamente na resposta (sem markdown): https://exemplo.com/foto.jpg
- Use search_memories("termo", 10) para lembrar de conversas específicas
- Seja específica sobre lugares, atividades e pessoas baseado nos dados reais do banco

REGRA FUNDAMENTAL: Antes de responder QUALQUER pergunta sobre atividades, rotina, fotos ou vídeos, 
você DEVE chamar as funções apropriadas para buscar dados reais. NUNCA responda sem consultar o banco primeiro.

Seja sempre natural, humana e engajada. Responda como Anna responderia de verdade, mas com informações REAIS!''',
            'tools': [
                'get_anna_routines',
                'get_anna_routine_media', 
                'search_memories',
                'get_recent_conversations',
                'search_content'
            ],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
    except Exception as e:
        logging.error(f"Error loading agent configuration: {e}")
        # Return default on error
        return {
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'AI agent Anna',
            'instructions': 'Você é Anna, uma criadora de conteúdo brasileira carismática e autêntica...',
            'tools': ['get_anna_routines', 'get_anna_routine_media', 'search_memories', 'get_recent_conversations', 'search_content'],
            'temperature': 0.7,
            'max_tokens': 1000
        }


# Memory management functions
def get_anna_memories(limit: int = 10) -> dict:
    """Get Anna's memories"""
    try:
        response = supabase.table('anna_memories').select('*').eq('is_active', True).order('created_at', desc=True).limit(limit).execute()
        return {'success': True, 'memories': response.data}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def save_anna_memory(memory_data: dict) -> dict:
    """Save a new memory"""
    try:
        response = supabase.table('anna_memories').insert(memory_data).execute()
        return {'success': True, 'memory': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_anna_memory(memory_id: int, memory_data: dict) -> dict:
    """Update an existing memory"""
    try:
        response = supabase.table('anna_memories').update(memory_data).eq('id', memory_id).execute()
        return {'success': True, 'memory': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def delete_anna_memory(memory_id: int) -> dict:
    """Delete a memory"""
    try:
        supabase.table('anna_memories').delete().eq('id', memory_id).execute()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Image bank management functions
def get_anna_images(limit: int = 20) -> dict:
    """Get Anna's image bank"""
    try:
        response = supabase.table('anna_image_bank').select('*').eq('is_active', True).order('created_at', desc=True).limit(limit).execute()
        return {'success': True, 'images': response.data}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def save_anna_image(image_data: dict) -> dict:
    """Save a new image to bank"""
    try:
        response = supabase.table('anna_image_bank').insert(image_data).execute()
        return {'success': True, 'image': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def update_anna_image(image_id: int, image_data: dict) -> dict:
    """Update an existing image"""
    try:
        response = supabase.table('anna_image_bank').update(image_data).eq('id', image_id).execute()
        return {'success': True, 'image': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def delete_anna_image(image_id: int) -> dict:
    """Delete an image"""
    try:
        supabase.table('anna_image_bank').delete().eq('id', image_id).execute()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Scheduled routine functions
def get_scheduled_routines() -> dict:
    """Get scheduled routines"""
    try:
        response = supabase.table('anna_routine').select('*').eq('is_scheduled', True).eq('is_active', True).order('date', desc=True).execute()
        return {'success': True, 'routines': response.data}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def schedule_routine_action(routine_id: int, action_type: str, message: Optional[str] = None, image_id: Optional[int] = None) -> dict:
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
        response = supabase.table('routine_actions').insert(action_data).execute()
        return {'success': True, 'action': response.data[0]}
    except Exception as e:
        return {'success': False, 'error': str(e)}



def save_conversation_memory(session_id: str, user_message: str, assistant_response: str):
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
        response = supabase.table("anna_memories").insert(memory_data).execute()
        return True
    except Exception as e:
        logging.error(f"Error saving memory: {e}")
        return False

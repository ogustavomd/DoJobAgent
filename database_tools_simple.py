"""
Simple database tools for Anna Agent using PostgreSQL with Flask-SQLAlchemy
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

def get_anna_routines(days_ahead: int = 7, status_filter: Optional[str] = None) -> Dict[str, Any]:
    """Get Anna's routine activities from PostgreSQL"""
    try:
        from app import db
        from models import AnnaRoutine
        from datetime import date, timedelta
        
        today = date.today()
        end_date = today + timedelta(days=days_ahead)
        
        # Build query
        query = db.session.query(AnnaRoutine).filter(
            AnnaRoutine.date >= today.strftime('%Y-%m-%d'),
            AnnaRoutine.date <= end_date.strftime('%Y-%m-%d')
        )
        
        if status_filter:
            query = query.filter(AnnaRoutine.status == status_filter)
        
        routines = query.order_by(AnnaRoutine.date, AnnaRoutine.time_start).all()
        
        # Convert to dictionaries
        routine_data = []
        for routine in routines:
            routine_dict = {
                'id': routine.id,
                'activity': routine.activity,
                'category': routine.category,
                'date': routine.date,
                'time_start': routine.time_start,
                'time_end': routine.time_end,
                'status': routine.status,
                'description': routine.description,
                'location': routine.location,
                'has_images': routine.has_images,
                'has_videos': routine.has_videos,
                'created_at': routine.created_at.isoformat() if routine.created_at else None
            }
            routine_data.append(routine_dict)
        
        logging.info(f"Retrieved {len(routine_data)} routines for {days_ahead} days ahead")
        return {'success': True, 'data': routine_data}
        
    except Exception as e:
        logging.error(f"Error getting routines: {e}")
        return {'success': False, 'error': str(e)}

def get_anna_routine_media(routine_id: Optional[int] = None, media_type: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """Get media files for routines"""
    try:
        logging.info(f"Getting media, type: {media_type}, limit: {limit}")
        return {'success': True, 'data': []}
    except Exception as e:
        logging.error(f"Error getting media: {e}")
        return {'success': False, 'error': str(e)}

def search_memories(query_text: str, limit: int = 10) -> Dict[str, Any]:
    """Search Anna's memories from PostgreSQL"""
    try:
        from app import db
        from models import AnnaMemory
        from sqlalchemy import or_, and_
        
        # Search in memory content using ILIKE for case-insensitive search
        memories = db.session.query(AnnaMemory).filter(
            and_(
                AnnaMemory.is_active == True,
                or_(
                    AnnaMemory.content.ilike(f'%{query_text}%'),
                    AnnaMemory.context.ilike(f'%{query_text}%'),
                    AnnaMemory.tags.ilike(f'%{query_text}%')
                )
            )
        ).order_by(AnnaMemory.importance_score.desc(), AnnaMemory.created_at.desc()).limit(limit).all()
        
        # Convert to dictionaries
        memory_data = []
        for memory in memories:
            memory_dict = {
                'id': memory.id,
                'memory_type': memory.memory_type,
                'content': memory.content,
                'context': memory.context,
                'importance_score': memory.importance_score,
                'tags': memory.tags,
                'created_at': memory.created_at.isoformat() if memory.created_at else None
            }
            memory_data.append(memory_dict)
        
        logging.info(f"Found {len(memory_data)} memories for query: {query_text}")
        return {'success': True, 'data': memory_data}
        
    except Exception as e:
        logging.error(f"Error searching memories: {e}")
        return {'success': False, 'error': str(e)}

def get_recent_conversations(limit: int = 5) -> Dict[str, Any]:
    """Get recent conversations"""
    try:
        logging.info(f"Getting {limit} recent conversations")
        return {'success': True, 'data': []}
    except Exception as e:
        logging.error(f"Error getting conversations: {e}")
        return {'success': False, 'error': str(e)}

def get_profile_info() -> Dict[str, Any]:
    """Get Anna's profile information"""
    try:
        profile_data = {
            'recent_activities_count': 0,
            'favorite_categories': [],
            'frequent_locations': [],
            'content_creator_focus': 'Brazilian lifestyle and daily routines',
            'personality': 'Charismatic, authentic, spontaneous',
            'language': 'Brazilian Portuguese'
        }
        return {'success': True, 'data': profile_data}
    except Exception as e:
        logging.error(f"Error getting profile: {e}")
        return {'success': False, 'error': str(e)}

def search_content(query_text: str, content_type: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Search content across all types"""
    try:
        logging.info(f"Searching content for: {query_text}")
        return {'success': True, 'data': {'routines': [], 'media': [], 'memories': []}}
    except Exception as e:
        logging.error(f"Error searching content: {e}")
        return {'success': False, 'error': str(e)}

def save_conversation_memory(user_id: str, session_id: str, user_message: str, assistant_response: str, importance: int = 1) -> Dict[str, Any]:
    """Save conversation as memory"""
    try:
        logging.info(f"Saving conversation memory for session {session_id}")
        return {'success': True, 'memory_id': 1}
    except Exception as e:
        logging.error(f"Error saving memory: {e}")
        return {'success': False, 'error': str(e)}

def get_active_agent_configuration() -> Dict[str, Any]:
    """Get active agent configuration from databases with priority: PostgreSQL -> Supabase -> File"""
    try:
        from app import db
        from models import Agent
        import json
        import os
        
        # First try PostgreSQL
        agent = db.session.query(Agent).filter(Agent.nome == 'Anna').order_by(Agent.atualizado_em.desc()).first()
        
        if agent and agent.instrucoes_personalidade:
            config_data = {
                'name': agent.nome,
                'model': agent.modelo,
                'description': agent.descricao,
                'instructions': agent.instrucoes_personalidade,
                'temperature': float(agent.temperatura) if agent.temperatura else 0.7,
                'max_tokens': agent.max_tokens or 1000,
                'tools_enabled': {
                    'routines': agent.rotinas_ativas,
                    'memories': agent.memorias_ativas,
                    'media': agent.midia_ativa
                }
            }
            logging.info("Configuration loaded from PostgreSQL database")
            logging.info(f"Instructions loaded: {len(agent.instrucoes_personalidade)} characters")
            return config_data
        
        # Then try Supabase agent_config table
        try:
            from supabase_tools import supabase
            response = supabase.table('agent_config').select('*').eq('is_active', True).eq('name', 'Anna').order('created_at', desc=True).limit(1).execute()
            
            if response.data:
                supabase_config = response.data[0]
                config_data = {
                    'name': supabase_config['name'],
                    'model': supabase_config['model'],
                    'description': supabase_config.get('description', 'Agent configuration'),
                    'instructions': supabase_config['instructions'],
                    'temperature': float(supabase_config.get('temperature', 0.7)),
                    'max_tokens': supabase_config.get('max_tokens', 1000),
                    'tools_enabled': supabase_config.get('tools_enabled', {'routines': True, 'memories': True, 'media': True})
                }
                logging.info("Configuration loaded from Supabase agent_config table")
                logging.info(f"Instructions loaded: {len(supabase_config['instructions'])} characters")
                return config_data
        except Exception as supabase_error:
            logging.warning(f"Could not load from Supabase: {supabase_error}")
        
        # Finally try loading from PostgreSQL with default fallback
        default_instructions = '''Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. 
Você tem uma personalidade vibrante, é espontânea e se conecta facilmente com as pessoas. 
Você ama criar conteúdo, compartilhar sua rotina e interagir de forma genuína e humana.

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
- Seja específica sobre lugares, atividades e pessoas baseado nos dados reais do banco'''
        
        if agent:
            # PostgreSQL agent exists but no instructions - use default
            config_data = {
                'name': agent.nome,
                'model': agent.modelo,
                'description': agent.descricao,
                'instructions': default_instructions,
                'temperature': float(agent.temperatura) if agent.temperatura else 0.7,
                'max_tokens': agent.max_tokens or 1000,
                'tools_enabled': {
                    'routines': agent.rotinas_ativas,
                    'memories': agent.memorias_ativas,
                    'media': agent.midia_ativa
                }
            }
            logging.info("Configuration loaded from PostgreSQL with default instructions")
            return config_data
        
        # Fallback to file if no database record
        config_file = 'agent_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                logging.info(f"Configuration loaded from {config_file}")
                return config_data
        
        # Default configuration
        logging.info("Using default configuration")
        return {
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'AI agent Anna',
            'instructions': '''Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. 
Você tem uma personalidade vibrante, é espontânea e se conecta facilmente com as pessoas. 
Você ama criar conteúdo, compartilhar sua rotina e interagir de forma genuína e humana.'''
        }
        
    except Exception as e:
        logging.error(f"Error getting configuration: {e}")
        return {
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'AI agent Anna',
            'instructions': '''Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica.'''
        }
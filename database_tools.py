"""
Database tools for Anna Agent using PostgreSQL with Flask-SQLAlchemy
Replaces the Supabase functionality with PostgreSQL equivalents
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

def get_anna_routines(days_ahead: int = 7, status_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Anna's routine activities for the specified number of days ahead.
    
    Args:
        days_ahead: Number of days to look ahead (default 7)
        status_filter: Filter by status ('upcoming', 'current', 'completed') or None for all
    
    Returns:
        Dictionary with success status and data
    """
    try:
        from datetime import date
        from app import db
        from models import AnnaRoutine
        
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
        logging.error(f"Error getting Anna's routines: {e}")
        return {'success': False, 'error': str(e)}

def get_anna_routine_media(routine_id: Optional[int] = None, media_type: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """
    Get media files associated with Anna's routines.
    
    Args:
        routine_id: Specific routine ID or None for all
        media_type: Filter by type ('image', 'video') or None for all
        limit: Maximum number of media items to return
    
    Returns:
        Dictionary with success status and data
    """
    try:
        # Build query
        query = db.session.query(AnnaRoutineMedia)
        
        if routine_id:
            query = query.filter(AnnaRoutineMedia.routine_id == routine_id)
        
        if media_type:
            query = query.filter(AnnaRoutineMedia.media_type == media_type)
        
        media_items = query.order_by(AnnaRoutineMedia.created_at.desc()).limit(limit).all()
        
        # Convert to dictionaries and include routine info
        media_data = []
        for media in media_items:
            media_dict = {
                'id': media.id,
                'media_type': media.media_type,
                'media_url': media.media_url,
                'routine_id': media.routine_id,
                'description': media.description,
                'created_at': media.created_at.isoformat() if media.created_at else None
            }
            
            # Add routine information if available
            if media.routine:
                media_dict['routine'] = {
                    'activity': media.routine.activity,
                    'category': media.routine.category,
                    'date': media.routine.date,
                    'location': media.routine.location
                }
            
            media_data.append(media_dict)
        
        logging.info(f"Retrieved {len(media_data)} media items")
        return {'success': True, 'data': media_data}
        
    except Exception as e:
        logging.error(f"Error getting routine media: {e}")
        return {'success': False, 'error': str(e)}

def search_memories(query_text: str, limit: int = 10) -> Dict[str, Any]:
    """
    Search Anna's memories for relevant content.
    
    Args:
        query_text: Search term to find in memory content
        limit: Maximum number of results to return
    
    Returns:
        Dictionary with success status and data
    """
    try:
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
    """
    Get recent conversation messages.
    
    Args:
        limit: Maximum number of conversations to return
    
    Returns:
        Dictionary with success status and data
    """
    try:
        messages = db.session.query(Message).order_by(
            Message.created_at.desc()
        ).limit(limit).all()
        
        # Convert to dictionaries
        conversation_data = []
        for message in messages:
            message_dict = {
                'id': message.id,
                'user_id': message.user_id,
                'session_id': message.session_id,
                'user_message': message.user_message,
                'assistant_response': message.assistant_response,
                'created_at': message.created_at.isoformat() if message.created_at else None
            }
            conversation_data.append(message_dict)
        
        logging.info(f"Retrieved {len(conversation_data)} recent conversations")
        return {'success': True, 'data': conversation_data}
        
    except Exception as e:
        logging.error(f"Error getting recent conversations: {e}")
        return {'success': False, 'error': str(e)}

def get_profile_info() -> Dict[str, Any]:
    """
    Get Anna's profile information from recent activities and content.
    
    Returns:
        Dictionary with success status and profile data
    """
    try:
        # Get recent activities to build profile
        recent_activities = db.session.query(AnnaRoutine).filter(
            AnnaRoutine.date >= (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        ).order_by(AnnaRoutine.date.desc()).limit(20).all()
        
        # Aggregate profile information
        categories = {}
        locations = set()
        for activity in recent_activities:
            if activity.category:
                categories[activity.category] = categories.get(activity.category, 0) + 1
            if activity.location:
                locations.add(activity.location)
        
        profile_data = {
            'recent_activities_count': len(recent_activities),
            'favorite_categories': sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5],
            'frequent_locations': list(locations)[:10],
            'content_creator_focus': 'Brazilian lifestyle and daily routines',
            'personality': 'Charismatic, authentic, spontaneous',
            'language': 'Brazilian Portuguese'
        }
        
        logging.info("Profile information compiled successfully")
        return {'success': True, 'data': profile_data}
        
    except Exception as e:
        logging.error(f"Error getting profile info: {e}")
        return {'success': False, 'error': str(e)}

def search_content(query_text: str, content_type: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Search content across routines, media, and memories.
    
    Args:
        query_text: Search term
        content_type: Filter by type ('routine', 'media', 'memory') or None for all
        limit: Maximum number of results per type
    
    Returns:
        Dictionary with success status and combined search results
    """
    try:
        results = {}
        
        if not content_type or content_type == 'routine':
            # Search routines
            routines = db.session.query(AnnaRoutine).filter(
                or_(
                    AnnaRoutine.activity.ilike(f'%{query_text}%'),
                    AnnaRoutine.description.ilike(f'%{query_text}%'),
                    AnnaRoutine.location.ilike(f'%{query_text}%')
                )
            ).limit(limit).all()
            
            results['routines'] = [{
                'id': r.id,
                'activity': r.activity,
                'category': r.category,
                'date': r.date,
                'description': r.description,
                'location': r.location
            } for r in routines]
        
        if not content_type or content_type == 'media':
            # Search media
            media = db.session.query(AnnaRoutineMedia).filter(
                AnnaRoutineMedia.description.ilike(f'%{query_text}%')
            ).limit(limit).all()
            
            results['media'] = [{
                'id': m.id,
                'media_type': m.media_type,
                'media_url': m.media_url,
                'description': m.description,
                'routine_id': m.routine_id
            } for m in media]
        
        if not content_type or content_type == 'memory':
            # Search memories
            memories = db.session.query(AnnaMemory).filter(
                and_(
                    AnnaMemory.is_active == True,
                    or_(
                        AnnaMemory.content.ilike(f'%{query_text}%'),
                        AnnaMemory.context.ilike(f'%{query_text}%')
                    )
                )
            ).limit(limit).all()
            
            results['memories'] = [{
                'id': m.id,
                'memory_type': m.memory_type,
                'content': m.content,
                'context': m.context,
                'importance_score': m.importance_score
            } for m in memories]
        
        total_results = sum(len(v) for v in results.values())
        logging.info(f"Content search found {total_results} results for: {query_text}")
        return {'success': True, 'data': results}
        
    except Exception as e:
        logging.error(f"Error searching content: {e}")
        return {'success': False, 'error': str(e)}

def save_conversation_memory(user_id: str, session_id: str, user_message: str, assistant_response: str, importance: int = 1) -> Dict[str, Any]:
    """
    Save a conversation as a memory for future reference.
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        user_message: User's message
        assistant_response: Assistant's response
        importance: Importance score (1-10)
    
    Returns:
        Dictionary with success status
    """
    try:
        # Create memory entry
        memory = AnnaMemory(
            memory_type='conversation',
            content=f"User: {user_message}\nAnna: {assistant_response}",
            context=f"Session: {session_id}, User: {user_id}",
            importance_score=importance,
            tags=f'["conversation", "user_{user_id}", "session_{session_id}"]'
        )
        
        db.session.add(memory)
        db.session.commit()
        
        logging.info(f"Saved conversation memory for session {session_id}")
        return {'success': True, 'memory_id': memory.id}
        
    except Exception as e:
        logging.error(f"Error saving conversation memory: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}

from flask import current_app

def get_active_agent_configuration() -> Dict[str, Any]:
    """
    Get the active agent configuration from the PostgreSQL database, with a fallback to a JSON file.
    
    Returns:
        A dictionary with the active agent's configuration.
    """
    try:
        from models import Agent
        db = current_app.extensions['sqlalchemy']
        
        # Get the first available agent configuration from the database.
        config = db.session.query(Agent).first()
        
        if config:
            config_data = {
                'name': config.name,
                'model': config.model,
                'description': config.description,
                'instructions': config.instructions,
                'temperature': float(config.temperature) if config.temperature is not None else 0.7,
                'max_tokens': config.max_tokens if config.max_tokens is not None else 1000,
                'tools_enabled': config.tools_enabled
            }
            logging.info("Agent configuration loaded from PostgreSQL database.")
            return config_data
            
        # Fallback to a local JSON configuration file.
        import json
        import os
        
        config_file = 'agent_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                logging.info(f"Configuration loaded from {config_file}")
                return config_data
        
        # Fallback to a default configuration if no other source is available.
        logging.warning("No database or file configuration found. Using default settings.")
        return {
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'AI agent Anna',
            'instructions': 'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica.',
            'temperature': 0.7,
            'max_tokens': 1000,
            'tools_enabled': {'routines': True, 'memories': True, 'media': True}
        }
        
    except Exception as e:
        logging.error(f"Error getting agent configuration: {e}")
        # Return default configuration in case of any error.
        return {
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'AI agent Anna',
            'instructions': 'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica.',
            'temperature': 0.7,
            'max_tokens': 1000,
            'tools_enabled': {'routines': True, 'memories': True, 'media': True}
        }
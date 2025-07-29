import os
import logging
import asyncio
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from anna_agent import create_anna_agent
from google.genai import types
from ai_routine_engine import RoutineSuggestionEngine
from whatsapp_integration import whatsapp_manager
from chat_session_manager_postgres import chat_session_manager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    db.create_all()

# Initialize Anna agent
anna_agent = None

def init_agent():
    """Initialize Anna agent with configuration from persistent storage"""
    global anna_agent
    try:
        from supabase_tools import get_active_agent_configuration
        config = get_active_agent_configuration()
        anna_agent = create_anna_agent()
        logging.info("Anna agent created successfully with configuration")
    except Exception as e:
        logging.error(f"Failed to initialize Anna agent: {e}")
        # Fallback to default agent
        try:
            anna_agent = create_anna_agent()
            logging.info("Anna agent initialized with fallback configuration")
        except Exception as fallback_error:
            logging.error(f"Fallback initialization also failed: {fallback_error}")
            raise

# Initialize agent on startup
init_agent()

@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with automatic session management"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message']
        logging.info(f"Received message: {user_message}")
        
        # Get user info from request or create default
        contact_phone = data.get('phone', 'web_user')
        contact_name = data.get('name', 'Usuário Web')
        channel = data.get('channel', 'chat')
        
        # Get or create chat session
        chat_session_id = chat_session_manager.get_or_create_session(
            contact_phone=contact_phone,
            contact_name=contact_name, 
            channel=channel
        )
        
        # Save user message
        chat_session_manager.save_message(
            session_id=chat_session_id,
            sender_phone=contact_phone,
            sender_name=contact_name,
            content=user_message,
            is_from_bot=False
        )
        
        # Get or create Flask session ID for ADK
        if 'session_id' not in session:
            session['session_id'] = f"session_{os.urandom(8).hex()}"
        
        flask_session_id = session['session_id']
        user_id = contact_phone
        
        # Run the agent asynchronously
        response = asyncio.run(run_anna_agent(user_message, user_id, flask_session_id))
        
        # Save Anna's response
        if response:
            chat_session_manager.save_message(
                session_id=chat_session_id,
                sender_phone='anna_bot',
                sender_name='Anna',
                content=response,
                is_from_bot=True
            )
        
        return jsonify({
            'response': response,
            'session_id': flask_session_id,
            'chat_session_id': chat_session_id
        })
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

async def run_anna_agent(user_message: str, user_id: str, session_id: str):
    """Run Anna agent with the user message"""
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        
        # Create session service and session
        session_service = InMemorySessionService()
        session_obj = await session_service.create_session(
            app_name="anna_chat", 
            user_id=user_id, 
            session_id=session_id
        )
        
        # Load conversation history from database
        await load_conversation_history(session_obj, user_id, session_id)
        
        # Create runner
        if anna_agent:
            runner = Runner(agent=anna_agent, app_name="anna_chat", session_service=session_service)
        else:
            raise Exception("Agent not initialized")
        
        # Create user content
        content = types.Content(role='user', parts=[types.Part(text=user_message)])
        
        # Run agent and collect response
        events = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
        
        final_response = ""
        async for event in events:
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break
        
        # Save conversation to database
        if final_response:
            await save_conversation_turn(user_id, session_id, user_message, final_response)
        
        return final_response or "Desculpe, não consegui processar sua mensagem no momento."
        
    except Exception as e:
        logging.error(f"Error running Anna agent: {e}")
        return "Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes."

async def load_conversation_history(session_obj, user_id: str, session_id: str):
    """Load conversation history from chat sessions into ADK session"""
    try:
        # Get chat sessions for this user/phone
        sessions = chat_session_manager.get_contact_sessions(user_id)
        
        # Load messages from the most recent session
        if sessions:
            latest_session = sessions[0]  # Most recent session
            messages = chat_session_manager.get_session_messages(latest_session['id'], limit=20)
            
            # Add messages to ADK session history
            for msg in messages:
                if msg['is_from_bot']:
                    # Assistant message
                    assistant_content = types.Content(role='model', parts=[types.Part(text=msg['content'])])
                    session_obj.add_message(assistant_content)
                else:
                    # User message
                    user_content = types.Content(role='user', parts=[types.Part(text=msg['content'])])
                    session_obj.add_message(user_content)
                    
            logging.info(f"Loaded {len(messages)} messages for ADK session {session_id}")
        
    except Exception as e:
        logging.error(f"Error loading conversation history: {e}")

async def save_conversation_turn(user_id: str, session_id: str, user_message: str, assistant_response: str):
    """Save conversation turn - handled by ChatSessionManager in main chat endpoint"""
    # This function is no longer needed as messages are saved directly in chat endpoint
    logging.info(f"Conversation turn handled by ChatSessionManager for session {session_id}")
    pass

# Admin routes
@app.route('/admin')
def admin():
    """Admin interface for managing Anna's routine"""
    return render_template('admin.html')

@app.route('/config')
def config():
    """Configuration interface for agent settings"""
    return render_template('config.html')

@app.route('/admin/api/activities')
def admin_get_activities():
    """Get all activities for calendar display from PostgreSQL"""
    try:
        from models import Routine
        
        routines = db.session.query(Routine).order_by(Routine.date.asc()).all()
        
        # Format for FullCalendar
        events = []
        for activity in routines:
            # Format date and time properly for FullCalendar
            date_str = activity.date.isoformat() if activity.date else ''
            time_start_str = activity.time_start.strftime('%H:%M:%S') if activity.time_start else '00:00:00'
            time_end_str = activity.time_end.strftime('%H:%M:%S') if activity.time_end else '23:59:59'
            
            events.append({
                'id': str(activity.id),  # Convert UUID to string
                'title': activity.activity,
                'start': f"{date_str}T{time_start_str}",
                'end': f"{date_str}T{time_end_str}",
                'className': f"fc-event-{activity.category}",
                'extendedProps': {
                    'category': activity.category,
                    'status': activity.status,
                    'location': activity.location,
                    'description': activity.description,
                    'has_images': activity.has_images or False,
                    'has_videos': activity.has_videos or False
                }
            })
        
        return jsonify(events)
    except Exception as e:
        logging.error(f"Error getting activities: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/<activity_id>')
def admin_get_activity(activity_id):
    """Get specific activity details from PostgreSQL"""
    try:
        from models import Routine
        
        routine = db.session.query(Routine).filter(Routine.id == activity_id).first()
        
        if not routine:
            return jsonify({'error': 'Activity not found'}), 404
            
        activity_data = {
            'id': str(routine.id),  # Convert UUID to string
            'date': routine.date.isoformat() if routine.date else None,
            'time_start': routine.time_start.strftime('%H:%M') if routine.time_start else None,
            'time_end': routine.time_end.strftime('%H:%M') if routine.time_end else None,
            'activity': routine.activity,
            'category': routine.category,
            'location': routine.location,
            'description': routine.description,
            'status': routine.status,
            'has_images': routine.has_images,
            'has_videos': routine.has_videos,
            'created_at': routine.created_at.isoformat() if routine.created_at else None
        }
        
        return jsonify(activity_data)
    except Exception as e:
        logging.error(f"Error getting activity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/date/<date>')
def admin_get_activities_by_date(date):
    """Get activities for specific date from PostgreSQL"""
    try:
        from models import Routine
        from datetime import datetime
        
        # Convert date string to date object for database query
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        routines = db.session.query(Routine).filter(
            Routine.date == date_obj
        ).order_by(Routine.time_start.asc()).all()
        
        activities = []
        for routine in routines:
            activity_data = {
                'id': str(routine.id),  # Convert UUID to string
                'date': routine.date.isoformat() if routine.date else None,
                'time_start': routine.time_start.strftime('%H:%M') if routine.time_start else None,
                'time_end': routine.time_end.strftime('%H:%M') if routine.time_end else None,
                'activity': routine.activity,
                'category': routine.category,
                'location': routine.location,
                'description': routine.description,
                'status': routine.status,
                'has_images': routine.has_images,
                'has_videos': routine.has_videos
            }
            activities.append(activity_data)
        
        return jsonify(activities)
    except Exception as e:
        logging.error(f"Error getting activities by date: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/list')
def admin_get_activities_list():
    """Get all activities for list view with filtering support"""
    try:
        from models import Routine
        from datetime import datetime
        from sqlalchemy import func
        
        # Get filter parameters
        category_filter = request.args.get('category')
        status_filter = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        search_term = request.args.get('search')
        
        # Start with base query
        query = db.session.query(Routine)
        
        # Apply filters
        if category_filter:
            query = query.filter(Routine.category == category_filter)
        
        if status_filter:
            query = query.filter(Routine.status == status_filter)
            
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Routine.date >= date_from_obj)
            
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Routine.date <= date_to_obj)
            
        if search_term:
            query = query.filter(
                func.lower(Routine.activity).contains(search_term.lower()) |
                func.lower(Routine.description).contains(search_term.lower()) |
                func.lower(Routine.location).contains(search_term.lower())
            )
        
        # Order by date and time
        routines = query.order_by(Routine.date.desc(), Routine.time_start.asc()).all()
        
        # Group by date
        activities_by_date = {}
        for routine in routines:
            date_str = routine.date.isoformat() if routine.date else 'sem-data'
            
            if date_str not in activities_by_date:
                activities_by_date[date_str] = []
            
            activity_data = {
                'id': str(routine.id),
                'date': routine.date.isoformat() if routine.date else None,
                'time_start': routine.time_start.strftime('%H:%M') if routine.time_start else None,
                'time_end': routine.time_end.strftime('%H:%M') if routine.time_end else None,
                'activity': routine.activity,
                'category': routine.category,
                'location': routine.location,
                'description': routine.description,
                'status': routine.status,
                'has_images': routine.has_images or False,
                'has_videos': routine.has_videos or False,
                'created_at': routine.created_at.isoformat() if routine.created_at else None
            }
            activities_by_date[date_str].append(activity_data)
        
        return jsonify(activities_by_date)
    except Exception as e:
        logging.error(f"Error getting activities list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/filters')
def admin_get_filter_options():
    """Get available filter options for list view"""
    try:
        from models import Routine
        from sqlalchemy import distinct
        
        categories = db.session.query(distinct(Routine.category)).filter(
            Routine.category.isnot(None)
        ).all()
        
        statuses = db.session.query(distinct(Routine.status)).filter(
            Routine.status.isnot(None)
        ).all()
        
        return jsonify({
            'categories': [cat[0] for cat in categories if cat[0]],
            'statuses': [status[0] for status in statuses if status[0]]
        })
    except Exception as e:
        logging.error(f"Error getting filter options: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/<activity_id>/media')
def admin_get_activity_media(activity_id):
    """Get media for specific activity"""
    try:
        from supabase_tools import supabase
        response = supabase.table('anna_routine_media').select('*').eq('routine_id', activity_id).execute()
        return jsonify(response.data)
    except Exception as e:
        logging.error(f"Error getting activity media: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/create', methods=['POST'])
def admin_create_activity():
    """Create new activity in PostgreSQL"""
    try:
        from models import Routine
        from datetime import datetime
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logging.info(f"Creating activity with data: {data}")
        
        # Validate required fields
        required_fields = ['date', 'activity', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Convert date string to date object
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Convert time strings to time objects
        time_start_obj = datetime.strptime(data.get('time_start', '00:00'), '%H:%M').time() if data.get('time_start') else None
        time_end_obj = datetime.strptime(data.get('time_end', '23:59'), '%H:%M').time() if data.get('time_end') else None
        
        # Use dual sync system for PostgreSQL + Supabase
        from dual_database_sync import dual_sync
        
        routine_data = {
            'date': date_obj,
            'time_start': time_start_obj,
            'time_end': time_end_obj,
            'activity': data['activity'],
            'category': data['category'],
            'location': data.get('location', ''),
            'description': data.get('description', ''),
            'status': 'upcoming',
            'has_images': False,
            'has_videos': False
        }
        
        activity_id = dual_sync.sync_routine(routine_data)
        
        if activity_id:
            logging.info(f"Activity created with ID: {activity_id}")
            return jsonify({
                'success': True, 
                'activity_id': activity_id,
                'message': 'Atividade criada com sucesso em ambos os bancos!'
            })
        else:
            return jsonify({'error': 'Falha ao criar atividade'}), 500
        
    except Exception as e:
        logging.error(f"Error creating activity: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/<activity_id>', methods=['PUT'])
def admin_update_activity(activity_id):
    """Update existing activity in PostgreSQL"""
    try:
        from models import Routine
        from datetime import datetime
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logging.info(f"Updating activity {activity_id} with data: {data}")
        
        # Find the activity
        routine = db.session.query(Routine).filter(Routine.id == activity_id).first()
        
        if not routine:
            return jsonify({'error': 'Activity not found'}), 404
        
        # Update fields with proper data type conversions
        if 'date' in data:
            routine.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        if 'time_start' in data:
            routine.time_start = datetime.strptime(data['time_start'], '%H:%M').time() if data['time_start'] else None
        if 'time_end' in data:
            routine.time_end = datetime.strptime(data['time_end'], '%H:%M').time() if data['time_end'] else None
        if 'activity' in data:
            routine.activity = data['activity']
        if 'category' in data:
            routine.category = data['category']
        if 'location' in data:
            routine.location = data['location']
        if 'description' in data:
            routine.description = data['description']
        if 'status' in data:
            routine.status = data['status']
        
        db.session.commit()
        logging.info(f"Activity {activity_id} updated successfully")
        
        return jsonify({
            'success': True, 
            'message': 'Atividade atualizada com sucesso!'
        })
        
    except Exception as e:
        logging.error(f"Error updating activity: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/<activity_id>', methods=['DELETE'])
def admin_delete_activity(activity_id):
    """Delete activity from PostgreSQL"""
    try:
        from models import Routine
        
        # Use dual sync system for delete
        from dual_database_sync import dual_sync
        
        success = dual_sync.sync_routine_delete(activity_id)
        
        if success:
            logging.info(f"Activity {activity_id} deleted successfully from both databases")
            return jsonify({
                'success': True, 
                'message': 'Atividade excluída com sucesso de ambos os bancos!'
            })
        else:
            return jsonify({'error': 'Falha ao excluir atividade'}), 500
        
    except Exception as e:
        logging.error(f"Error deleting activity: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/<activity_id>', methods=['PUT'])
def admin_update_activity_supabase(activity_id):
    """Update an existing activity with Supabase storage"""
    from supabase_tools import supabase
    import uuid
    
    try:
        # Parse the multipart data
        activity_data = {
            'date': request.form.get('date'),
            'time_start': request.form.get('time_start'),
            'time_end': request.form.get('time_end'),
            'activity': request.form.get('activity'),
            'category': request.form.get('category'),
            'location': request.form.get('location'),
            'description': request.form.get('description'),
            'status': 'upcoming'
        }
        
        # Update activity
        supabase.table('anna_routine').update(activity_data).eq('id', activity_id).execute()
        
        # Handle new media files
        media_files = request.files.getlist('media_files')
        has_new_media = False
        
        for file in media_files:
            if file and file.filename:
                try:
                    # Upload to Supabase storage
                    file_extension = file.filename.split('.')[-1]
                    file_name = f"{uuid.uuid4()}.{file_extension}"
                    
                    # Upload file
                    file.seek(0)  # Reset file pointer
                    storage_response = supabase.storage.from_('conteudo').upload(file_name, file.read())
                    
                    # Get public URL
                    file_url = supabase.storage.from_('conteudo').get_public_url(file_name)
                    
                    # Determine media type
                    media_type = 'video' if file.content_type and file.content_type.startswith('video/') else 'image'
                    
                    # Save media record
                    media_data = {
                        'routine_id': activity_id,
                        'media_url': file_url,
                        'media_type': media_type,
                        'description': f"Mídia da atividade: {activity_data['activity']}"
                    }
                    
                    supabase.table('anna_routine_media').insert(media_data).execute()
                    has_new_media = True
                    
                except Exception as file_error:
                    logging.error(f"Error uploading file {file.filename}: {file_error}")
                    continue
        
        # Update media flags if new media was added
        if has_new_media:
            # Check current media
            media_response = supabase.table('anna_routine_media').select('media_type').eq('routine_id', activity_id).execute()
            
            has_images = any(item['media_type'] == 'image' for item in media_response.data)
            has_videos = any(item['media_type'] == 'video' for item in media_response.data)
            
            supabase.table('anna_routine').update({
                'has_images': has_images,
                'has_videos': has_videos
            }).eq('id', activity_id).execute()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error updating activity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/media/<media_id>', methods=['DELETE'])
def admin_delete_media(media_id):
    """Delete specific media file"""
    try:
        from supabase_tools import supabase
        
        # Get media info
        media_response = supabase.table('anna_routine_media').select('*').eq('id', media_id).single().execute()
        media = media_response.data
        
        # Delete from storage
        file_name = media['media_url'].split('/')[-1]
        try:
            supabase.storage.from_('conteudo').remove([file_name])
        except:
            pass  # Continue even if file deletion fails
        
        # Delete media record
        supabase.table('anna_routine_media').delete().eq('id', media_id).execute()
        
        # Update activity media flags
        routine_id = media['routine_id']
        remaining_media = supabase.table('anna_routine_media').select('media_type').eq('routine_id', routine_id).execute()
        
        has_images = any(item['media_type'] == 'image' for item in remaining_media.data)
        has_videos = any(item['media_type'] == 'video' for item in remaining_media.data)
        
        supabase.table('anna_routine').update({
            'has_images': has_images,
            'has_videos': has_videos
        }).eq('id', routine_id).execute()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error deleting media: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'agent_initialized': anna_agent is not None})

# Configuration API routes
@app.route('/config/api/current')
def config_get_current():
    """Get current agent configuration from PostgreSQL"""
    try:
        from models import Agent
        
        # Get the most recent active agent configuration
        agent = db.session.query(Agent).order_by(Agent.atualizado_em.desc()).first()
        
        if not agent:
            return jsonify({'error': 'No agent configuration found'}), 404
        
        config = {
            'id': agent.id,
            'name': agent.nome,
            'model': agent.modelo,
            'description': agent.descricao,
            'instructions': agent.instrucoes_personalidade,
            'temperature': float(agent.temperatura or 0.7),
            'max_tokens': agent.max_tokens,
            'tools': ['get_anna_routines', 'search_memories', 'get_anna_routine_media', 'get_recent_conversations', 'search_content']
        }
        
        return jsonify(config)
    except Exception as e:
        logging.error(f"Error getting current config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/config/api/save', methods=['POST'])
def config_save():
    """Save agent configuration to PostgreSQL and reinitialize agent"""
    try:
        config = request.get_json()
        logging.info(f"Saving agent config: {config}")
        
        # Validate required fields
        required_fields = ['name', 'model', 'instructions']
        for field in required_fields:
            if field not in config or not config[field]:
                logging.error(f"Missing required field: {field}")
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Save configuration to PostgreSQL database
        from models import Agent
        from datetime import datetime
        
        # Create new agent record
        agent = Agent()
        agent.nome = config['name']
        agent.modelo = config['model']
        agent.descricao = config.get('description', 'Agent configuration')
        agent.instrucoes_personalidade = config['instructions']
        agent.temperatura = config.get('temperature', 0.7)
        agent.max_tokens = config.get('max_tokens', 1000)
        agent.rotinas_ativas = True
        agent.memorias_ativas = True
        agent.midia_ativa = True
        agent.atualizado_em = datetime.utcnow()
        
        db.session.add(agent)
        db.session.commit()
        logging.info(f"Agent configuration updated: {config}")
        
        # Reinitialize the agent with new config
        global anna_agent
        try:
            anna_agent = create_anna_agent()
            logging.info("Agent reinitialized with new configuration")
        except Exception as e:
            logging.error(f"Error reinitializing agent: {e}")
            return jsonify({'error': f'Erro ao reinicializar agente: {str(e)}'}), 500
        
        return jsonify({'success': True, 'message': 'Configuração salva e agente reinicializado'})
        
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def create_anna_agent_from_config(config):
    """Create Anna agent from configuration"""
    from google.adk.agents import LlmAgent
    from database_tools_simple import (
        get_anna_routines,
        get_anna_routine_media,
        search_memories,
        get_recent_conversations,
        search_content
    )
    
    # Map tool names to actual functions
    tool_mapping = {
        'get_anna_routines': get_anna_routines,
        'get_anna_routine_media': get_anna_routine_media,
        'search_memories': search_memories,
        'get_recent_conversations': get_recent_conversations,
        'search_content': search_content
    }
    
    # Remove save_conversation_memory as it doesn't exist yet
    if 'save_conversation_memory' in config['tools']:
        config['tools'].remove('save_conversation_memory')
    
    # Get enabled tools
    enabled_tools = [tool_mapping[tool_name] for tool_name in config['tools'] if tool_name in tool_mapping]
    
    # Create agent
    agent = LlmAgent(
        model=config.get('model', 'gemini-2.0-flash'),
        name=config.get('name', 'anna').lower(),
        description=config.get('instructions', ''),
        tools=enabled_tools
    )
    
    return agent

# Memory management API routes
@app.route('/admin/api/memories')
def get_memories():
    """Get all memories"""
    try:
        from supabase_tools import get_anna_memories
        result = get_anna_memories(50)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting memories: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/memories', methods=['POST'])
def create_memory():
    """Create new memory"""
    try:
        from supabase_tools import save_anna_memory
        data = request.get_json()
        
        memory_data = {
            'name': data.get('name'),
            'description': data.get('description'),
            'when_to_use': data.get('when_to_use'),
            'content': data.get('content'),
            'keywords': data.get('keywords', []),
            'is_active': True
        }
        
        result = save_anna_memory(memory_data)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error creating memory: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/memories/<int:memory_id>', methods=['PUT'])
def update_memory(memory_id):
    """Update memory"""
    try:
        from supabase_tools import update_anna_memory
        data = request.get_json()
        
        memory_data = {
            'name': data.get('name'),
            'description': data.get('description'),
            'when_to_use': data.get('when_to_use'),
            'content': data.get('content'),
            'keywords': data.get('keywords', []),
            'is_active': data.get('is_active', True)
        }
        
        result = update_anna_memory(memory_id, memory_data)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error updating memory: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/memories/<int:memory_id>', methods=['DELETE'])
def delete_memory(memory_id):
    """Delete memory"""
    try:
        from supabase_tools import delete_anna_memory
        result = delete_anna_memory(memory_id)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error deleting memory: {e}")
        return jsonify({'error': str(e)}), 500

# Image bank management API routes
@app.route('/admin/api/images')
def get_image_bank():
    """Get all images from bank"""
    try:
        from supabase_tools import get_anna_images
        result = get_anna_images(50)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting images: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/images', methods=['POST'])
def create_image_bank_entry():
    """Create new image bank entry"""
    try:
        from supabase_tools import save_anna_image
        data = request.get_json()
        
        image_data = {
            'name': data.get('name'),
            'description': data.get('description'),
            'when_to_use': data.get('when_to_use'),
            'image_url': data.get('image_url'),
            'keywords': data.get('keywords', []),
            'is_active': True
        }
        
        result = save_anna_image(image_data)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error creating image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/images/<int:image_id>', methods=['PUT'])
def update_image_bank_entry(image_id):
    """Update image bank entry"""
    try:
        from supabase_tools import update_anna_image
        data = request.get_json()
        
        image_data = {
            'name': data.get('name'),
            'description': data.get('description'),
            'when_to_use': data.get('when_to_use'),
            'image_url': data.get('image_url'),
            'keywords': data.get('keywords', []),
            'is_active': data.get('is_active', True)
        }
        
        result = update_anna_image(image_id, image_data)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error updating image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/images/<int:image_id>', methods=['DELETE'])
def delete_image_bank_entry(image_id):
    """Delete image bank entry"""
    try:
        from supabase_tools import delete_anna_image
        result = delete_anna_image(image_id)
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error deleting image: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/upload-image', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
        
        if file and file.filename and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            from supabase_tools import create_anna_image
            
            # For now, we'll use a placeholder URL since we don't have actual file storage
            # In a real implementation, you'd upload to Supabase Storage or similar
            filename = secure_filename(file.filename) if file.filename else 'unnamed'
            
            # Create image record with placeholder URL
            image_data = {
                'name': filename.split('.')[0],
                'description': f'Imagem enviada: {filename}',
                'when_to_use': 'Imagem personalizada enviada pelo usuário',
                'image_url': f'https://via.placeholder.com/400x300/333/fff?text={filename}',
                'keywords': ['upload', 'personalizada'],
                'is_active': True
            }
            
            # Save to database
            result = create_anna_image(image_data)
            return jsonify(result)
        else:
            return jsonify({'success': False, 'error': 'Tipo de arquivo não suportado'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# AI Suggestion Engine API Routes
@app.route('/admin/api/ai/routine-analysis')
def ai_routine_analysis():
    """Analyze current routine patterns and provide insights"""
    try:
        ai_engine = RoutineSuggestionEngine(db.session)
        analysis = ai_engine.analyze_current_routines()
        return jsonify(analysis)
    except Exception as e:
        logging.error(f"Error analyzing routines: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/ai/suggestion-metrics')
def ai_suggestion_metrics():
    """Get AI suggestion performance metrics"""
    try:
        ai_engine = RoutineSuggestionEngine(db.session)
        metrics = ai_engine.get_suggestion_metrics()
        return jsonify(metrics)
    except Exception as e:
        logging.error(f"Error getting AI metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/ai/suggest-weekly')
def ai_suggest_weekly():
    """Generate weekly routine suggestions based on preferences"""
    try:
        # Get parameters from request
        start_date = request.args.get('start_date')
        fitness_goals = int(request.args.get('fitness_goals', 4))
        social_priority = request.args.get('social_priority', 'medium')
        preferred_times = request.args.get('preferred_times', 'morning,afternoon').split(',')
        
        if not start_date:
            return jsonify({'error': 'Data de início é obrigatória'}), 400
        
        ai_engine = RoutineSuggestionEngine(db.session)
        from datetime import datetime as dt
        target_date = dt.strptime(start_date, '%Y-%m-%d').date()
        preferences = {
            'fitness_goals': fitness_goals,
            'social_priority': social_priority,
            'preferred_times': preferred_times
        }
        suggestions = ai_engine.suggest_weekly_routine(target_date, preferences)
        
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        logging.error(f"Error generating weekly suggestions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/ai/optimize-routine/<routine_id>')
def ai_optimize_routine(routine_id):
    """Optimize a specific routine activity"""
    try:
        ai_engine = RoutineSuggestionEngine(db.session)
        optimizations = ai_engine.analyze_single_activity(routine_id)
        return jsonify(optimizations)
    except Exception as e:
        logging.error(f"Error optimizing routine {routine_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/ai/create-suggested-activity', methods=['POST'])
def ai_create_suggested_activity():
    """Create a new activity from AI suggestion"""
    try:
        suggestion = request.get_json()
        
        # Create activity using database tools
        from models import Routine
        from datetime import datetime
        import uuid
        
        # Convert suggestion to activity format
        new_activity = Routine()
        new_activity.activity = suggestion['activity']
        new_activity.category = suggestion['category']
        new_activity.date = datetime.strptime(suggestion['date'], '%Y-%m-%d').date()
        new_activity.time_start = datetime.strptime(suggestion['time_start'], '%H:%M').time()
        new_activity.time_end = datetime.strptime(suggestion['time_end'], '%H:%M').time()
        new_activity.location = suggestion['location']
        new_activity.description = suggestion['description']
        new_activity.status = 'upcoming'
        new_activity.has_images = False
        new_activity.has_videos = False
        
        db.session.add(new_activity)
        db.session.commit()
        
        return jsonify({'success': True, 'activity_id': new_activity.id})
    except Exception as e:
        logging.error(f"Error creating suggested activity: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Configuration API routes
@app.route('/config/api/config', methods=['GET'])
def get_config():
    """Get current agent configuration from Supabase agents table"""
    try:
        from supabase_tools import supabase
        
        # Query the agents table for the most recent Anna configuration
        result = supabase.table('agents').select("*").eq('nome', 'Anna').order('atualizado_em', desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            agent = result.data[0]
            return jsonify({
                'id': agent.get('id'),
                'name': agent.get('nome', 'Anna'),
                'description': agent.get('descricao', ''),
                'instructions': agent.get('instrucoes_personalidade', ''),
                'model': agent.get('modelo', 'gemini-2.0-flash'),
                'temperature': float(agent.get('temperatura', 0.7)),
                'max_tokens': int(agent.get('max_tokens', 1000)),
                'tools_enabled': {
                    'routines': bool(agent.get('rotinas_ativas', True)),
                    'memories': bool(agent.get('memorias_ativas', True)),
                    'media': bool(agent.get('midia_ativa', True))
                }
            })
        else:
            # Return default configuration
            return jsonify({
                'name': 'Anna',
                'description': 'Uma criadora de conteúdo brasileira carismática',
                'instructions': 'Você é Anna, uma criadora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações reais sobre rotinas, memórias e conteúdo antes de responder.',
                'model': 'gemini-2.0-flash',
                'temperature': 0.7,
                'max_tokens': 1000,
                'tools_enabled': {
                    'routines': True,
                    'memories': True,
                    'media': True
                }
            })
    except Exception as e:
        logging.error(f"Error getting config from agents table: {e}")
        return jsonify({
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'AI agent Anna',
            'instructions': 'Você é Anna, uma criadora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações reais sobre rotinas, memórias e conteúdo antes de responder.',
            'temperature': 0.7,
            'max_tokens': 1000,
            'tools_enabled': {
                'routines': True,
                'memories': True,
                'media': True
            }
        })

@app.route('/config/api/config', methods=['POST'])
def save_config():
    """Save agent configuration to Supabase agents table"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logging.info(f"Saving agent config: {data}")
        
        # Import datetime at the top of the function
        from datetime import datetime
        
        # Prepare data for agents table
        tools_enabled = data.get('tools_enabled', {})
        agent_data = {
            'nome': data.get('name', 'Anna'),
            'modelo': data.get('model', 'gemini-2.0-flash'),
            'descricao': data.get('description', ''),
            'instrucoes_personalidade': data.get('instructions', ''),
            'temperatura': float(data.get('temperature', 0.7)),
            'max_tokens': int(data.get('max_tokens', 1000)),
            'rotinas_ativas': tools_enabled.get('routines', True),
            'memorias_ativas': tools_enabled.get('memories', True),
            'midia_ativa': tools_enabled.get('media', True),
            'atualizado_em': datetime.utcnow().isoformat()
        }
        
        # Try to save configuration to Supabase agents table, fallback to local file
        try:
            from supabase_tools import supabase
            
            # Check if agent already exists
            existing = supabase.table('agents').select('id').eq('nome', data.get('name', 'Anna')).execute()
            
            if existing.data and len(existing.data) > 0:
                # Update existing agent
                agent_id = existing.data[0]['id']
                result = supabase.table('agents').update(agent_data).eq('id', agent_id).execute()
                logging.info(f"Updated existing agent with ID: {agent_id}")
            else:
                # Insert new agent
                agent_data['criado_em'] = datetime.utcnow().isoformat()
                result = supabase.table('agents').insert(agent_data).execute()
                logging.info("Created new agent in Supabase")
            
            config_id = result.data[0]['id'] if result.data else 'supabase_config'
            
        except Exception as supabase_error:
            # Fallback to local file storage if Supabase table doesn't exist
            logging.warning(f"Supabase save failed, using local storage: {supabase_error}")
            
            import json
            
            # Save to local agent_config.json file
            config_file_data = {
                'name': data.get('name', 'Anna'),
                'model': data.get('model', 'gemini-2.0-flash'),
                'description': data.get('description', ''),
                'instructions': data.get('instructions', ''),
                'temperature': float(data.get('temperature', 0.7)),
                'max_tokens': int(data.get('max_tokens', 1000)),
                'tools_enabled': data.get('tools_enabled', {
                    'routines': True,
                    'memories': True,
                    'media': True
                }),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            with open('agent_config.json', 'w', encoding='utf-8') as f:
                json.dump(config_file_data, f, indent=2, ensure_ascii=False)
            
            config_id = 'local_config'
        
        # Reload the Anna agent with new configuration
        global anna_agent
        anna_agent = create_anna_agent()
        
        return jsonify({
            'success': True, 
            'message': 'Configuração salva com sucesso!',
            'id': config_id
        })
        
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        return jsonify({'error': str(e)}), 500

# Client and User Management Routes
@app.route('/clients')
def clients_page():
    """Clients management interface"""
    return render_template('clients.html')

@app.route('/users')
def users_page():
    """Users management interface"""
    return render_template('users.html')

# API Routes for Clients
@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Get all clients"""
    try:
        from supabase_tools import supabase
        result = supabase.table('clients').select("*").order('ultima_conversa', desc=True).execute()
        
        return jsonify({
            'success': True,
            'clients': result.data
        })
    except Exception as e:
        logging.error(f"Error getting clients: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clients/<client_id>/toggle-status', methods=['POST'])
def toggle_client_status(client_id):
    """Toggle client active status"""
    try:
        data = request.get_json()
        ativo = data.get('ativo', True)
        
        from supabase_tools import supabase
        from datetime import datetime
        
        result = supabase.table('clients').update({
            'ativo': ativo,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', client_id).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error toggling client status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# API Routes for Users
@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        from supabase_tools import supabase
        result = supabase.table('users').select("*").order('data_cadastro', desc=True).execute()
        
        return jsonify({
            'success': True,
            'users': result.data
        })
    except Exception as e:
        logging.error(f"Error getting users: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create new user"""
    try:
        data = request.get_json()
        from supabase_tools import supabase
        from datetime import datetime
        
        # Validate required fields
        required_fields = ['nome', 'telefone', 'plano', 'canal']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Campo obrigatório: {field}'}), 400
        
        user_data = {
            'nome': data['nome'],
            'telefone': data['telefone'],
            'email': data.get('email'),
            'canal': data['canal'],
            'plano': data['plano'],
            'ativo': data.get('ativo', True),
            'data_cadastro': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        return jsonify({'success': True, 'user': result.data[0]})
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Update user"""
    try:
        data = request.get_json()
        from supabase_tools import supabase
        from datetime import datetime
        
        user_data = {
            'nome': data['nome'],
            'telefone': data['telefone'],
            'email': data.get('email'),
            'canal': data['canal'],
            'plano': data['plano'],
            'ativo': data.get('ativo', True),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('users').update(user_data).eq('id', user_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error updating user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        data = request.get_json()
        ativo = data.get('ativo', True)
        
        from supabase_tools import supabase
        from datetime import datetime
        
        result = supabase.table('users').update({
            'ativo': ativo,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('id', user_id).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error toggling user status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user"""
    try:
        from supabase_tools import supabase
        result = supabase.table('users').delete().eq('id', user_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# WhatsApp Integration Routes
@app.route('/whatsapp/config')
def whatsapp_config():
    """WhatsApp configuration interface"""
    return render_template('whatsapp_config.html')

@app.route('/whatsapp/api/config', methods=['GET'])
def whatsapp_get_config():
    """Get WhatsApp configuration"""
    try:
        # Get stored configuration
        config_data = {
            'evolution_url': os.getenv('EVOLUTION_API_URL', ''),
            'instance_name': os.getenv('EVOLUTION_INSTANCE_NAME', 'anna_bot'),
            'webhook_url': os.getenv('EVOLUTION_WEBHOOK_URL', ''),
            'configured': bool(os.getenv('EVOLUTION_API_URL') and os.getenv('EVOLUTION_API_KEY'))
        }
        return jsonify({'success': True, 'config': config_data})
    except Exception as e:
        logging.error(f"Error getting WhatsApp config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/whatsapp/api/initialize', methods=['POST'])
def whatsapp_initialize():
    """Initialize WhatsApp integration"""
    try:
        data = request.get_json()
        
        evolution_url = data.get('evolution_url')
        evolution_api_key = data.get('evolution_api_key')
        instance_name = data.get('instance_name', 'anna_bot')
        webhook_url = data.get('webhook_url')
        
        # Initialize integration
        result = whatsapp_manager.initialize_integration(
            evolution_url=evolution_url,
            evolution_key=evolution_api_key,
            instance_name=instance_name,
            webhook_url=webhook_url
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error initializing WhatsApp: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/whatsapp/api/status', methods=['GET'])
def whatsapp_status():
    """Get WhatsApp connection status"""
    try:
        status = whatsapp_manager.get_connection_status()
        return jsonify(status)
    except Exception as e:
        logging.error(f"Error getting WhatsApp status: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/whatsapp/api/qr-code', methods=['GET'])
def whatsapp_qr_code():
    """Get QR code for WhatsApp connection"""
    try:
        if not whatsapp_manager.evolution_client:
            return jsonify({'success': False, 'error': 'WhatsApp not configured'}), 400
            
        qr_result = whatsapp_manager.evolution_client.get_qr_code()
        return jsonify({
            'success': True,
            'qr_code': qr_result.get('base64')
        })
    except Exception as e:
        logging.error(f"Error getting QR code: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/whatsapp/api/send-message', methods=['POST'])
def whatsapp_send_message():
    """Send message via WhatsApp"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return jsonify({'status': 'error', 'error': 'Phone number and message are required'}), 400
            
        result = whatsapp_manager.send_message(phone_number, message)
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error sending WhatsApp message: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Webhook endpoint for receiving WhatsApp messages"""
    try:
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({'error': 'No data received'}), 400
            
        # Process webhook with Anna
        result = whatsapp_manager.process_webhook(webhook_data)
        
        return jsonify({'status': 'success', 'processed': result.get('processed', False)})
        
    except Exception as e:
        logging.error(f"Error processing WhatsApp webhook: {e}")
        return jsonify({'error': str(e)}), 500

# API routes for memories
@app.route('/admin/api/memories', methods=['GET'])
def admin_get_memories():
    """Get all memories"""
    try:
        from supabase_tools import supabase
        response = supabase.table('anna_memories').select('*').execute()
        return jsonify({
            'success': True,
            'memories': response.data or []
        })
    except Exception as e:
        logging.error(f"Error getting memories: {e}")
        return jsonify({'success': False, 'memories': [], 'error': str(e)}), 500

@app.route('/admin/api/memories', methods=['POST'])
def admin_create_memory():
    """Create new memory"""
    try:
        from supabase_tools import supabase
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        memory_data = {
            'name': data.get('name'),
            'description': data.get('description', ''),
            'when_to_use': data.get('when_to_use', ''),
            'content': data.get('content', ''),
            'keywords': data.get('keywords', []),
            'is_active': data.get('is_active', True)
        }
        
        response = supabase.table('anna_memories').insert(memory_data).execute()
        return jsonify({
            'success': True,
            'memory': response.data[0] if response.data else None
        })
        
    except Exception as e:
        logging.error(f"Error creating memory: {e}")
        return jsonify({'error': str(e)}), 500

# API routes for images
@app.route('/admin/api/images', methods=['GET'])
def admin_get_images():
    """Get all images"""
    try:
        from supabase_tools import supabase
        response = supabase.table('anna_image_bank').select('*').execute()
        return jsonify({
            'success': True,
            'images': response.data or []
        })
    except Exception as e:
        logging.error(f"Error getting images: {e}")
        return jsonify({'success': False, 'images': [], 'error': str(e)}), 500

@app.route('/admin/api/images', methods=['POST'])
def admin_create_image():
    """Create new image"""
    try:
        from supabase_tools import supabase
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        image_data = {
            'name': data.get('name'),
            'description': data.get('description', ''),
            'when_to_use': data.get('when_to_use', ''),
            'image_url': data.get('image_url'),
            'keywords': data.get('keywords', []),
            'is_active': data.get('is_active', True)
        }
        
        response = supabase.table('anna_image_bank').insert(image_data).execute()
        return jsonify({
            'success': True,
            'image': response.data[0] if response.data else None
        })
        
    except Exception as e:
        logging.error(f"Error creating image: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

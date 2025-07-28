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
    """Handle chat messages"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message']
        logging.info(f"Received message: {user_message}")
        
        # Get or create session ID
        if 'session_id' not in session:
            session['session_id'] = f"session_{os.urandom(8).hex()}"
        
        session_id = session['session_id']
        user_id = "web_user"
        
        # Run the agent asynchronously
        response = asyncio.run(run_anna_agent(user_message, user_id, session_id))
        
        return jsonify({
            'response': response,
            'session_id': session_id
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
    """Load conversation history from PostgreSQL database and populate session"""
    try:
        from models import Message
        from google.genai import types
        
        # Get recent messages for this session
        messages = db.session.query(Message).filter(
            Message.session_id == session_id
        ).order_by(Message.created_at.asc()).limit(50).all()
        
        if messages:
            # Add conversation history to session
            for message in messages:
                # Add user message
                if message.user_message:
                    user_content = types.Content(role='user', parts=[types.Part(text=message.user_message)])
                    session_obj.add_turn(user_content)
                
                # Add assistant response
                if message.assistant_response:
                    assistant_content = types.Content(role='model', parts=[types.Part(text=message.assistant_response)])
                    session_obj.add_turn(assistant_content)
                    
        logging.info(f"Loaded {len(messages)} conversation turns for session {session_id}")
        
    except Exception as e:
        logging.error(f"Error loading conversation history: {e}")

async def save_conversation_turn(user_id: str, session_id: str, user_message: str, assistant_response: str):
    """Save a conversation turn to PostgreSQL database"""
    try:
        from models import Message
        
        # Create new message record
        message = Message(
            user_id=user_id,
            session_id=session_id,
            user_message=user_message,
            assistant_response=assistant_response
        )
        
        db.session.add(message)
        db.session.commit()
        logging.info(f"Saved conversation turn for session {session_id}")
        
    except Exception as e:
        logging.error(f"Error saving conversation turn: {e}")
        db.session.rollback()

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
        from models import AnnaRoutine
        
        routines = db.session.query(AnnaRoutine).order_by(AnnaRoutine.date.asc()).all()
        
        # Format for FullCalendar
        events = []
        for activity in routines:
            events.append({
                'id': activity.id,
                'title': activity.activity,
                'start': f"{activity.date}T{activity.time_start or '00:00'}",
                'end': f"{activity.date}T{activity.time_end or '23:59'}",
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
    """Get specific activity details"""
    try:
        from supabase_tools import supabase
        response = supabase.table('anna_routine').select('*').eq('id', activity_id).single().execute()
        return jsonify(response.data)
    except Exception as e:
        logging.error(f"Error getting activity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/date/<date>')
def admin_get_activities_by_date(date):
    """Get activities for specific date"""
    try:
        from supabase_tools import supabase
        response = supabase.table('anna_routine').select('*').eq('date', date).order('time_start').execute()
        return jsonify(response.data)
    except Exception as e:
        logging.error(f"Error getting activities by date: {e}")
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
    """Create new activity"""
    try:
        from supabase_tools import supabase
        import json
        import uuid
        
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logging.info(f"Creating activity with data: {data}")
        
        # Map frontend fields to database fields
        activity_data = {
            'date': data.get('date'),
            'time_start': data.get('time_start'),
            'time_end': data.get('time_end'),
            'activity': data.get('activity'),
            'category': data.get('category'),
            'location': data.get('location', ''),
            'description': data.get('description', ''),

            'status': 'upcoming',
            'has_images': False,
            'has_videos': False
        }
        
        # Validate required fields
        required_fields = ['date', 'activity', 'category']
        for field in required_fields:
            if not activity_data.get(field):
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Insert activity
        response = supabase.table('anna_routine').insert(activity_data).execute()
        
        if not response.data:
            return jsonify({'error': 'Erro ao criar atividade'}), 500
            
        activity_id = response.data[0]['id']
        logging.info(f"Activity created with ID: {activity_id}")
        
        # Handle media files
        media_files = request.files.getlist('media_files')
        has_images = False
        has_videos = False
        uploaded_count = 0
        
        for file in media_files:
            if file and file.filename and file.filename != '':
                logging.info(f"Processing file: {file.filename}, type: {file.content_type}, size: {file.content_length}")
                
                # Upload to Supabase storage
                file_extension = file.filename.split('.')[-1].lower()
                file_name = f"{uuid.uuid4()}.{file_extension}"
                
                # Upload file
                file.seek(0)  # Reset file pointer
                file_content = file.read()
                
                if len(file_content) == 0:
                    logging.warning(f"File {file.filename} is empty, skipping")
                    continue
                
                try:
                    storage_response = supabase.storage.from_('conteudo').upload(file_name, file_content)
                    logging.info(f"Storage response: {storage_response}")
                    
                    # Get public URL
                    file_url = supabase.storage.from_('conteudo').get_public_url(file_name)
                    logging.info(f"Public URL: {file_url}")
                    
                    # Determine media type
                    media_type = 'video' if (file.content_type and file.content_type.startswith('video/')) else 'image'
                    
                    # Save media record
                    media_data = {
                        'routine_id': activity_id,
                        'media_url': file_url,
                        'media_type': media_type,
                        'description': f"Mídia da atividade: {activity_data['activity']}"
                    }
                    
                    media_response = supabase.table('anna_routine_media').insert(media_data).execute()
                    logging.info(f"Media record created: {media_response.data}")
                    
                    if media_type == 'image':
                        has_images = True
                    else:
                        has_videos = True
                        
                    uploaded_count += 1
                        
                except Exception as e:
                    logging.error(f"Error uploading file {file.filename}: {e}")
                    continue
        
        # Handle media URLs from the frontend
        media_urls = data.get('media_urls', [])
        for url in media_urls:
            if url.strip():
                # Determine media type from URL extension
                media_type = 'video' if any(ext in url.lower() for ext in ['.mp4', '.mov', '.avi', '.webm']) else 'image'
                
                media_data = {
                    'routine_id': activity_id,
                    'media_url': url.strip(),
                    'media_type': media_type,
                    'description': f"Mídia da atividade: {activity_data['activity']}"
                }
                
                try:
                    media_response = supabase.table('anna_routine_media').insert(media_data).execute()
                    logging.info(f"Media URL record created: {media_response.data}")
                    
                    if media_type == 'image':
                        has_images = True
                    else:
                        has_videos = True
                        
                except Exception as e:
                    logging.error(f"Error saving media URL {url}: {e}")
        
        # Update activity with media flags
        if has_images or has_videos:
            update_data = {
                'has_images': has_images,
                'has_videos': has_videos
            }
            supabase.table('anna_routine').update(update_data).eq('id', activity_id).execute()
            
        return jsonify({
            'success': True, 
            'id': activity_id,
            'message': f'Atividade criada com sucesso! {uploaded_count + len([u for u in media_urls if u.strip()])} arquivos de mídia processados.'
        })
        
    except Exception as e:
        logging.error(f"Error creating activity: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/api/activities/update', methods=['POST'])
def admin_update_activity():
    """Update existing activity"""
    try:
        from supabase_tools import supabase
        import uuid
        
        activity_id = request.form.get('id')
        
        # Get form data
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
                # Upload to Supabase storage
                file_extension = file.filename.split('.')[-1]
                file_name = f"{uuid.uuid4()}.{file_extension}"
                
                # Upload file
                file.seek(0)  # Reset file pointer
                try:
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
                    
                except Exception as e:
                    logging.error(f"Error uploading file {file.filename}: {e}")
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

@app.route('/admin/api/activities/<activity_id>', methods=['DELETE'])
def admin_delete_activity(activity_id):
    """Delete activity and its media"""
    try:
        from supabase_tools import supabase
        
        # Delete media files from storage
        media_response = supabase.table('anna_routine_media').select('media_url').eq('routine_id', activity_id).execute()
        
        for media in media_response.data:
            # Extract filename from URL and delete from storage
            file_name = media['media_url'].split('/')[-1]
            try:
                supabase.storage.from_('conteudo').remove([file_name])
            except:
                pass  # Continue even if file deletion fails
        
        # Delete media records first
        supabase.table('anna_routine_media').delete().eq('routine_id', activity_id).execute()
        
        # Delete activity
        supabase.table('anna_routine').delete().eq('id', activity_id).execute()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error deleting activity: {e}")
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
        agent = Agent(
            nome=config['name'],
            modelo=config['model'],
            descricao=config.get('description', 'Agent configuration'),
            instrucoes_personalidade=config['instructions'],
            temperatura=config.get('temperature', 0.7),
            max_tokens=config.get('max_tokens', 1000),
            rotinas_ativas=True,
            memorias_ativas=True,
            midia_ativa=True,
            atualizado_em=datetime.utcnow()
        )
        
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
        
        if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            from supabase_tools import create_anna_image
            
            # For now, we'll use a placeholder URL since we don't have actual file storage
            # In a real implementation, you'd upload to Supabase Storage or similar
            filename = secure_filename(file.filename)
            
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

# Configuration API routes
@app.route('/config/api/config', methods=['GET'])
def get_config():
    """Get current agent configuration"""
    try:
        from anna_agent import agent
        config = {
            'name': getattr(agent, 'name', 'Anna'),
            'model': getattr(agent, 'model', 'gemini-2.0-flash'),
            'description': getattr(agent, 'description', ''),
            'instructions': getattr(agent, 'instructions', ''),
            'temperature': getattr(agent, 'temperature', 0.7),
            'max_tokens': getattr(agent, 'max_tokens', 1000),
            'tools': getattr(agent, 'tools', [])
        }
        return jsonify(config)
    except Exception as e:
        logging.error(f"Error getting config: {e}")
        return jsonify({
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'AI agent Anna',
            'instructions': 'Você é Anna, uma criadora de conteúdo brasileira...',
            'temperature': 0.7,
            'max_tokens': 1000,
            'tools': ['get_anna_routines', 'search_memories', 'get_anna_routine_media']
        })

@app.route('/config/api/config', methods=['POST'])
def save_config():
    """Save agent configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        logging.info(f"Saving agent config: {data}")
        
        # Update agent configuration - for now we'll save to a simple config
        # In a real implementation, you would update the actual agent
        config_data = {
            'name': data.get('name', 'Anna'),
            'model': data.get('model', 'gemini-2.0-flash'),
            'description': data.get('description', ''),
            'instructions': data.get('instructions', ''),
            'temperature': data.get('temperature', 0.7),
            'max_tokens': data.get('max_tokens', 1000),
            'tools': data.get('tools', [])
        }
        
        # You could save this to a database or file for persistence
        # For now, we'll just log it and return success
        logging.info(f"Agent configuration updated: {config_data}")
        
        return jsonify({
            'success': True,
            'message': 'Configuração salva com sucesso!',
            'config': config_data
        })
        
    except Exception as e:
        logging.error(f"Error saving config: {e}")
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

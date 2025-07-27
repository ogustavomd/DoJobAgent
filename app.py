import os
import logging
import asyncio
from flask import Flask, render_template, request, jsonify, session
from werkzeug.middleware.proxy_fix import ProxyFix
from anna_agent import create_anna_agent
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize Anna agent
anna_agent = None

def init_agent():
    """Initialize Anna agent"""
    global anna_agent
    try:
        anna_agent = create_anna_agent()
        logging.info("Anna agent initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Anna agent: {e}")
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
        
        # Create runner
        runner = Runner(agent=anna_agent, app_name="anna_chat", session_service=session_service)
        
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
        
        return final_response or "Desculpe, não consegui processar sua mensagem no momento."
        
    except Exception as e:
        logging.error(f"Error running Anna agent: {e}")
        return "Desculpe, ocorreu um erro interno. Tente novamente em alguns instantes."

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
    """Get all activities for calendar display"""
    try:
        from supabase_tools import supabase
        response = supabase.table('anna_routine').select('*').order('date', desc=False).execute()
        
        # Format for FullCalendar
        events = []
        for activity in response.data:
            events.append({
                'id': activity['id'],
                'title': activity['activity'],
                'start': f"{activity['date']}T{activity['time_start']}",
                'end': f"{activity['date']}T{activity['time_end']}",
                'className': f"fc-event-{activity['category']}",
                'extendedProps': {
                    'category': activity['category'],
                    'status': activity['status'],
                    'location': activity.get('location'),
                    'description': activity.get('description'),
                    'has_images': activity.get('has_images', False),
                    'has_videos': activity.get('has_videos', False)
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
        import uuid
        
        logging.info(f"Creating activity with form data: {dict(request.form)}")
        logging.info(f"Media files received: {len(request.files.getlist('media_files'))}")
        
        # Get form data
        activity_data = {
            'date': request.form.get('date'),
            'time_start': request.form.get('time_start'),
            'time_end': request.form.get('time_end'),
            'activity': request.form.get('activity'),
            'category': request.form.get('category'),
            'location': request.form.get('location'),
            'description': request.form.get('description'),
            'status': 'upcoming',
            'has_images': False,
            'has_videos': False
        }
        
        # Validate required fields
        required_fields = ['date', 'time_start', 'time_end', 'activity', 'category']
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
                    media_type = 'video' if file.content_type and file.content_type.startswith('video/') else 'image'
                    
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
        
        # Update activity with media flags
        if has_images or has_videos:
            update_response = supabase.table('anna_routine').update({
                'has_images': has_images,
                'has_videos': has_videos
            }).eq('id', activity_id).execute()
            logging.info(f"Activity updated with media flags: {update_response.data}")
        
        logging.info(f"Activity creation completed. Uploaded {uploaded_count} files.")
        return jsonify({
            'success': True, 
            'id': activity_id, 
            'uploaded_files': uploaded_count,
            'has_images': has_images,
            'has_videos': has_videos
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
                    media_type = 'video' if file.content_type.startswith('video/') else 'image'
                    
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
    """Get current agent configuration"""
    try:
        # This would normally load from a config file or database
        # For now, return default configuration based on current agent
        config = {
            'name': 'Anna',
            'model': 'gemini-2.0-flash',
            'description': 'Uma criadora de conteúdo brasileira carismática e autêntica que compartilha sua rotina diária.',
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
                'search_content',
                'save_conversation_memory'
            ],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        return jsonify(config)
    except Exception as e:
        logging.error(f"Error getting current config: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/config/api/save', methods=['POST'])
def config_save():
    """Save agent configuration and reinitialize agent"""
    try:
        config = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'model', 'instructions', 'tools']
        for field in required_fields:
            if field not in config or not config[field]:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Save configuration to file (in production, this would be a database)
        config_file = 'agent_config.json'
        import json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Reinitialize the agent with new config
        global anna_agent
        try:
            anna_agent = create_anna_agent_from_config(config)
            logging.info("Agent reinitialized with new configuration")
        except Exception as e:
            logging.error(f"Error reinitializing agent: {e}")
            return jsonify({'error': f'Erro ao reinicializar agente: {str(e)}'}), 500
        
        return jsonify({'success': True, 'message': 'Configuração salva e agente reinicializado'})
        
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        return jsonify({'error': str(e)}), 500

def create_anna_agent_from_config(config):
    """Create Anna agent from configuration"""
    from google.adk.agents import LlmAgent
    from supabase_tools import (
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
    
    # Import save_conversation_memory if it exists
    try:
        from supabase_tools import save_conversation_memory
        tool_mapping['save_conversation_memory'] = save_conversation_memory
    except ImportError:
        # Remove from available tools if function doesn't exist
        if 'save_conversation_memory' in config['tools']:
            config['tools'].remove('save_conversation_memory')
    
    # Get enabled tools
    enabled_tools = [tool_mapping[tool_name] for tool_name in config['tools'] if tool_name in tool_mapping]
    
    # Create agent
    agent = LlmAgent(
        model=config.get('model', 'gemini-2.0-flash'),
        name=config.get('name', 'anna').lower(),
        instructions=config.get('instructions', ''),
        tools=enabled_tools
    )
    
    return agent

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

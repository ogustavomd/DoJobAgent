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

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'agent_initialized': anna_agent is not None})

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

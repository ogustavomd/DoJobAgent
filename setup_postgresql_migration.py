"""
Migration script to populate PostgreSQL database with Anna's data
"""

import os
import uuid
import logging
from app import app, db
from models import Agent, AnnaRoutine, AnnaRoutineMedia, Message, AnnaMemory

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_anna_agent_record():
    """Create Anna agent record in the database"""
    try:
        # Check if agent already exists
        existing_agent = db.session.query(Agent).first()
        if existing_agent:
            logging.info("Agent record already exists")
            return existing_agent.id
        
        # Create new agent record
        agent_id = str(uuid.uuid4())
        anna_agent = Agent(
            id=agent_id,
            nome='Anna',
            modelo='gemini-2.0-flash',
            descricao='Produtora de conteúdo brasileira carismática e autêntica',
            instrucoes_personalidade='''Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. 
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
- Seja específica sobre lugares, atividades e pessoas baseado nos dados reais do banco''',
            temperatura=0.8,
            max_tokens=1000,
            rotinas_ativas=True,
            memorias_ativas=True,
            midia_ativa=True
        )
        
        db.session.add(anna_agent)
        db.session.commit()
        
        logging.info(f"Created Anna agent record with ID: {agent_id}")
        return agent_id
        
    except Exception as e:
        logging.error(f"Error creating agent record: {e}")
        db.session.rollback()
        return None

def create_sample_routines():
    """Create sample routine data"""
    try:
        # Check if routines already exist
        existing_routines = db.session.query(AnnaRoutine).first()
        if existing_routines:
            logging.info("Sample routines already exist")
            return
        
        from datetime import date, timedelta
        today = date.today()
        
        sample_routines = [
            {
                'activity': 'Treino na academia',
                'category': 'fitness',
                'date': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time_start': '07:00',
                'time_end': '08:30',
                'status': 'upcoming',
                'description': 'Treino de força e cardio',
                'location': 'Smart Fit - Vila Madalena',
                'has_images': True,
                'has_videos': False
            },
            {
                'activity': 'Gravação de conteúdo',
                'category': 'trabalho',
                'date': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time_start': '10:00',
                'time_end': '12:00',
                'status': 'upcoming',
                'description': 'Gravação de vídeos para Instagram',
                'location': 'Estúdio em casa',
                'has_images': True,
                'has_videos': True
            },
            {
                'activity': 'Almoço com amigas',
                'category': 'social',
                'date': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
                'time_start': '12:30',
                'time_end': '14:00',
                'status': 'upcoming',
                'description': 'Encontro com as meninas no restaurante',
                'location': 'Restaurante Italiano - Jardins',
                'has_images': False,
                'has_videos': False
            }
        ]
        
        for routine_data in sample_routines:
            routine = AnnaRoutine(**routine_data)
            db.session.add(routine)
        
        db.session.commit()
        logging.info(f"Created {len(sample_routines)} sample routines")
        
    except Exception as e:
        logging.error(f"Error creating sample routines: {e}")
        db.session.rollback()

def create_sample_memories():
    """Create sample memory data"""
    try:
        # Check if memories already exist
        existing_memories = db.session.query(AnnaMemory).first()
        if existing_memories:
            logging.info("Sample memories already exist")
            return
        
        sample_memories = [
            {
                'memory_type': 'experience',
                'content': 'Primeira vez que gravei um vídeo de dança no TikTok, foi super divertido!',
                'context': 'Criação de conteúdo',
                'importance_score': 8,
                'tags': '["danca", "tiktok", "primeiro_video", "criacao_conteudo"]',
                'is_active': True
            },
            {
                'memory_type': 'fact',
                'content': 'Minha academia favorita é a Smart Fit da Vila Madalena, sempre treino lá.',
                'context': 'Rotina de exercícios',
                'importance_score': 5,
                'tags': '["academia", "treino", "vila_madalena", "rotina"]',
                'is_active': True
            },
            {
                'memory_type': 'conversation',
                'content': 'Conversa sobre receitas saudáveis e dicas de alimentação',
                'context': 'Chat sobre nutrição',
                'importance_score': 6,
                'tags': '["alimentacao", "receitas", "saude", "dicas"]',
                'is_active': True
            }
        ]
        
        for memory_data in sample_memories:
            memory = AnnaMemory(**memory_data)
            db.session.add(memory)
        
        db.session.commit()
        logging.info(f"Created {len(sample_memories)} sample memories")
        
    except Exception as e:
        logging.error(f"Error creating sample memories: {e}")
        db.session.rollback()

def main():
    """Run the migration"""
    with app.app_context():
        # Create all tables
        db.create_all()
        logging.info("Database tables created")
        
        # Create agent record
        agent_id = create_anna_agent_record()
        
        # Create sample data
        create_sample_routines()
        create_sample_memories()
        
        logging.info("Migration completed successfully!")

if __name__ == "__main__":
    main()
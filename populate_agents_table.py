import logging
from app import app, db
from models import Agent

def populate_agents():
    """Populate the agents table with a default agent"""
    try:
        with app.app_context():
            print("Populating agents table...")
            
            # Check if agent already exists
            agent_exists = db.session.query(Agent).filter_by(nome='Anna').first()
            if agent_exists:
                print("✓ Default agent 'Anna' already exists")
                return True

            default_agent = Agent(
                nome='Anna',
                modelo='gemini-2.0-flash',
                descricao='AI agent Anna',
                instrucoes_personalidade='Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica.',
                temperatura=0.7,
                max_tokens=1000,
                rotinas_ativas=True,
                memorias_ativas=True,
                midia_ativa=True
            )
            db.session.add(default_agent)
            db.session.commit()
            print("✓ Default agent 'Anna' created successfully")
            return True
    except Exception as e:
        print(f"✗ Error populating agents table: {e}")
        return False

def main():
    """Main setup function"""
    print("Populating agents table...")
    
    success = populate_agents()
    
    if success:
        print("\n✓ Agents table populated successfully!")
        with app.app_context():
            agents = db.session.query(Agent).all()
            print("\nAgents in database:")
            for agent in agents:
                print(f"- {agent.nome}")
    else:
        print("\n✗ Agents table population failed")
    
    return success

if __name__ == "__main__":
    main()

import os
import json
import logging
from google.adk.agents import LlmAgent
from google.genai import types
from database_tools_simple import (get_anna_routines, get_anna_routine_media,
                            search_memories, get_recent_conversations,
                            get_profile_info, search_content,
                            save_conversation_memory)


def create_anna_agent():
    """Create and configure Anna agent using configuration from database and file"""
    try:
        # First try to load from database (latest saved from config interface)
        from database_tools_simple import get_active_agent_configuration
        config = get_active_agent_configuration()
        
        if config and config.get('instructions'):
            logging.info("Configuration loaded from database (most recent)")
        else:
            # Fallback to file if no database config
            with open('agent_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.info("Configuration loaded from agent_config.json file")
            
    except Exception as e:
        logging.error(f"Error loading config, using defaults: {e}")
        # Fallback configuration
        config = {
            'name': 'Anna', 
            'model': 'gemini-2.0-flash',
            'instructions': 'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações do banco de dados antes de responder.',
            'tools': ['get_anna_routines', 'search_memories', 'get_anna_routine_media', 'get_recent_conversations', 'search_content', 'save_conversation_memory']
        }

    # Get instructions from config (prioritizing database saved instructions)
    instructions = config.get('instructions')
    if not instructions:
        instructions = 'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações do banco de dados antes de responder.'
    
    logging.info(f"Using instructions (first 100 chars): {instructions[:100]}...")
    
    # Create the agent with tools from configuration
    agent = LlmAgent(
        model=config.get('model', 'gemini-2.0-flash'),
        name=config.get('name', 'Anna').lower(),
        description="Anna é uma produtora de conteúdo brasileira que interage de forma natural e carismática, compartilhando sua rotina, memórias e criações.",
        instruction=instructions,
        tools=[
            get_anna_routines, get_anna_routine_media, search_memories,
            get_recent_conversations, get_profile_info, search_content,
            save_conversation_memory
        ],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.8,  # More creative and spontaneous
            max_output_tokens=1000))

    logging.info("Anna agent created successfully")
    return agent


# Function to dynamically reload agent with new instructions
def reload_agent_with_instructions(new_instructions):
    """Reload agent with new instructions"""
    try:
        with open('agent_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        config['instructions'] = new_instructions
        
        with open('agent_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logging.error(f"Error updating instructions: {e}")
        return False
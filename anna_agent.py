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
    """Create and configure Anna agent using configuration from Supabase or database and file"""
    try:
        config = None
        
        # First try to load from Supabase agent_config table
        try:
            from supabase_tools import supabase
            result = supabase.table('agent_config').select("*").eq('is_active', True).eq('name', 'Anna').order('created_at', desc=True).limit(1).execute()
            
            if result.data and len(result.data) > 0:
                config = result.data[0]
                logging.info("Configuration loaded from Supabase agent_config")
        except Exception as e:
            logging.error(f"Error loading from Supabase: {e}")
        
        # If no config from Supabase, try PostgreSQL agents table
        if not config:
            try:
                from database_tools_simple import get_active_agent_configuration
                config = get_active_agent_configuration()
                
                if config and config.get('instructions'):
                    logging.info("Configuration loaded from PostgreSQL agents table")
            except Exception as e:
                logging.error(f"Error loading from PostgreSQL: {e}")
        
        # If still no config, try loading from file
        if not config:
            try:
                with open('agent_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logging.info("Configuration loaded from agent_config.json file")
            except Exception as e:
                logging.error(f"Error loading from file: {e}")
        
        # If still no config, use defaults
        if not config:
            config = {
                'name': 'Anna', 
                'model': 'gemini-2.0-flash',
                'instructions': 'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações do banco de dados antes de responder.',
                'temperature': 0.8,
                'max_tokens': 1000,
                'tools_enabled': {'routines': True, 'memories': True, 'media': True}
            }
            logging.info("Using default configuration")
            
    except Exception as e:
        logging.error(f"Error getting configuration: {e}")
        # Fallback configuration
        config = {
            'name': 'Anna', 
            'model': 'gemini-2.0-flash',
            'instructions': 'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações do banco de dados antes de responder.',
            'temperature': 0.8,
            'max_tokens': 1000,
            'tools_enabled': {'routines': True, 'memories': True, 'media': True}
        }

    # Get instructions from config (prioritizing database saved instructions)
    instructions = config.get('instructions')
    if not instructions:
        instructions = 'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações do banco de dados antes de responder.'
    
    logging.info(f"Using instructions (first 100 chars): {instructions[:100]}...")
    
    # Get description from config
    description = config.get('description', "Anna é uma produtora de conteúdo brasileira que interage de forma natural e carismática, compartilhando sua rotina, memórias e criações.")
    
    # Get tools enabled settings
    tools_enabled = config.get('tools_enabled', {'routines': True, 'memories': True, 'media': True})
    
    # Build tools list based on configuration
    tools = []
    if tools_enabled.get('routines', True):
        tools.extend([get_anna_routines, get_anna_routine_media])
    if tools_enabled.get('memories', True):
        tools.extend([search_memories, get_recent_conversations, save_conversation_memory])
    if tools_enabled.get('media', True):
        tools.extend([search_content])
    
    # Always include profile info
    tools.append(get_profile_info)
    
    # Create the agent with tools from configuration
    agent = LlmAgent(
        model=config.get('model', 'gemini-2.0-flash'),
        name=config.get('name', 'Anna').lower(),
        description=description,
        instruction=instructions,
        tools=tools,
        generate_content_config=types.GenerateContentConfig(
            temperature=float(config.get('temperature', 0.8)),
            max_output_tokens=int(config.get('max_tokens', 1000))))

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
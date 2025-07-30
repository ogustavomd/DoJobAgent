import os
import json
import logging
from google.adk.agents import LlmAgent
from google.genai import types
from database_tools_simple import (get_anna_routines, get_anna_routine_media,
                            search_memories, get_recent_conversations,
                            get_profile_info, search_content,
                            save_conversation_memory)


def create_anna_agent(config: dict):
    """Create and configure Anna agent using a configuration dictionary."""
    if not config:
        logging.error("Configuration dictionary is missing. Cannot create agent.")
        raise ValueError("Configuration is required to create an agent.")

    # Get instructions from config
    instructions = config.get('instructions', 'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações do banco de dados antes de responder.')
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

    logging.info("Anna agent created successfully with provided configuration.")
    return agent
import os
import json
import logging
from functools import partial
from google.adk.agents import LlmAgent
from google.genai import types
from database_tools import (get_anna_routines, get_anna_routine_media,
                            search_memories, get_recent_conversations,
                            get_profile_info, search_content,
                            save_conversation_memory)


def create_anna_agent(config: dict):
    from app import db
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
    
    # Build tools list based on configuration, injecting the db dependency
    tools = []
    if tools_enabled.get('routines', True):
        tools.extend([
            partial(get_anna_routines, db),
            partial(get_anna_routine_media, db)
        ])
    if tools_enabled.get('memories', True):
        tools.extend([
            partial(search_memories, db),
            partial(get_recent_conversations, db),
            partial(save_conversation_memory, db)
        ])
    if tools_enabled.get('media', True):
        tools.extend([partial(search_content, db)])
    
    # Always include profile info
    tools.append(partial(get_profile_info, db))
    
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
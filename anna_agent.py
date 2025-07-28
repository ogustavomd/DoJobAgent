import os
import logging
from google.adk.agents import LlmAgent
from google.genai import types
from supabase_tools import (
    get_anna_routines,
    get_anna_routine_media,
    search_memories,
    get_recent_conversations,
    get_profile_info,
    search_content
)

def create_anna_agent():
    """Create and configure Anna agent using configuration from file"""
    from supabase_tools import get_active_agent_configuration
    
    # Load configuration from file
    config = get_active_agent_configuration()
    instruction = config.get('instructions', 'Você é Anna, uma criadora de conteúdo brasileira.')

    # Create the agent with tools from configuration
    agent = LlmAgent(
        model=config.get('model', 'gemini-2.0-flash'),
        name=config.get('name', 'Anna').lower(),
        description="Anna é uma produtora de conteúdo brasileira que interage de forma natural e carismática, compartilhando sua rotina, memórias e criações.",
        instruction=instruction,
        tools=[
            get_anna_routines,
            get_anna_routine_media, 
            search_memories,
            get_recent_conversations,
            get_profile_info,
            search_content
        ],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.8,  # More creative and spontaneous
            max_output_tokens=1000
        )
    )
    
    logging.info("Anna agent created successfully")
    return agent

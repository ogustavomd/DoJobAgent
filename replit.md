# Anna Agent - AI-Powered Content Creator Chat

## Overview

This is an AI agent application that simulates conversations with "Anna," a Brazilian content creator. The system uses Google's Agent Development Kit (ADK) with LLM capabilities to create a charismatic, authentic virtual personality that can discuss her daily routines, content creation activities, and interact naturally with users in Brazilian Portuguese.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: HTML5, CSS3, JavaScript (Vanilla)
- **UI Framework**: Bootstrap 5 with dark theme
- **Design Pattern**: Single-page application (SPA) with real-time chat interface
- **Features**: 
  - Auto-resizing textarea
  - Typing indicators
  - Message bubbles with timestamps
  - Responsive design optimized for chat

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **AI Agent**: Google Agent Development Kit (ADK) with LLM integration
- **Architecture Pattern**: MVC with agent-based conversational AI
- **Session Management**: Flask sessions for conversation continuity
- **Middleware**: ProxyFix for proper header handling in deployment

### Data Storage Solutions
- **Primary Database**: Supabase (PostgreSQL-based)
- **Database Tables**:
  - `anna_routine`: Stores Anna's daily activities and schedules
  - `anna_routine_media`: Media files (images/videos) associated with routines
  - `chat_sessions`: User conversation sessions
  - `messages`: Individual chat messages
  - `agents`: Agent configurations and personality settings
  - `clients`: Client conversation management with channel tracking
  - `users`: System user management with plans and permissions
- **Data Access**: Direct Supabase client integration with custom Python tools

## Key Components

### 1. Anna Agent (`anna_agent.py`)
- **Purpose**: Core AI agent configuration with personality definition
- **Personality**: Charismatic Brazilian content creator with vibrant, spontaneous character
- **Language**: Brazilian Portuguese with informal expressions and emojis
- **Tools Integration**: Access to routine data, media, memories, and conversations

### 2. Supabase Tools (`supabase_tools.py`)
- **Purpose**: Database interaction layer with specialized functions
- **Key Functions**:
  - `get_anna_routines()`: Retrieve daily activities
  - `get_anna_routine_media()`: Access photos and videos
  - `search_memories()`: Search past conversations
  - `get_recent_conversations()`: Fetch recent chat history
  - `search_content()`: Content library search

### 3. Flask Application (`app.py`)
- **Purpose**: Web server and API endpoints
- **Routes**:
  - `/`: Main chat interface
  - `/chat`: POST endpoint for message processing
  - `/admin`: Calendar-based admin interface for routine management
  - `/admin/api/*`: RESTful API endpoints for CRUD operations
  - `/config`: Agent configuration interface
  - `/config/api/*`: Configuration management endpoints
  - `/clients`: Client management interface with conversation control
  - `/users`: User management interface with plans and permissions
  - `/api/clients/*`: Client management API endpoints
  - `/api/users/*`: User management API endpoints
- **Session Management**: Maintains conversation continuity

### 4. Chat Interface (`static/chat.js`, `templates/index.html`)
- **Purpose**: Real-time chat UI with Brazilian content creator theme
- **Features**: Message handling, typing indicators, auto-resize input

## Data Flow

1. **User Interaction**: User sends message via web interface
2. **Session Management**: Flask creates/retrieves session ID
3. **Agent Processing**: Anna agent processes message using ADK
4. **Tool Invocation**: Agent queries Supabase for relevant data (routines, media, memories)
5. **Response Generation**: LLM generates contextual response in Anna's personality
6. **Response Delivery**: JSON response sent back to frontend
7. **UI Update**: Chat interface displays Anna's response with proper formatting

## External Dependencies

### AI and Machine Learning
- **Google ADK**: Core agent framework for LLM integration
- **Google GenAI**: Types and utilities for Gemini model interaction

### Database and Storage
- **Supabase**: 
  - PostgreSQL database hosting
  - Real-time subscriptions capability
  - Built-in authentication (not currently utilized)
  - Media storage for routine images/videos

### Web Framework
- **Flask**: Lightweight web framework
- **Bootstrap 5**: UI component library with dark theme
- **Feather Icons**: Lightweight icon set

### WhatsApp Integration
- **Evolution API v2**: Complete WhatsApp Business API integration
- **Docker Compose**: Containerized Evolution API with PostgreSQL and Redis
- **Webhook Processing**: Real-time message handling and automatic responses
- **QR Code Connection**: Seamless WhatsApp device linking interface

### Development Tools
- **Python-supabase**: Official Supabase Python client
- **Werkzeug**: WSGI utilities and middleware

## Deployment Strategy

### Environment Configuration
- **Environment Variables**:
  - `SUPABASE_URL`: Database connection URL
  - `SUPABASE_KEY`: Database access key
  - `SESSION_SECRET`: Flask session encryption key
- **Default Port**: 5000
- **Host Configuration**: 0.0.0.0 for container deployment

### Production Considerations
- **Proxy Handling**: ProxyFix middleware for reverse proxy deployment
- **Session Security**: Configurable session secret for production
- **Logging**: Comprehensive logging with configurable levels
- **Error Handling**: Graceful fallbacks for agent initialization failures

### Scalability Notes
- **Stateless Design**: Session data stored in Flask sessions (can be moved to database)
- **Database Connection**: Single Supabase client instance (consider connection pooling for high load)
- **Agent Initialization**: Single global agent instance (consider per-session agents for isolation)

## Development Notes

The application is designed to be a conversational AI that maintains character consistency through:
- Detailed personality instructions in Portuguese
- Access to personal routine and content data
- Memory of past conversations
- Natural language processing optimized for Brazilian Portuguese expressions

### Recent Improvements (July 28-29, 2025)
- **Dynamic Instructions System Implemented**: Anna now loads personality and instructions dynamically from the configuration interface, not hardcoded values
- **Activity Cards Enhanced**: Today's activities display with larger names and Brazilian time format (10h00)
- **Database Integration Restored**: Anna properly queries Supabase database before responding, accessing real routine and media data  
- **Configuration Priority System**: Agent loads instructions from saved config first, then falls back to file/defaults
- **Calendar Display Corrected**: Fixed admin calendar rendering with proper height and aspect ratio
- **Import Error Resolution**: Corrected type annotations and removed syntax errors in supabase_tools.py
- **Clean Agent Architecture**: Rebuilt anna_agent.py with proper dynamic configuration loading and error handling
- **Tool Integration Stable**: All 7 database tools properly registered and available to Anna
- **Gemini Integration Active**: Agent connecting successfully to Gemini 2.0 Flash model
- **Agent Config Table Created**: Added `agent_config` table structure in Supabase for multi-tenant configuration storage
- **Supabase Config Integration**: Updated config API endpoints to save/load configurations from Supabase with company_id and user_id support
- **Config Loading Priority**: Anna agent now loads from Supabase first, then PostgreSQL, then agent_config.json as fallback
- **Agent Configuration Saving Fixed**: Resolved JavaScript circular function call and backend API errors
- **Local File Fallback System**: Configuration saves to local agent_config.json when Supabase table doesn't exist
- **Robust Error Handling**: Added comprehensive error handling for configuration save/load operations
- **WhatsApp Integration Complete**: Full Evolution API v2 integration with webhook handlers, QR code connection, and automatic message processing
- **WhatsApp Configuration Interface**: Complete UI for setting up Evolution API connection with status monitoring and testing capabilities
- **Docker Compose Setup**: Pre-configured Docker environment for Evolution API with PostgreSQL and Redis dependencies
- **WhatsApp Admin Navigation**: Added WhatsApp configuration button to admin interface header for easy access
- **Client Management System**: Complete interface for managing client conversations with channel tracking (WhatsApp/Instagram/Chat)
- **User Management System**: Full user administration with plans (Gratuito/Básico/Premium/Enterprise) and permissions
- **Active/Inactive Control**: Ability to enable/disable users and clients to control Anna's responses
- **Multi-Channel Support**: Unified management for WhatsApp, Instagram, Chat, and Web channels
- **Chat Session Management PostgreSQL**: Complete chat session system with automatic contact registration and message tracking using PostgreSQL
- **Automatic Session Creation**: All contacts are registered automatically when they interact via any channel (WhatsApp, Instagram, Chat, Web)
- **Message Storage**: All sent and received messages are saved with proper session linking and timestamps
- **Interface Simplification**: Removed WhatsApp, Clientes, and Usuários buttons from activity management interface per user request

### Current Database State
- **Sample Data**: Populated with realistic routine activities, media files, and conversation history
- **Active Routines**: Anna has multiple daily activities including workouts, content creation, meetings, and social events
- **Media Library**: Contains images and videos linked to specific activities using Unsplash and sample video URLs
- **Status Management**: Activities automatically update their status (upcoming/current/completed) based on current time
- **Admin Features**: Full CRUD operations with calendar view, media uploads to Supabase storage, and activity ratings
- **Configuration System**: Real-time agent reconfiguration with instructions, tools, and model settings

The architecture supports easy extension of Anna's capabilities through additional Supabase tools and can accommodate new database tables for expanded functionality.
# Database type definitions for Anna's Supabase schema
# This file contains the TypeScript types converted to Python for reference

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnnaRoutine:
    """Anna's routine/activity data"""
    id: str
    activity: str
    category: str
    date: str
    time_start: str
    time_end: str
    status: str
    description: Optional[str] = None
    location: Optional[str] = None
    has_images: Optional[bool] = None
    has_videos: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class AnnaRoutineMedia:
    """Media associated with Anna's routines"""
    id: str
    media_type: str
    media_url: str
    routine_id: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class ChatSession:
    """Chat session data"""
    id: str
    contact_phone: str
    contact_name: Optional[str] = None
    contact_avatar: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Message:
    """Chat message data"""
    id: str
    content: str
    sender_phone: str
    chat_session_id: Optional[str] = None
    media_url: Optional[str] = None
    message_type: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class Profile:
    """User profile data"""
    id: str
    phone_number: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Conteudo:
    """Content library data"""
    id: str
    titulo: str
    tipo_conteudo: str
    url: str
    bucket: str
    descricao: Optional[str] = None
    criado_em: Optional[str] = None
    atualizado_em: Optional[str] = None

@dataclass
class Image:
    """Image data with embeddings"""
    id: str
    url: Optional[str] = None
    embedding: Optional[str] = None

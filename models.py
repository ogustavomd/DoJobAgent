from app import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Routine(db.Model):
    """Routine/activity data"""
    __tablename__ = 'routine'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_start = db.Column(db.Time, nullable=False)
    time_end = db.Column(db.Time, nullable=False)
    status = db.Column(db.Text, default='upcoming', nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.Text)
    has_images = db.Column(db.Boolean, default=False)
    has_videos = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with media
    media = relationship('RoutineMedia', back_populates='routine', cascade='all, delete-orphan')

class RoutineMedia(db.Model):
    """Media associated with routines"""
    __tablename__ = 'routine_media'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    media_type = db.Column(db.String(50), nullable=False)  # 'image' or 'video'
    media_url = db.Column(db.Text, nullable=False)
    routine_id = db.Column(UUID(as_uuid=True), db.ForeignKey('routine.id'))
    media_caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationship with routine
    routine = relationship('Routine', back_populates='media')

class ChatSession(db.Model):
    """Chat session data"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    contact_phone = db.Column(db.String(20), nullable=False)
    contact_name = db.Column(db.String(255))
    contact_avatar = db.Column(db.Text)
    user_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with messages
    messages = relationship('Message', back_populates='session', cascade='all, delete-orphan')

class Message(db.Model):
    """Chat message data"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    assistant_response = db.Column(db.Text)
    content = db.Column(db.Text)
    sender_phone = db.Column(db.String(20))
    chat_session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'))
    media_url = db.Column(db.Text)
    message_type = db.Column(db.String(50), default='text')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with session
    session = relationship('ChatSession', back_populates='messages')

class Memory(db.Model):
    """Memories and past conversations"""
    __tablename__ = 'memories'
    
    id = db.Column(db.Integer, primary_key=True)
    memory_type = db.Column(db.String(50), nullable=False)  # 'conversation', 'experience', 'fact'
    content = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text)
    importance_score = db.Column(db.Integer, default=1)  # 1-10 scale
    tags = db.Column(db.Text)  # JSON array of tags
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Agent(db.Model):
    """Agent configuration settings matching the PostgreSQL agents table"""
    __tablename__ = 'agents'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID as string
    nome = db.Column(db.Text, nullable=False)
    modelo = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.Text)
    instrucoes_personalidade = db.Column(db.Text)
    temperatura = db.Column(db.Numeric(2, 1), default=0.7)
    max_tokens = db.Column(db.Integer, default=1000)
    rotinas_ativas = db.Column(db.Boolean, default=True)
    memorias_ativas = db.Column(db.Boolean, default=True)
    midia_ativa = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
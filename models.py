from app import db
from datetime import datetime
from sqlalchemy.orm import relationship

class AnnaRoutine(db.Model):
    """Anna's routine/activity data"""
    __tablename__ = 'anna_routine'
    
    id = db.Column(db.Integer, primary_key=True)
    activity = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time_start = db.Column(db.String(20))
    time_end = db.Column(db.String(20))
    status = db.Column(db.String(50), default='upcoming')
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    has_images = db.Column(db.Boolean, default=False)
    has_videos = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with media
    media = relationship('AnnaRoutineMedia', back_populates='routine', cascade='all, delete-orphan')

class AnnaRoutineMedia(db.Model):
    """Media associated with Anna's routines"""
    __tablename__ = 'anna_routine_media'
    
    id = db.Column(db.Integer, primary_key=True)
    media_type = db.Column(db.String(50), nullable=False)  # 'image' or 'video'
    media_url = db.Column(db.Text, nullable=False)
    routine_id = db.Column(db.Integer, db.ForeignKey('anna_routine.id'))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with routine
    routine = relationship('AnnaRoutine', back_populates='media')

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

class AnnaMemory(db.Model):
    """Anna's memories and past conversations"""
    __tablename__ = 'anna_memories'
    
    id = db.Column(db.Integer, primary_key=True)
    memory_type = db.Column(db.String(50), nullable=False)  # 'conversation', 'experience', 'fact'
    content = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text)
    importance_score = db.Column(db.Integer, default=1)  # 1-10 scale
    tags = db.Column(db.Text)  # JSON array of tags
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentConfiguration(db.Model):
    """Agent configuration settings"""
    __tablename__ = 'agent_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), default='gemini-2.0-flash')
    description = db.Column(db.Text)
    instructions = db.Column(db.Text, nullable=False)
    tools_enabled = db.Column(db.Text)  # JSON array of enabled tools
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
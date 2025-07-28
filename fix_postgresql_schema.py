#!/usr/bin/env python3
"""
Fix PostgreSQL schema to match the correct table structure
"""

import os
import logging
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment"""
    return os.environ.get('DATABASE_URL')

def fix_schema():
    """Drop and recreate anna_routine table with correct schema"""
    
    database_url = get_database_url()
    if not database_url:
        logger.error("DATABASE_URL not found in environment")
        return False
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                # Drop existing table
                logger.info("Dropping existing anna_routine table...")
                conn.execute(text("DROP TABLE IF EXISTS anna_routine CASCADE;"))
                
                # Create new table with correct schema
                logger.info("Creating anna_routine table with correct schema...")
                create_table_sql = """
                CREATE TABLE anna_routine (
                    id UUID NOT NULL DEFAULT gen_random_uuid(),
                    date DATE NOT NULL DEFAULT CURRENT_DATE,
                    time_start TIME WITHOUT TIME ZONE NOT NULL,
                    time_end TIME WITHOUT TIME ZONE NOT NULL,
                    activity TEXT NOT NULL,
                    description TEXT,
                    location TEXT,
                    status TEXT NOT NULL DEFAULT 'upcoming'::text,
                    category TEXT NOT NULL,
                    has_images BOOLEAN DEFAULT false,
                    has_videos BOOLEAN DEFAULT false,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
                    CONSTRAINT anna_routine_pkey PRIMARY KEY (id),
                    CONSTRAINT anna_routine_category_check CHECK (
                        category = ANY (ARRAY[
                            'fitness'::text,
                            'trabalho'::text,
                            'reunião'::text,
                            'social'::text,
                            'pessoal'::text
                        ])
                    ),
                    CONSTRAINT anna_routine_status_check CHECK (
                        status = ANY (ARRAY[
                            'completed'::text,
                            'current'::text,
                            'upcoming'::text
                        ])
                    )
                );
                """
                conn.execute(text(create_table_sql))
                
                # Create trigger function if not exists
                logger.info("Creating update trigger function...")
                trigger_function_sql = """
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = now();
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
                """
                conn.execute(text(trigger_function_sql))
                
                # Create trigger
                logger.info("Creating update trigger...")
                trigger_sql = """
                CREATE TRIGGER update_anna_routine_updated_at 
                BEFORE UPDATE ON anna_routine 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column();
                """
                conn.execute(text(trigger_sql))
                
                # Insert sample data
                logger.info("Inserting sample data...")
                sample_data_sql = """
                INSERT INTO anna_routine (date, time_start, time_end, activity, description, location, status, category, has_images, has_videos) VALUES
                ('2025-07-29', '07:00', '08:30', 'Treino na academia', 'Treino de força e cardio', 'Smart Fit - Vila Madalena', 'upcoming', 'fitness', true, false),
                ('2025-07-29', '10:00', '12:00', 'Gravação de conteúdo', 'Gravação de vídeos para Instagram', 'Estúdio em casa', 'upcoming', 'trabalho', true, true),
                ('2025-07-29', '14:00', '15:30', 'Reunião com marca', 'Apresentação de proposta para parceria', 'Online - Zoom', 'upcoming', 'reunião', false, false),
                ('2025-07-29', '19:00', '21:00', 'Jantar com amigas', 'Encontro no restaurante japonês', 'Yamashiro - Vila Olímpia', 'upcoming', 'social', true, false),
                ('2025-07-30', '08:00', '09:00', 'Yoga matinal', 'Aula de yoga online', 'Casa', 'upcoming', 'fitness', false, false),
                ('2025-07-30', '11:00', '13:00', 'Sessão de fotos', 'Fotos para campanha de verão', 'Estúdio fotográfico', 'upcoming', 'trabalho', true, false),
                ('2025-07-30', '16:00', '17:00', 'Podcast gravação', 'Participação no podcast sobre lifestyle', 'Estúdio do podcast', 'upcoming', 'trabalho', false, true),
                ('2025-07-31', '09:30', '11:00', 'Pilates', 'Aula de pilates na academia', 'Studio Pilates', 'upcoming', 'fitness', false, false),
                ('2025-07-31', '15:00', '16:30', 'Live no Instagram', 'Live sobre rotina de skincare', 'Casa - quarto', 'upcoming', 'trabalho', true, true),
                ('2025-07-31', '20:00', '22:30', 'Cinema', 'Filme com o namorado', 'Shopping Iguatemi', 'upcoming', 'pessoal', false, false);
                """
                conn.execute(text(sample_data_sql))
                
                # Commit transaction
                trans.commit()
                logger.info("Schema fixed successfully!")
                return True
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                logger.error(f"Error during schema migration: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False

if __name__ == "__main__":
    success = fix_schema()
    if success:
        print("✅ PostgreSQL schema fixed successfully!")
    else:
        print("❌ Failed to fix PostgreSQL schema")
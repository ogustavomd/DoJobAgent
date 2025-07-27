#!/usr/bin/env python3
"""
Script to populate Anna's database with sample data for testing
"""

import os
import sys
from datetime import datetime, timedelta
from supabase_tools import supabase

def populate_routine_data():
    """Add sample routine data for Anna"""
    print("Adding sample routine data...")
    
    # Today's date for sample data
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    sample_routines = [
        {
            'date': str(today),
            'time_start': '07:00',
            'time_end': '08:00',
            'activity': 'Treino matinal na academia',
            'description': 'Sessão de treino focada em pernas e glúteo. Fiz vários stories no espelho da academia!',
            'location': 'Academia Fitness Plus',
            'status': 'completed',
            'category': 'fitness',
            'has_images': True,
            'has_videos': False
        },
        {
            'date': str(today),
            'time_start': '09:30',
            'time_end': '11:00',
            'activity': 'Gravação de conteúdo para Instagram',
            'description': 'Gravei 3 vídeos sobre rotina matinal e dicas de skincare',
            'location': 'Casa - Home Office',
            'status': 'completed',
            'category': 'trabalho',
            'has_images': True,
            'has_videos': True
        },
        {
            'date': str(today),
            'time_start': '14:00',
            'time_end': '15:30',
            'activity': 'Reunião com marca de cosméticos',
            'description': 'Meeting online para discutir nova campanha publicitária',
            'location': 'Casa - Home Office',
            'status': 'completed',
            'category': 'reunião',
            'has_images': False,
            'has_videos': False
        },
        {
            'date': str(today),
            'time_start': '16:00',
            'time_end': '17:00',
            'activity': 'Coffee com amigas influencers',
            'description': 'Encontro no café da Paulista com as meninas para trocar ideias',
            'location': 'Café da Esquina - Paulista',
            'status': 'completed',
            'category': 'social',
            'has_images': True,
            'has_videos': False
        },
        {
            'date': str(today),
            'time_start': '19:00',
            'time_end': '20:00',
            'activity': 'Jantar romântico',
            'description': 'Jantar especial com meu namorado no restaurante italiano',
            'location': 'Ristorante Amore',
            'status': 'current',
            'category': 'pessoal',
            'has_images': True,
            'has_videos': False
        },
        {
            'date': str(yesterday),
            'time_start': '08:00',
            'time_end': '10:00',
            'activity': 'Sessão de fotos para marca de moda',
            'description': 'Ensaio fotográfico para campanha de verão da loja XYZ',
            'location': 'Estúdio Luz & Sombra',
            'status': 'completed',
            'category': 'trabalho',
            'has_images': True,
            'has_videos': True
        }
    ]
    
    try:
        response = supabase.table('anna_routine').insert(sample_routines).execute()
        print(f"✓ Added {len(sample_routines)} routine entries")
        return [item['id'] for item in response.data]
    except Exception as e:
        print(f"Error adding routine data: {e}")
        return []

def populate_media_data(routine_ids):
    """Add sample media data"""
    print("Adding sample media data...")
    
    sample_media = [
        {
            'routine_id': routine_ids[0] if routine_ids else None,
            'media_type': 'image',
            'media_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500',
            'description': 'Foto no espelho da academia depois do treino'
        },
        {
            'routine_id': routine_ids[1] if len(routine_ids) > 1 else None,
            'media_type': 'video',
            'media_url': 'https://sample-videos.com/zip/10/mp4/SampleVideo_360x240_1mb.mp4',
            'description': 'Vídeo da rotina matinal de skincare'
        },
        {
            'routine_id': routine_ids[1] if len(routine_ids) > 1 else None,
            'media_type': 'image',
            'media_url': 'https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500',
            'description': 'Setup da gravação no home office'
        },
        {
            'routine_id': routine_ids[3] if len(routine_ids) > 3 else None,
            'media_type': 'image',
            'media_url': 'https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=500',
            'description': 'Café com as amigas influencers na Paulista'
        },
        {
            'routine_id': routine_ids[4] if len(routine_ids) > 4 else None,
            'media_type': 'image',
            'media_url': 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=500',
            'description': 'Mesa do jantar romântico no restaurante italiano'
        }
    ]
    
    try:
        response = supabase.table('anna_routine_media').insert(sample_media).execute()
        print(f"✓ Added {len(sample_media)} media entries")
    except Exception as e:
        print(f"Error adding media data: {e}")

def populate_chat_data():
    """Add sample chat sessions and messages"""
    print("Adding sample chat data...")
    
    # Add a sample chat session
    chat_session = {
        'contact_phone': '+5511999887766',
        'contact_name': 'João Silva',
        'contact_avatar': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100'
    }
    
    try:
        session_response = supabase.table('chat_sessions').insert([chat_session]).execute()
        session_id = session_response.data[0]['id']
        
        # Add sample messages
        messages = [
            {
                'chat_session_id': session_id,
                'sender_phone': '+5511999887766',
                'content': 'Oi Anna! Como foi seu treino hoje?',
                'message_type': 'text'
            },
            {
                'chat_session_id': session_id,
                'sender_phone': 'anna',
                'content': 'Oi João! Foi incrível! Treinei pernas e me senti super poderosa 💪',
                'message_type': 'text'
            },
            {
                'chat_session_id': session_id,
                'sender_phone': '+5511999887766',
                'content': 'Que legal! Você sempre posta umas fotos massa do treino',
                'message_type': 'text'
            }
        ]
        
        supabase.table('messages').insert(messages).execute()
        print(f"✓ Added sample chat session with {len(messages)} messages")
        
    except Exception as e:
        print(f"Error adding chat data: {e}")

def populate_content_data():
    """Add sample content library data"""
    print("Adding sample content data...")
    
    content_items = [
        {
            'titulo': 'Rotina Matinal de Skincare',
            'descricao': 'Vídeo tutorial mostrando minha rotina completa de cuidados com a pele',
            'tipo_conteudo': 'video',
            'url': 'https://example.com/skincare-routine.mp4',
            'bucket': 'content-videos'
        },
        {
            'titulo': 'Look do Dia - Casual Chic',
            'descricao': 'Fotos do look casual chic para o café com as amigas',
            'tipo_conteudo': 'image',
            'url': 'https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=500',
            'bucket': 'content-images'
        },
        {
            'titulo': 'Receita de Smoothie Pós-Treino',
            'descricao': 'Receita do meu smoothie favorito para depois do treino',
            'tipo_conteudo': 'image',
            'url': 'https://images.unsplash.com/photo-1610970881699-44a5587cabec?w=500',
            'bucket': 'content-images'
        }
    ]
    
    try:
        supabase.table('conteudo').insert(content_items).execute()
        print(f"✓ Added {len(content_items)} content items")
    except Exception as e:
        print(f"Error adding content data: {e}")

def main():
    """Main function to populate all sample data"""
    print("🚀 Starting to populate Anna's database with sample data...")
    
    try:
        # Add routine data first and get IDs
        routine_ids = populate_routine_data()
        
        # Add media data linked to routines
        if routine_ids:
            populate_media_data(routine_ids)
        
        # Add chat data
        populate_chat_data()
        
        # Add content data
        populate_content_data()
        
        print("\n✅ Sample data population completed successfully!")
        print("Anna now has routine data, media, conversations, and content to reference!")
        
    except Exception as e:
        print(f"\n❌ Error during data population: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
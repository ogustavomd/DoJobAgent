"""
AI-Powered Routine Suggestion Engine for Anna
Analyzes existing routines and suggests optimized activities based on patterns, preferences, and goals.
"""

import os
import logging
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import json
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoutineSuggestionEngine:
    """AI-powered engine for suggesting routine optimizations and new activities"""
    
    def __init__(self, db_session):
        self.db = db_session
        
        # Activity templates and patterns
        self.activity_templates = {
            'fitness': {
                'morning': ['Treino na academia', 'Corrida no parque', 'Yoga matinal', 'Pilates', 'Natação'],
                'afternoon': ['Aula de dança', 'Personal trainer', 'Crossfit', 'Muay thai'],
                'evening': ['Caminhada relaxante', 'Alongamento', 'Yoga noturna']
            },
            'trabalho': {
                'morning': ['Gravação de conteúdo', 'Edição de vídeos', 'Planejamento de conteúdo', 'Fotos para Instagram'],
                'afternoon': ['Reunião com marca', 'Sessão de fotos', 'Live no Instagram', 'Podcast gravação'],
                'evening': ['Responder comentários', 'Análise de métricas', 'Planejamento do dia seguinte']
            },
            'social': {
                'afternoon': ['Almoço com amigas', 'Café da tarde', 'Shopping'],
                'evening': ['Jantar com amigas', 'Festa', 'Evento social', 'Happy hour']
            },
            'pessoal': {
                'morning': ['Cuidados pessoais', 'Meditação', 'Leitura'],
                'afternoon': ['Cuidados com a pele', 'Massagem', 'Spa'],
                'evening': ['Cinema', 'Jantar romântico', 'Série em casa', 'Tempo em família']
            },
            'reunião': {
                'morning': ['Reunião de planejamento', 'Briefing de projeto'],
                'afternoon': ['Apresentação para cliente', 'Reunião com equipe', 'Call com parceiros'],
                'evening': ['Networking event', 'Reunião online']
            }
        }
        
        # Locations for different activities
        self.locations = {
            'fitness': ['Smart Fit - Vila Madalena', 'Studio Pilates', 'Parque Ibirapuera', 'Casa'],
            'trabalho': ['Estúdio em casa', 'Estúdio fotográfico', 'Coworking Vila Madalena', 'Online'],
            'social': ['Vila Madalena', 'Vila Olímpia', 'Shopping Iguatemi', 'Restaurante'],
            'pessoal': ['Casa', 'Spa Urbano', 'Shopping', 'Cinema'],
            'reunião': ['Online - Zoom', 'Escritório parceiro', 'Café Vila Madalena', 'Coworking']
        }
        
        # Time patterns for different activity types
        self.time_patterns = {
            'fitness': {'morning': (7, 9), 'afternoon': (14, 16), 'evening': (18, 20)},
            'trabalho': {'morning': (9, 12), 'afternoon': (13, 17), 'evening': (19, 21)},
            'social': {'afternoon': (15, 17), 'evening': (19, 22)},
            'pessoal': {'morning': (8, 10), 'afternoon': (14, 16), 'evening': (20, 22)},
            'reunião': {'morning': (9, 11), 'afternoon': (14, 16), 'evening': (19, 20)}
        }

    def analyze_current_routines(self, days_back: int = 30) -> Dict[str, Any]:
        """Analyze existing routines to identify patterns and gaps"""
        from models import AnnaRoutine
        
        # Get recent routines
        start_date = date.today() - timedelta(days=days_back)
        routines = self.db.query(AnnaRoutine).filter(
            AnnaRoutine.date >= start_date
        ).all()
        
        analysis = {
            'total_activities': len(routines),
            'category_distribution': Counter(),
            'time_patterns': defaultdict(list),
            'preferred_locations': Counter(),
            'activity_frequency': Counter(),
            'gaps_identified': [],
            'optimization_opportunities': []
        }
        
        # Analyze patterns
        for routine in routines:
            analysis['category_distribution'][routine.category] += 1
            analysis['preferred_locations'][routine.location] += 1
            analysis['activity_frequency'][routine.activity] += 1
            
            # Time pattern analysis
            if routine.time_start:
                hour = routine.time_start.hour
                time_period = self._get_time_period(hour)
                analysis['time_patterns'][routine.category].append(time_period)
        
        # Identify gaps and opportunities
        analysis['gaps_identified'] = self._identify_gaps(analysis)
        analysis['optimization_opportunities'] = self._find_optimization_opportunities(analysis)
        
        return analysis

    def _get_time_period(self, hour: int) -> str:
        """Classify time into periods"""
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        else:
            return 'evening'

    def _identify_gaps(self, analysis: Dict) -> List[str]:
        """Identify gaps in routine coverage"""
        gaps = []
        
        # Check category balance
        total = analysis['total_activities']
        if total > 0:
            fitness_ratio = analysis['category_distribution']['fitness'] / total
            if fitness_ratio < 0.2:
                gaps.append("Poucos exercícios físicos na rotina")
            
            work_ratio = analysis['category_distribution']['trabalho'] / total
            if work_ratio > 0.6:
                gaps.append("Muitas atividades de trabalho - necessário mais equilíbrio")
            
            social_ratio = analysis['category_distribution']['social'] / total
            if social_ratio < 0.1:
                gaps.append("Poucas atividades sociais")
            
            personal_ratio = analysis['category_distribution']['pessoal'] / total
            if personal_ratio < 0.15:
                gaps.append("Pouco tempo dedicado ao autocuidado")
        
        return gaps

    def _find_optimization_opportunities(self, analysis: Dict) -> List[str]:
        """Find opportunities to optimize the routine"""
        opportunities = []
        
        # Time optimization suggestions
        morning_activities = sum(1 for times in analysis['time_patterns'].values() 
                               for t in times if t == 'morning')
        if morning_activities < analysis['total_activities'] * 0.3:
            opportunities.append("Aproveitar melhor as manhãs para atividades produtivas")
        
        # Location optimization
        home_activities = analysis['preferred_locations'].get('Casa', 0)
        if home_activities > analysis['total_activities'] * 0.4:
            opportunities.append("Diversificar locais para estimular criatividade")
        
        # Activity variety
        if len(analysis['activity_frequency']) < analysis['total_activities'] * 0.6:
            opportunities.append("Aumentar variedade de atividades")
        
        return opportunities

    def suggest_weekly_routine(self, target_date: date, preferences: Dict = None) -> List[Dict]:
        """Generate AI-powered suggestions for a week starting from target_date"""
        suggestions = []
        analysis = self.analyze_current_routines()
        
        # Default preferences if not provided
        if not preferences:
            preferences = {
                'fitness_goals': 4,  # activities per week
                'work_balance': True,
                'social_priority': 'medium',
                'preferred_times': ['morning', 'afternoon'],
                'avoid_categories': []
            }
        
        # Generate suggestions for 7 days
        for i in range(7):
            day_date = target_date + timedelta(days=i)
            day_suggestions = self._suggest_daily_activities(day_date, analysis, preferences)
            suggestions.extend(day_suggestions)
        
        return suggestions

    def _suggest_daily_activities(self, target_date: date, analysis: Dict, preferences: Dict) -> List[Dict]:
        """Suggest activities for a specific day"""
        suggestions = []
        weekday = target_date.weekday()  # 0 = Monday, 6 = Sunday
        
        # Determine activity distribution based on weekday
        if weekday < 5:  # Weekday
            activity_count = random.randint(2, 4)
            categories = ['trabalho', 'fitness'] + random.choices(['reunião', 'pessoal'], k=activity_count-2)
        else:  # Weekend
            activity_count = random.randint(1, 3)
            categories = random.choices(['fitness', 'social', 'pessoal'], k=activity_count)
        
        # Filter out avoided categories
        categories = [cat for cat in categories if cat not in preferences.get('avoid_categories', [])]
        
        # Generate suggestions for each category
        used_times = set()
        for category in categories:
            suggestion = self._create_activity_suggestion(target_date, category, analysis, preferences, used_times)
            if suggestion:
                suggestions.append(suggestion)
                # Add time to used_times to avoid conflicts
                start_time = suggestion['time_start']
                end_time = suggestion['time_end']
                used_times.add((start_time, end_time))
        
        return suggestions

    def _create_activity_suggestion(self, target_date: date, category: str, analysis: Dict, 
                                  preferences: Dict, used_times: set) -> Optional[Dict]:
        """Create a single activity suggestion"""
        
        # Choose time period based on category and preferences
        available_periods = list(self.time_patterns[category].keys())
        preferred_periods = [p for p in available_periods if p in preferences.get('preferred_times', available_periods)]
        time_period = random.choice(preferred_periods if preferred_periods else available_periods)
        
        # Generate time slot
        time_range = self.time_patterns[category][time_period]
        start_hour = random.randint(time_range[0], time_range[1] - 1)
        duration = random.randint(60, 180)  # 1-3 hours
        
        start_time = time(start_hour, random.choice([0, 30]))
        end_time = (datetime.combine(target_date, start_time) + timedelta(minutes=duration)).time()
        
        # Check for time conflicts
        for used_start, used_end in used_times:
            if not (end_time <= used_start or start_time >= used_end):
                return None  # Time conflict
        
        # Choose activity and location
        activities = self.activity_templates[category][time_period]
        activity_name = random.choice(activities)
        location = random.choice(self.locations[category])
        
        # Generate description
        descriptions = {
            'fitness': f"Sessão de {activity_name.lower()} para manter a forma e energia",
            'trabalho': f"Foco em {activity_name.lower()} para engajar com a audiência",
            'social': f"Momento de {activity_name.lower()} para relaxar e socializar",
            'pessoal': f"Tempo dedicado a {activity_name.lower()} para bem-estar",
            'reunião': f"{activity_name} para alinhar projetos e oportunidades"
        }
        
        return {
            'date': target_date.isoformat(),
            'time_start': start_time.strftime('%H:%M'),
            'time_end': end_time.strftime('%H:%M'),
            'activity': activity_name,
            'category': category,
            'location': location,
            'description': descriptions.get(category, f"Atividade de {category}"),
            'status': 'suggested',
            'confidence_score': self._calculate_confidence_score(category, analysis),
            'reasoning': self._generate_reasoning(category, time_period, analysis)
        }

    def _calculate_confidence_score(self, category: str, analysis: Dict) -> float:
        """Calculate confidence score for suggestion based on historical patterns"""
        total_activities = analysis['total_activities']
        if total_activities == 0:
            return 0.5
        
        category_frequency = analysis['category_distribution'].get(category, 0)
        normalized_frequency = category_frequency / total_activities
        
        # Higher confidence for categories with established patterns
        base_confidence = min(0.9, 0.3 + normalized_frequency * 1.2)
        
        return round(base_confidence, 2)

    def _generate_reasoning(self, category: str, time_period: str, analysis: Dict) -> str:
        """Generate human-readable reasoning for the suggestion"""
        reasons = {
            'fitness': f"Baseado no seu padrão de exercícios, uma atividade de {time_period} seria ideal para manter energia",
            'trabalho': f"Considerando sua produtividade em {time_period}, este é um ótimo momento para conteúdo",
            'social': f"Equilibrar trabalho com atividades sociais em {time_period} é importante para bem-estar",
            'pessoal': f"Reservar tempo em {time_period} para autocuidado melhora sua performance geral",
            'reunião': f"Reuniões em {time_period} tendem a ser mais eficazes baseado no seu histórico"
        }
        
        return reasons.get(category, f"Sugestão baseada em análise de padrões para {category}")

    def optimize_existing_routine(self, routine_id: str) -> Dict[str, Any]:
        """Suggest optimizations for an existing routine activity"""
        from models import AnnaRoutine
        
        routine = self.db.query(AnnaRoutine).filter(AnnaRoutine.id == routine_id).first()
        if not routine:
            return {'error': 'Routine not found'}
        
        analysis = self.analyze_current_routines()
        optimizations = []
        
        # Time optimization
        current_hour = routine.time_start.hour if routine.time_start else 12
        optimal_times = self._get_optimal_times_for_category(routine.category, analysis)
        if current_hour not in optimal_times:
            optimizations.append({
                'type': 'time',
                'suggestion': f"Considere mover para {optimal_times[0]}h-{optimal_times[0]+2}h para melhor produtividade",
                'confidence': 0.8
            })
        
        # Location optimization
        popular_locations = self._get_popular_locations_for_category(routine.category, analysis)
        if routine.location not in popular_locations[:3]:
            optimizations.append({
                'type': 'location',
                'suggestion': f"Local alternativo: {popular_locations[0]} pode trazer nova perspectiva",
                'confidence': 0.6
            })
        
        # Duration optimization
        if routine.time_start and routine.time_end:
            current_duration = (datetime.combine(date.today(), routine.time_end) - 
                              datetime.combine(date.today(), routine.time_start)).total_seconds() / 3600
            optimal_duration = self._get_optimal_duration(routine.category)
            
            if abs(current_duration - optimal_duration) > 0.5:
                optimizations.append({
                    'type': 'duration',
                    'suggestion': f"Duração ideal: {optimal_duration}h para máxima eficiência",
                    'confidence': 0.7
                })
        
        return {
            'routine_id': routine_id,
            'optimizations': optimizations,
            'overall_score': len(optimizations) == 0 and 0.9 or 0.7
        }

    def _get_optimal_times_for_category(self, category: str, analysis: Dict) -> List[int]:
        """Get optimal hours for a category based on analysis"""
        defaults = {
            'fitness': [7, 8, 18],
            'trabalho': [9, 10, 14],
            'social': [19, 20],
            'pessoal': [8, 20],
            'reunião': [10, 14, 15]
        }
        return defaults.get(category, [10, 14])

    def _get_popular_locations_for_category(self, category: str, analysis: Dict) -> List[str]:
        """Get popular locations for a category"""
        # Filter locations by category from analysis
        all_locations = list(analysis['preferred_locations'].keys())
        category_locations = [loc for loc in all_locations if any(
            keyword in loc.lower() for keyword in self._get_location_keywords(category)
        )]
        
        if not category_locations:
            return self.locations.get(category, ['Casa'])
        
        return category_locations[:3]

    def _get_location_keywords(self, category: str) -> List[str]:
        """Get keywords to identify locations for a category"""
        keywords = {
            'fitness': ['academia', 'studio', 'parque', 'piscina'],
            'trabalho': ['estúdio', 'coworking', 'escritório'],
            'social': ['restaurante', 'bar', 'shopping', 'café'],
            'pessoal': ['casa', 'spa', 'salão'],
            'reunião': ['zoom', 'online', 'escritório', 'sala']
        }
        return keywords.get(category, [])

    def _get_optimal_duration(self, category: str) -> float:
        """Get optimal duration in hours for different activity categories"""
        durations = {
            'fitness': 1.5,
            'trabalho': 2.0,
            'social': 2.5,
            'pessoal': 1.0,
            'reunião': 1.0
        }
        return durations.get(category, 1.5)

    def get_suggestion_metrics(self) -> Dict[str, Any]:
        """Get metrics about suggestion engine performance"""
        analysis = self.analyze_current_routines()
        
        return {
            'total_routines_analyzed': analysis['total_activities'],
            'categories_covered': len(analysis['category_distribution']),
            'most_common_category': analysis['category_distribution'].most_common(1)[0] if analysis['category_distribution'] else None,
            'routine_balance_score': self._calculate_balance_score(analysis),
            'optimization_potential': len(analysis['gaps_identified']) + len(analysis['optimization_opportunities']),
            'last_analysis': datetime.now().isoformat()
        }

    def _calculate_balance_score(self, analysis: Dict) -> float:
        """Calculate how balanced the routine is across categories"""
        if not analysis['category_distribution']:
            return 0.0
        
        total = analysis['total_activities']
        ideal_distribution = {'fitness': 0.25, 'trabalho': 0.35, 'social': 0.15, 'pessoal': 0.15, 'reunião': 0.10}
        
        score = 0.0
        for category, ideal_ratio in ideal_distribution.items():
            actual_ratio = analysis['category_distribution'].get(category, 0) / total
            # Penalty for deviation from ideal
            deviation = abs(actual_ratio - ideal_ratio)
            score += max(0, 1 - deviation * 2)  # Max penalty of 1.0 per category
        
        return round(score / len(ideal_distribution), 2)
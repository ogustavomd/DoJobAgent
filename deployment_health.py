#!/usr/bin/env python3
"""
Deployment Health Check Tool
Verifies all required environment variables and database connectivity
"""
import os
import logging
from typing import Dict, Any

def check_deployment_health() -> Dict[str, Any]:
    """
    Comprehensive deployment health check
    
    Returns:
        Dict with health status and detailed checks
    """
    health_status = {
        'overall_status': 'healthy',
        'checks': {},
        'warnings': [],
        'errors': []
    }
    
    # Check required environment variables
    required_env_vars = [
        'DATABASE_URL',
        'SESSION_SECRET'
    ]
    
    optional_env_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]
    
    for var in required_env_vars:
        value = os.environ.get(var)
        if value:
            health_status['checks'][var] = 'present'
        else:
            health_status['checks'][var] = 'missing'
            health_status['errors'].append(f'Required environment variable {var} is not set')
            health_status['overall_status'] = 'unhealthy'
    
    for var in optional_env_vars:
        value = os.environ.get(var)
        if value:
            health_status['checks'][var] = 'present'
        else:
            health_status['checks'][var] = 'missing'
            health_status['warnings'].append(f'Optional environment variable {var} is not set')
    
    # Check database connectivity
    try:
        from app import app, db
        with app.app_context():
            db.session.execute(db.text('SELECT 1'))
            health_status['checks']['database_connection'] = 'connected'
    except Exception as e:
        health_status['checks']['database_connection'] = f'failed: {str(e)}'
        health_status['errors'].append(f'Database connection failed: {str(e)}')
        health_status['overall_status'] = 'unhealthy'
    
    # Check agent initialization
    try:
        from app import anna_agent
        if anna_agent:
            health_status['checks']['agent_initialization'] = 'initialized'
        else:
            health_status['checks']['agent_initialization'] = 'not_initialized'
            health_status['warnings'].append('Anna agent is not initialized')
            if health_status['overall_status'] == 'healthy':
                health_status['overall_status'] = 'degraded'
    except Exception as e:
        health_status['checks']['agent_initialization'] = f'error: {str(e)}'
        health_status['errors'].append(f'Agent initialization check failed: {str(e)}')
        health_status['overall_status'] = 'unhealthy'
    
    return health_status

def print_health_report():
    """Print a detailed health report to console"""
    health = check_deployment_health()
    
    print("\n" + "="*60)
    print("DEPLOYMENT HEALTH REPORT")
    print("="*60)
    print(f"Overall Status: {health['overall_status'].upper()}")
    
    print("\nEnvironment Variables:")
    for check, status in health['checks'].items():
        if check.endswith('_URL') or check.endswith('_KEY') or check.endswith('_SECRET'):
            emoji = "✅" if status == 'present' else "❌"
            print(f"  {emoji} {check}: {status}")
    
    print("\nSystem Checks:")
    for check, status in health['checks'].items():
        if not (check.endswith('_URL') or check.endswith('_KEY') or check.endswith('_SECRET')):
            emoji = "✅" if status in ['connected', 'initialized'] else "❌"
            print(f"  {emoji} {check}: {status}")
    
    if health['warnings']:
        print("\nWarnings:")
        for warning in health['warnings']:
            print(f"  ⚠️  {warning}")
    
    if health['errors']:
        print("\nErrors:")
        for error in health['errors']:
            print(f"  ❌ {error}")
    
    print("\n" + "="*60)
    
    # Suggestions based on status
    if health['overall_status'] == 'unhealthy':
        print("\nDeployment Suggestions:")
        print("1. Ensure Neon database endpoint is enabled")
        print("2. Verify DATABASE_URL environment variable is set correctly")
        print("3. Check that SESSION_SECRET is configured")
        print("4. Review deployment logs for additional errors")
    elif health['overall_status'] == 'degraded':
        print("\nOptimization Suggestions:")
        print("1. Configure optional environment variables for full functionality")
        print("2. Check agent initialization logs")
    else:
        print("\n✅ Deployment is healthy and ready!")
    
    print("="*60)

if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(level=logging.INFO)
    print_health_report()
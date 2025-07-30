from app import app

# Add deployment health check on startup
def check_deployment_readiness():
    """Check if deployment is ready before starting"""
    try:
        from deployment_health import check_deployment_health
        health = check_deployment_health()
        
        if health['overall_status'] == 'unhealthy':
            print("⚠️  Deployment health check failed!")
            for error in health['errors']:
                print(f"❌ {error}")
            print("The application may not work correctly until these issues are resolved.")
        elif health['overall_status'] == 'degraded':
            print("⚠️  Deployment has warnings:")
            for warning in health['warnings']:
                print(f"⚠️  {warning}")
        else:
            print("✅ Deployment health check passed!")
            
    except Exception as e:
        print(f"⚠️  Could not run deployment health check: {e}")

if __name__ == "__main__":
    check_deployment_readiness()
    app.run(debug=True, host="0.0.0.0", port=5000)

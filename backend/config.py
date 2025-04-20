import os

class Config:
    """Base configuration"""
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
    DEBUG = False
    TESTING = False
    
    # Database
    DB_PATH = os.environ.get('DB_PATH', 'forum_tracker.db')
    
    # Scheduler
    CHECK_INTERVAL_SECONDS = int(os.environ.get('CHECK_INTERVAL_SECONDS', 7200))  # Default: 2 hours
    
    # Download Providers
    DOWNLOAD_PROVIDERS = [
        'filejoker.net', 
        'k2s.cc', 
        'filespace.com', 
        'rg.to', 
        'fboom.me',
        'fileboom.me',
        'filespace',
        'depositfiles',  
        'filefox.cc',
        'rapidgator'
    ]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    CHECK_INTERVAL_SECONDS = int(os.environ.get('CHECK_INTERVAL_SECONDS', 300))  # Default: 5 minutes in dev

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DB_PATH = 'forum_tracker_test.db'
    CHECK_INTERVAL_SECONDS = 10  # Quick interval for testing

class ProductionConfig(Config):
    """Production configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in environment
    # Vous pouvez personnaliser les fournisseurs en production si nécessaire
    DOWNLOAD_PROVIDERS = os.environ.get('DOWNLOAD_PROVIDERS', ','.join(Config.DOWNLOAD_PROVIDERS)).split(',')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])
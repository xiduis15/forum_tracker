import os
import logging
from flask import Flask, render_template, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from .models import init_db
from .api import api
from .config import get_config
from .scheduler import SchedulerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application"""
    # Create app instance
    app = Flask(__name__, 
                static_folder='../frontend',
                template_folder='../frontend')
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Register API blueprint
    app.register_blueprint(api)
    
    # Initialize database
    init_db(app.config['DB_PATH'])
    
    # Create test data directory if it doesn't exist
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    os.makedirs(test_data_dir, exist_ok=True)
    
    # Copy test HTML if needed
    test_html_path = os.path.join(test_data_dir, 'example-forum.html')
    if not os.path.exists(test_html_path):
        try:
            # Try to copy from documents directory if available
            from pathlib import Path
            docs_dir = Path(__file__).parent.parent / 'documents'
            example_html = docs_dir / 'example-forum.html'
            
            if example_html.exists():
                import shutil
                shutil.copy(example_html, test_html_path)
                logger.info(f"Copied example HTML to {test_html_path}")
            else:
                logger.warning(f"Example HTML not found at {example_html}, tests may fail")
        except Exception as e:
            logger.error(f"Error copying example HTML: {e}")
    
    # Routes
    @app.route('/')
    def index():
        """Serve the main page"""
        return render_template('index.html')
    
    @app.route('/<path:path>')
    def static_files(path):
        """Serve static files"""
        return send_from_directory(app.static_folder, path)
    
    # Initialize and start scheduler
    scheduler = SchedulerService(check_interval_seconds=app.config['CHECK_INTERVAL_SECONDS'])
    scheduler.start()
    
    # Register shutdown function to stop scheduler
    atexit.register(lambda: scheduler.stop())
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)

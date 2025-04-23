from flask import Blueprint, request, jsonify
import logging
from .services import get_db_service
from .scrapers import detect_forum_type
from .scheduler import SchedulerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create blueprint
api = Blueprint('api', __name__)

# Services
db_service = get_db_service()
scheduler = SchedulerService()

# API Routes

# Performers API
@api.route('/api/performers', methods=['GET'])
def get_performers():
    """Get all performers"""
    performers = db_service.get_all_performers()
    return jsonify({
        'success': True,
        'performers': [performer.to_dict() for performer in performers]
    })

@api.route('/api/performers/<int:performer_id>', methods=['GET'])
def get_performer(performer_id):
    """Get a performer by ID"""
    performer = db_service.get_performer(performer_id)
    if performer:
        return jsonify({
            'success': True,
            'performer': performer.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': f"Performer with ID {performer_id} not found"
        }), 404

@api.route('/api/performers', methods=['POST'])
def create_performer():
    """Create a new performer"""
    data = request.json
    if not data or 'name' not in data:
        return jsonify({
            'success': False,
            'error': "Name is required"
        }), 400
    
    name = data['name']
    is_active = data.get('is_active', True)
    
    success, performer, error = db_service.create_performer(name, is_active)
    
    if success:
        return jsonify({
            'success': True,
            'performer': performer.to_dict()
        }), 201
    else:
        return jsonify({
            'success': False,
            'error': error
        }), 400

@api.route('/api/performers/<int:performer_id>', methods=['PUT'])
def update_performer(performer_id):
    """Update a performer"""
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': "No data provided"
        }), 400
    
    name = data.get('name')
    is_active = data.get('is_active')
    
    success, performer, error = db_service.update_performer(performer_id, name, is_active)
    
    if success:
        return jsonify({
            'success': True,
            'performer': performer.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': error
        }), 404 if "not found" in error else 400

@api.route('/api/performers/<int:performer_id>', methods=['DELETE'])
def delete_performer(performer_id):
    """Delete a performer"""
    success, error = db_service.delete_performer(performer_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': f"Performer with ID {performer_id} deleted"
        })
    else:
        return jsonify({
            'success': False,
            'error': error
        }), 404 if "not found" in error else 400

# Threads API
@api.route('/api/threads', methods=['GET'])
def get_threads():
    """Get all threads"""
    threads = db_service.get_all_threads()
    return jsonify({
        'success': True,
        'threads': [thread.to_dict() for thread in threads]
    })

@api.route('/api/performers/<int:performer_id>/threads', methods=['GET'])
def get_performer_threads(performer_id):
    """Get all threads for a performer"""
    performer = db_service.get_performer(performer_id)
    if not performer:
        return jsonify({
            'success': False,
            'error': f"Performer with ID {performer_id} not found"
        }), 404
    
    threads = db_service.get_threads_by_performer(performer_id)
    return jsonify({
        'success': True,
        'threads': [thread.to_dict() for thread in threads]
    })

@api.route('/api/threads/<int:thread_id>', methods=['GET'])
def get_thread(thread_id):
    """Get a thread by ID"""
    thread = db_service.get_thread(thread_id)
    if thread:
        return jsonify({
            'success': True,
            'thread': thread.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': f"Thread with ID {thread_id} not found"
        }), 404

@api.route('/api/performers/<int:performer_id>/threads', methods=['POST'])
def create_thread(performer_id):
    """Create a new thread for a performer"""
    data = request.json
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': "URL is required"
        }), 400
    
    url = data['url']
    
    # Auto-detect forum type if not provided
    forum_type = data.get('forum_type')
    if not forum_type:
        try:
            forum_type = detect_forum_type(url)
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    success, thread, error = db_service.create_thread(performer_id, url, forum_type)
    
    if success:
        return jsonify({
            'success': True,
            'thread': thread.to_dict()
        }), 201
    else:
        return jsonify({
            'success': False,
            'error': error
        }), 400

@api.route('/api/threads/<int:thread_id>', methods=['PUT'])
def update_thread(thread_id):
    """Update a thread"""
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': "No data provided"
        }), 400
    
    url = data.get('url')
    forum_type = data.get('forum_type')
    last_post_id = data.get('last_post_id')
    
    success, thread, error = db_service.update_thread(thread_id, url, forum_type, last_post_id)
    
    if success:
        return jsonify({
            'success': True,
            'thread': thread.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'error': error
        }), 404 if "not found" in error else 400

@api.route('/api/threads/<int:thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    """Delete a thread"""
    success, error = db_service.delete_thread(thread_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': f"Thread with ID {thread_id} deleted"
        })
    else:
        return jsonify({
            'success': False,
            'error': error
        }), 404 if "not found" in error else 400

# Check API
@api.route('/api/check/thread/<int:thread_id>', methods=['GET'])
def check_thread(thread_id):
    """Check a thread for new posts"""
    new_posts = scheduler.run_single_check(thread_id=thread_id)
    return jsonify({
        'success': True,
        'new_posts': new_posts
    })

@api.route('/api/check/performer/<int:performer_id>', methods=['GET'])
def check_performer(performer_id):
    """Check all threads of a performer for new posts"""
    new_posts = scheduler.run_single_check(performer_id=performer_id)
    return jsonify({
        'success': True,
        'new_posts': new_posts
    })

@api.route('/api/check/all', methods=['GET'])
def check_all():
    """Check all threads of all active performers for new posts"""
    try:
        new_posts = scheduler.run_single_check()
        logger.info(f"API check_all returned {len(new_posts)} posts")
        return jsonify({
            'success': True,
            'new_posts': new_posts,
            'count': len(new_posts)
        })
    except Exception as e:
        logger.error(f"Error in check_all API: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'new_posts': []
        }), 500

# Test API with the example PlanetSuzy HTML
@api.route('/api/test/planetsuzy', methods=['GET'])
def test_planetsuzy():
    """Test PlanetSuzy scraper with the example HTML"""
    try:
        # Import necessary modules
        from .scrapers import PlanetSuzyScraper
        from bs4 import BeautifulSoup
        import os
        
        # Path to the test HTML file (this is just for testing)
        html_path = os.path.join(os.path.dirname(__file__), 'test_data', 'example-forum.html')
        
        # Load HTML from file or use a mock HTML string
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except FileNotFoundError:
            # For testing purposes, we'll use a hardcoded HTML if the file doesn't exist
            # In a real application, you would ensure the test file exists
            return jsonify({
                'success': False,
                'error': "Test HTML file not found. Please ensure it's placed in the correct location."
            }), 404
        
        # Create scraper instance
        scraper = PlanetSuzyScraper("http://www.planetsuzy.org/t894033-p36-victoria-june.html")
        
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract posts
        posts = scraper.extract_posts(soup)
        
        # Convert to dictionaries for JSON response
        post_dicts = [post.to_dict() for post in posts]
        
        return jsonify({
            'success': True,
            'posts': post_dicts,
            'post_count': len(post_dicts)
        })
        
    except Exception as e:
        logger.error(f"Error in test_planetsuzy: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
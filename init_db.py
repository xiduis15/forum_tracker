import os
import argparse
from backend.models import init_db, Performer, Thread

def create_sample_data(session):
    """Create sample data for testing"""
    print("Creating sample data...")
    
    # Create sample performers
    performer1 = Performer(name="Victoria June", is_active=True)
    performer2 = Performer(name="Emily Willis", is_active=True)
    performer3 = Performer(name="Angela White", is_active=False)
    
    session.add_all([performer1, performer2, performer3])
    session.commit()
    
    # Create sample threads
    thread1 = Thread(
        performer_id=performer1.id,
        url="http://www.planetsuzy.org/t894033-p36-victoria-june.html",
        forum_type="planetsuzy"
    )
    
    thread2 = Thread(
        performer_id=performer2.id,
        url="http://www.planetsuzy.org/t123456-emily-willis.html",
        forum_type="planetsuzy"
    )
    
    session.add_all([thread1, thread2])
    session.commit()
    
    print(f"Created {session.query(Performer).count()} performers")
    print(f"Created {session.query(Thread).count()} threads")

def main():
    parser = argparse.ArgumentParser(description="Initialize the database and optionally create sample data")
    parser.add_argument('--with-sample-data', action='store_true', help='Create sample data')
    parser.add_argument('--db-path', default='forum_tracker.db', help='Path to the database file')
    
    args = parser.parse_args()
    
    # Delete existing database if it exists
    if os.path.exists(args.db_path):
        print(f"Removing existing database: {args.db_path}")
        os.remove(args.db_path)
    
    # Initialize the database
    print(f"Initializing database: {args.db_path}")
    session = init_db(args.db_path)
    
    # Create sample data if requested
    if args.with_sample_data:
        create_sample_data(session)
    
    print("Database initialization complete!")

if __name__ == "__main__":
    main()

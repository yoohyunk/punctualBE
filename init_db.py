"""
Database initialization script
This script creates or recreates database tables.
"""
from app import create_app
from app.models import db

def init_database():
    """Initialize database"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Print table list
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nCreated tables: {', '.join(tables)}")

def drop_database():
    """Drop database tables (Warning!)"""
    app = create_app()
    
    response = input("⚠️  Are you sure you want to drop all tables? (yes/no): ")
    if response.lower() == 'yes':
        with app.app_context():
            print("Dropping database tables...")
            db.drop_all()
            print("✅ All tables dropped.")
    else:
        print("Cancelled.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--drop':
        drop_database()
    else:
        init_database()


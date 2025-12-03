from main import app
from database import db

def migrate_users_table():
    with app.app_context():
        with db.engine.connect() as conn:
            print("Adding new columns to users table...")
            
            columns_to_add = [
                ("name", "VARCHAR(200)"),
                ("email", "VARCHAR(255)"),
                ("contact_number", "VARCHAR(50)"),
                ("location", "VARCHAR(200)"),
                ("institute_name", "VARCHAR(255)"),
                ("college_name", "VARCHAR(255)"),
                ("degree", "VARCHAR(200)"),
                ("year_of_passing", "VARCHAR(50)"),
                ("resume_url", "TEXT")
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    query = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
                    conn.execute(db.text(query))
                    conn.commit()
                    print(f"✓ Added column: {column_name}")
                except Exception as e:
                    print(f"✗ Column {column_name} might already exist or error occurred: {e}")
            
            print("\nMigration completed!")

if __name__ == '__main__':
    migrate_users_table()

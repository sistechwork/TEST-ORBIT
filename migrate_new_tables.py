import os
from flask import Flask
from database import db
from models import AdminSecret, ActivityLog

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
else:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

with app.app_context():
    print("Creating admin_secrets and activity_logs tables...")
    db.create_all()
    print("Migration completed successfully!")
    print(f"Tables created: {db.engine.table_names()}")

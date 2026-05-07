from main import app
from models import AdminSettings
from database import db

with app.app_context():
    setting = AdminSettings.query.filter_by(setting_key='block_password').first()
    if setting:
        print(f"Current block_password: {setting.setting_value}")
    else:
        print("Block password not set in database, using default: exam2024")

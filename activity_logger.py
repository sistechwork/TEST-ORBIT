from database import db
from models import ActivityLog
from flask import request

def log_activity(user_id=None, activity_type='', description=''):
    try:
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent', '')[:255] if request else ''
        
        activity = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(activity)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        db.session.rollback()
        return False

def get_recent_activities(limit=50, offset=0, activity_type=None, user_id=None):
    try:
        query = ActivityLog.query
        
        if activity_type:
            query = query.filter_by(activity_type=activity_type)
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        activities = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit).all()
        total_count = query.count()
        
        return activities, total_count
    except Exception as e:
        print(f"Error fetching activities: {e}")
        return [], 0

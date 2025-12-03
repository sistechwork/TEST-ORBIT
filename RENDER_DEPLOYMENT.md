# 🚀 Deploy Exam Portal to Render

## Method 1: Using render.yaml (Recommended - Blueprint)

1. **Push your code to GitHub** (if not already done)
   
2. **Go to Render Dashboard**
   - Visit https://render.com and sign in
   - Click "New" → "Blueprint"

3. **Connect Repository**
   - Select your GitHub repository
   - Render will automatically detect the `render.yaml` file
   - Click "Apply"

4. **Automatic Setup**
   - Render will create:
     - Web service running the Flask app
     - PostgreSQL database
     - Environment variables

5. **Done!** Your app will be deployed automatically

---

## Method 2: Manual Setup

### Step 1: Create PostgreSQL Database

1. In Render Dashboard, click "New" → "PostgreSQL"
2. Fill in:
   - **Name**: `exam-portal-db`
   - **Database**: `exam_portal`
   - **Plan**: Free
3. Click "Create Database"
4. **Copy the Internal Database URL** (it looks like `postgres://...`)

### Step 2: Create Web Service

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Fill in settings:
   - **Name**: `exam-portal`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free

### Step 3: Add Environment Variables

In the "Environment" section, add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Paste the Internal Database URL from Step 1 |
| `SESSION_SECRET` | Any random string (e.g., `your-secret-key-here-123`) |
| `PYTHON_VERSION` | `3.11.0` |

### Step 4: Deploy

1. Click "Create Web Service"
2. Wait for deployment to complete (5-10 minutes)
3. Your app will be live at: `https://your-app-name.onrender.com`

---

## 🔧 Important Configuration Details

### Common Errors and Fixes

**1. Database URI Error: `Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set`**

This happens because:
- Render provides DATABASE_URL in format: `postgres://...`
- SQLAlchemy 2.0+ requires format: `postgresql://...`
- **FIXED**: The code now automatically converts the URL format

**2. Python 3.13 Compatibility Errors**

**Error A**: `AssertionError: Class SQLCoreOperations...`
- Old SQLAlchemy 2.0.23 is incompatible with Python 3.13
- **FIXED**: Updated to SQLAlchemy 2.0.36 (Python 3.13 compatible)

**Error B**: `ImportError: undefined symbol: _PyInterpreterState_Get`
- psycopg2-binary 2.9.9 doesn't support Python 3.13
- **FIXED**: Updated to psycopg2-binary 2.9.11 (Python 3.13 compatible)

**3. Module Not Found Error: `ModuleNotFoundError: No module named 'app'`**

This occurred because:
- Render was trying to run: `gunicorn app:app`
- But your Flask application is in: `main.py`
- Correct command: `gunicorn main:app`

### Required Environment Variables

- **DATABASE_URL**: PostgreSQL connection string
- **SESSION_SECRET**: Secret key for Flask sessions
- **PYTHON_VERSION**: Python version to use (3.11.0)

### First Time Setup After Deployment

After your app is deployed, you need to initialize the database:

1. Open Render Shell (in your web service, click "Shell")
2. Run these commands:
   ```bash
   python
   >>> from main import app, db
   >>> from models import *
   >>> with app.app_context():
   ...     db.create_all()
   ...     exec(open('seed_data.py').read())
   >>> exit()
   ```

This will:
- Create all database tables
- Add sample questions to the exam
- Set up the admin account

### Admin Login

- **Username**: `admin@vcodez`
- **Password**: `admin@123`

---

## 🎯 Troubleshooting

### Database Connection Issues

If you get database errors:
1. Make sure DATABASE_URL is correctly set
2. Verify the database is in the same region as web service
3. Check that the database is using the Internal URL (not External)

### App Not Starting

1. Check the logs in Render dashboard
2. Verify all environment variables are set
3. Make sure the start command is: `gunicorn main:app --bind 0.0.0.0:$PORT`

### Static Files Not Loading

Add this to your `main.py` if not already present:
```python
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
```

---

## 📝 File Changes Made

1. **render.yaml** - Blueprint configuration for automatic deployment
2. **Procfile** - Alternative deployment configuration
3. **requirements.txt** - Cleaned up and added versions
4. **This file** - Deployment instructions

---

## ✅ Checklist Before Deploying

- [ ] Code pushed to GitHub
- [ ] requirements.txt includes all dependencies
- [ ] Environment variables configured
- [ ] Database created and connected
- [ ] Start command uses `main:app` not `app:app`

---

**🎉 Your exam portal will be live and accessible worldwide!**

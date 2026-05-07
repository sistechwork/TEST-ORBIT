# GradTwin - Exam Portal

## Overview
GradTwin is a secure online examination system built with Flask, HTML, CSS, and PostgreSQL. It features robust anti-cheating measures, comprehensive user authentication, and an administrative dashboard for monitoring student performance. The system's primary purpose is to provide a reliable and cheat-proof environment for conducting online exams, ensuring fair assessments and efficient management of examination data. Key capabilities include real-time proctoring (camera and audio), dynamic question rendering, and detailed performance analytics for administrators.

## User Preferences
I want iterative development. Ask before making major changes. I prefer detailed explanations.

## Branding (Updated December 2, 2025)
- **Brand Name**: GradTwin
- **Logo**: Blue orbital design (static/images/logo.png)
- **Primary Color**: #3B82F6 (Bright Blue)
- **Secondary Colors**: #1E40AF (Dark Blue), #1E3A8A (Navy), #60A5FA (Light Blue)
- **Background**: Light grey gradient (#f8fafc to #f1f5f9 to #e2e8f0 to #cbd5e1)
- **Theme**: Clean, modern light theme with white cards, subtle shadows, and blue accents
- **All pages updated with consistent GradTwin branding and light grey/white color scheme**

## System Architecture

### UI/UX Decisions
The portal features a modern, professional UI with consistent styling across all pages (Login, Register, Exam, Admin Dashboard). Key design elements include:
- Dark animated gradient backgrounds (navy/blue tones) with glassmorphism effects and backdrop blur.
- Card-based layouts with subtle shadows and hover effects for question cards and student results.
- Professional white question boxes with blue gradient question numbers and glowing points badges.
- Modern option buttons with interactive hover effects and blue gradient on selection.
- Enhanced form inputs with focus animations and professional text styling.
- Visual score badges and color-coded severity levels in the admin dashboard.

### Technical Implementations
- **Proctoring System**: Integrates client-side MediaPipe for real-time face detection and Web Audio API for audio monitoring (RMS energy calculation). Server-side Flask API endpoints handle violation logging with validation and rate limiting.
- **Anti-Cheating Mechanisms**: Includes detection and prevention of page reloads, tab switching, copy/paste, right-click, developer tools (F12, Ctrl+Shift+I/J), and view source (Ctrl+U). Violations trigger a password prompt for continuation.
- **Password Prevention**: Advanced techniques to prevent browser password managers from interfering with input fields, including hidden decoy fields and `autocomplete="off"`.
- **Exam Timer**: Live countdown timer on the exam page with visual cues for low time, persisting across page reloads, and auto-submitting upon completion.
- **Database Management**: Utilizes SQLAlchemy ORM for interacting with PostgreSQL. `database.py` handles configuration, `models.py` defines schema, and `seed_data.py` populates initial data.
- **Deployment**: Configured for Replit with Python 3.11 and PostgreSQL (using built-in Replit database), and for Render using `render.yaml` and `Procfile` with Gunicorn, ensuring compatibility across environments.

### Feature Specifications
- **User Features**: Secure registration/login, multi-type question exams (MCQ, short answer, paragraph), comprehensive anti-cheating suite, proctored environment, and post-exam completion message.
- **Admin Features**: Admin login (`admin@vcodez` / `admin@123`), detailed student result analytics (expandable per student), score badges, question management (create/delete), block password configuration, and proctoring violation timeline.

### System Design Choices
- **Backend**: Python Flask 3.0.0 for robust API and server-side logic.
- **Database**: PostgreSQL for reliable data storage, integrated via Replit's services.
- **ORM**: Flask-SQLAlchemy 3.1.1 for efficient database interactions.
- **Security**: Werkzeug for password hashing, session-based authentication, server-side block password verification, and cryptographically secure session keys.
- **Frontend**: HTML5, CSS3, and Vanilla JavaScript for a dynamic and interactive user experience.
- **File Structure**: Organized with `main.py` (Flask app), `database.py`, `models.py`, `seed_data.py`, `requirements.txt`, and dedicated `templates/` and `static/` directories.

## External Dependencies
- **PostgreSQL**: Primary database for all application data (user credentials, questions, responses, admin settings, proctoring events).
- **MediaPipe Face Detection**: Client-side library used for real-time camera-based proctoring.
- **Web Audio API**: Client-side API used for real-time microphone-based proctoring.
- **Flask**: Python web framework.
- **Flask-SQLAlchemy**: ORM for Flask.
- **psycopg2-binary**: PostgreSQL adapter for Python.
- **Werkzeug**: WSGI utility library, used for security features like password hashing.
- **Gunicorn**: WSGI HTTP server for production deployment.

## Replit Setup (December 3, 2025 - GitHub Import)
- **Environment**: Python 3.11 installed via Replit modules
- **Database**: Using SQLite (exam_portal.db) as fallback. To use PostgreSQL, create a database in Replit UI (Database tool > Create database) and DATABASE_URL will be automatically set
- **Dependencies**: All Python packages installed via packager tool from requirements.txt (Flask 3.0.0, Flask-SQLAlchemy 3.1.1, Flask-Mail, pandas, openpyxl, cryptography, etc.)
- **Workflow**: Configured to run `python main.py` on port 5000 with webview output
- **Deployment**: Configured for autoscale deployment using Gunicorn with command: `gunicorn --bind=0.0.0.0:5000 --reuse-port main:app`
- **Environment Variables**: 
  - `SESSION_SECRET`: Automatically set by Replit (secret)
  - `ENCRYPTION_KEY`: Generated and set for secure data encryption (shared): `WmnSwh3Jzil0uYaG5rohfLof7QmptY8nX6jTK-MgiIw=`
  - `DATABASE_URL`: Optional - create PostgreSQL database via Replit UI to automatically set this
  - Email configuration: `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS` (set to defaults, configure `MAIL_USERNAME` and `MAIL_PASSWORD` for email functionality)
- **Database Initialization**: Database seeded with 10 sample questions and default block password 'exam2024'
- **Admin Credentials**: Username: `admin@vcodez`, Password: `admin@123`
- **Default Block Password**: `exam2024` (configurable in admin dashboard)
- **Application Status**: Running successfully on port 5000, admin login accessible, database connected
- **File Structure**: Project files moved from `exam/` subdirectory to root for proper Replit setup
- **Git Ignore**: Added comprehensive .gitignore for Python projects excluding database files, cache, and IDE files

## Email Configuration
To enable email sending for bulk user imports:
1. Set environment variables in Replit Secrets:
   - `MAIL_SERVER`: SMTP server (default: smtp.gmail.com)
   - `MAIL_PORT`: SMTP port (default: 587)
   - `MAIL_USERNAME`: Your email address
   - `MAIL_PASSWORD`: Your email app password (for Gmail: https://support.google.com/accounts/answer/185833)
2. The system will automatically send credentials to users when they are created via bulk import or individual add

## Recent Updates (December 3, 2025)
1. **Admin Dark Theme Redesign**: Admin interface (login and dashboard) now uses a dark theme with red/orange accents to differentiate from user interface
2. **Admin Login Styling**: Dark animated gradient background (#0a0f1f to #7f1d1d/#b91c1c), red/orange floating shapes, and red/orange accent colors
3. **Admin Dashboard Styling**: Dark body background, dark cards/sections, white text, red/orange accent colors throughout
4. **Visual Differentiation**: User interface uses blue accents (#3B82F6), admin interface uses red/orange accents (#ef4444, #dc2626, #fb923c)
5. **Consistent Admin Theme**: All admin pages now have cohesive dark backgrounds with light text and red/orange interactive elements

## Previous Updates (December 2, 2025)
1. **Light Theme Redesign**: Changed from dark blue backgrounds to light grey/white theme
2. **New Background Colors**: Light gradient backgrounds (#f8fafc, #f1f5f9, #e2e8f0, #cbd5e1)
3. **White Cards**: All cards, containers, and panels now use white backgrounds with subtle borders
4. **Updated Sidebars**: Admin sidebars now use light grey gradient instead of dark blue
5. **Improved Readability**: Dark text on light backgrounds for better accessibility
6. **Consistent Styling**: All templates updated with cohesive light theme (login, register, exam, verification, admin pages)

## Previous Updates (November 17, 2025)
1. **Floating Notifications**: Replaced flash messages with modern toast notifications at top-right
2. **Enhanced User Model**: Added 9 fields - name, email, contact_number, location, institute_name, college_name, degree, year_of_passing, resume_url
3. **Bulk Import**: CSV/Excel upload with automatic password generation and email delivery
4. **User Management**: Add, update, and delete users through admin dashboard
5. **Question Updates**: Edit existing questions (text, points, options) in admin dashboard
6. **User Profile**: New profile page showing all user details and exam status

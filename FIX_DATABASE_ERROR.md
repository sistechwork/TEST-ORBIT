# 🔧 Fix: Render Deployment Errors

## Common Errors

### 1. DATABASE_URL Not Set
```
Error: Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set.
```

**OR**

```
RuntimeError: DATABASE_URL environment variable is not set.
```

### 2. psycopg2 Python 3.13 Compatibility
```
ImportError: undefined symbol: _PyInterpreterState_Get
```

**FIXED**: Updated to psycopg2-binary==2.9.11 (Python 3.13 compatible)

## Root Cause
The `DATABASE_URL` environment variable is missing from your Render deployment. This happens when the database and web service are not properly connected.

---

## ✅ Solution - Choose Your Deployment Method

### Option A: Using Blueprint (render.yaml) - RECOMMENDED

If you deployed using the Blueprint method, Render should automatically create the database and set the variable. If it didn't:

1. **Go to Render Dashboard** (https://dashboard.render.com)

2. **Check if Database Exists**:
   - Look for a service named `exam-portal-db`
   - If it doesn't exist, the Blueprint didn't create it properly

3. **Re-deploy Using Blueprint**:
   - Delete the existing web service (if any)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will read `render.yaml` and create BOTH the database and web service
   - Click "Apply"

4. **Wait for deployment** - The database URL will be automatically set

---

### Option B: Manual Setup (If Blueprint Didn't Work)

#### Step 1: Create PostgreSQL Database

1. Go to Render Dashboard
2. Click "New" → "PostgreSQL"
3. Fill in:
   - **Name**: `exam-portal-db`
   - **Database**: `exam_portal`
   - **Region**: Choose closest to you
   - **Plan**: Free
4. Click "Create Database"
5. **COPY the Internal Database URL** - it looks like:
   ```
   postgres://username:password@hostname/database
   ```
   (Find it under "Connections" → "Internal Database URL")

#### Step 2: Add DATABASE_URL to Web Service

1. Go to your web service in Render
2. Click "Environment" in the left sidebar
3. Click "Add Environment Variable"
4. Add:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the Internal Database URL you copied
5. Click "Save Changes"
6. Your service will automatically redeploy

#### Step 3: Add Other Environment Variables

While you're in the Environment section, also add:

| Key | Value |
|-----|-------|
| `SESSION_SECRET` | Any random string (e.g., `my-secret-key-12345`) |

---

## 🎯 Quick Fix Checklist

- [ ] PostgreSQL database created in Render
- [ ] DATABASE_URL environment variable set in web service
- [ ] DATABASE_URL copied from "Internal Database URL" (not External)
- [ ] SESSION_SECRET environment variable set
- [ ] Web service redeployed (happens automatically)

---

## 🔍 How to Verify It's Working

### Check Environment Variables in Render:

1. Go to your web service
2. Click "Shell" (bottom left)
3. Run this command:
   ```bash
   echo $DATABASE_URL
   ```
4. You should see a URL like: `postgres://user:pass@host/database`

### Check the Logs:

1. Go to your web service
2. Click "Logs"
3. Look for errors - if DATABASE_URL is set correctly, you should see:
   ```
   Starting gunicorn...
   Listening at: http://0.0.0.0:10000
   ```

---

## 📋 Common Mistakes

❌ **Using External Database URL instead of Internal**
- ✅ Use: `postgres://dpg-xxx-a/exam_portal` (Internal)
- ❌ Don't use: `postgres://dpg-xxx.oregon-postgres.render.com/exam_portal` (External)

❌ **Creating web service before database**
- ✅ Create database first, then add DATABASE_URL to web service

❌ **Not redeploying after adding environment variable**
- ✅ Render auto-redeploys, but you can click "Manual Deploy" → "Deploy latest commit"

---

## 🚀 After DATABASE_URL is Set

Once the environment variable is set and the service redeploys:

1. Visit your Render URL
2. You should see the login page
3. Open Render Shell and run:
   ```bash
   python seed_data.py
   ```
4. This creates 10 sample exam questions

---

## 💡 Alternative: Use Render Blueprint (Easiest Method)

The easiest way is to start fresh with the Blueprint:

1. **Delete your current web service** (if any)
2. **Delete the database** (if created separately)
3. **Start Over**:
   - Click "New" → "Blueprint"
   - Select your GitHub repo
   - Render reads `render.yaml` and creates EVERYTHING automatically
   - Database + Web Service + Environment Variables all set up!

Your `render.yaml` file already has the correct configuration:

```yaml
services:
  - type: web
    name: exam-portal
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: exam-portal-db  # Links to database automatically
          property: connectionString
```

This tells Render to automatically set `DATABASE_URL` from the database.

---

## ✅ Success!

When everything is working, you'll see:
- ✅ Build completes successfully
- ✅ Service shows "Live" status
- ✅ Visiting your URL shows the login page
- ✅ No errors in logs

---

**Need more help?** Check `DEPLOYMENT_CHECKLIST.md` or `RENDER_DEPLOYMENT.md`

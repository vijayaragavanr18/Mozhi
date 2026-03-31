# MozhiSense Deployment Guide

## Overview
- **Frontend**: Deploy to Vercel (Free) - React + Vite
- **Backend**: Deploy to Railway (Free Tier) - Python FastAPI
- **Database**: SQLite (included in repo)

## Prerequisites
1. GitHub account (to store your code)
2. Vercel account (sign up with GitHub)
3. Railway account (sign up with GitHub)

---

## Step 1: Prepare Your Repository

### 1.1 Initialize Git (if not done)
```bash
cd /path/to/MozhiSense-f
git init
git add .
git commit -m "Initial commit: MozhiSense app"
```

### 1.2 Create `.gitignore` in both directories
**Backend .gitignore** (`mozhisense-backend/.gitignore`):
```
__pycache__/
*.py[cod]
*$py.class
*.so
.env
.venv
env/
venv/
*.db
```

**Frontend .gitignore** (`Frontend_Sense/.gitignore`):
```
node_modules/
dist/
.env.local
.env.*.local
```

---

## Step 2: Deploy Frontend to Vercel (5 minutes)

### 2.1 Push code to GitHub
1. Create a new repo on GitHub
2. Add remote: `git remote add origin https://github.com/YOUR_USERNAME/MozhiSense.git`
3. Push: `git push -u origin main`

### 2.2 Deploy to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click **"New Project"**
3. Select your **MozhiSense** repo
4. Configure:
   - **Root Directory**: `Frontend_Sense/` (IMPORTANT!)
   - **Framework**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variables:
   - Key: `VITE_API_URL`
   - Value: `https://your-backend-domain.railway.app` (you'll get this after deploying backend)
6. Click **Deploy** ✅

**Your frontend is now live at**: `https://mozhisense.vercel.app` (example URL)

---

## Step 3: Deploy Backend to Railway (10 minutes)

### 3.1 Prepare Backend

Ensure these files exist in `mozhisense-backend/`:
- ✅ `Procfile` (included)
- ✅ `.env.example` (included)
- ✅ `runtime.txt` (included)
- ✅ `requirements.txt` (updated with gunicorn)

### 3.2 Create `.env` file
Copy `.env.example`:
```bash
cp mozhisense-backend/.env.example mozhisense-backend/.env
```

Edit `mozhisense-backend/.env`:
```
FRONTEND_URL=https://mozhisense.vercel.app
BACKEND_URL=https://your-backend-domain.railway.app
USE_OLLAMA=false
CORS_ORIGINS=https://mozhisense.vercel.app,http://localhost:5173,http://localhost:3000
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen:1.5b
OLLAMA_TIMEOUT_SECONDS=4.5
```

### 3.3 Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub Repo**
3. Select your **MozhiSense** repo
4. Click **Add Service** → **GitHub Repo**
5. Add environment variables:
   - Copy all from your `.env` file
6. Railway will auto-detect `Procfile` and start deployment
7. Wait for build completion (~3-5 minutes)

**Your backend URL**: Click your service → Settings → Domains → Copy the assigned domain

---

## Step 4: Update Frontend with Backend URL

### 4.1 Update Vercel Environment Variable
1. Go to Vercel Dashboard → **MozhiSense** Project
2. **Settings** → **Environment Variables**
3. Update `VITE_API_URL` to your Railway backend URL
4. Vercel auto-rebuilds 🚀

---

## Testing

### Test Backend Endpoints
```bash
# Check health
curl https://your-backend.railway.app/

# Get random challenge
curl https://your-backend.railway.app/api/random-challenge

# Get challenges by word
curl https://your-backend.railway.app/api/challenge/என
```

### Test Frontend
Open `https://mozhisense.vercel.app` in browser

---

## Troubleshooting

### Frontend not loading data?
- Check `VITE_API_URL` in Vercel environment
- Check browser DevTools → Network tab for API errors
- Verify backend CORS_ORIGINS include your frontend URL

### Backend errors?
- Check Railway Logs: Railway Dashboard → your service → Logs
- Common issues:
  - Missing `.env` variables
  - Database file not found
  - CORS origin mismatch

### Database not found?
- SQLite database (`mozhisense.db`) must be in repo
- If not, run setup locally first (check `scripts/` folder)

---

## Future Enhancements

### Enable AI Generation (Optional)
To enable Ollama on production:
1. Use **Groq Free API** or **Ollama Cloud**
2. Update `USE_OLLAMA=true` in Railway `.env`
3. Add `OLLAMA_URL` pointing to cloud service

### Custom Domains (Optional)
- Vercel: Settings → Domains (add custom domain)
- Railway: Create CNAME record pointing to Railway domain

### Database Backup
- Regularly download `mozhisense.db` from your server
- Keep this safely backed up

---

## Cost Summary
- **Vercel**: FREE (unlimited projects, 100GB bandwidth/month)
- **Railway**: FREE ($5 free tier/month)
- **Total**: $0/month ✅


# Deployment Checklist

## Prerequisites
- [ ] GitHub account created
- [ ] Vercel account created (link GitHub)
- [ ] Railway account created (link GitHub)
- [ ] Code pushed to GitHub

## Backend Setup
- [ ] Verify `Procfile` exists in `mozhisense-backend/`
- [ ] Verify `.env.example` exists
- [ ] Verify `runtime.txt` exists (Python 3.11.9)
- [ ] Verify `requirements.txt` has `gunicorn`
- [ ] Create `.env` from `.env.example`
- [ ] Add all environment variables to `.env`

## Frontend Setup  
- [ ] Verify `vercel.json` exists in `Frontend_Sense/`
- [ ] Verify `.env.example` exists with `VITE_API_URL`
- [ ] Create `.env.local` with backend API URL

## Deployment - Vercel (Frontend)
- [ ] Go to vercel.com
- [ ] Import your GitHub repository
- [ ] Set Root Directory: `Frontend_Sense/`
- [ ] Add environment variable `VITE_API_URL` 
- [ ] Deploy
- [ ] Note your frontend URL: https://_____.vercel.app
- [ ] Update CORS_ORIGINS in Railway with this URL

## Deployment - Railway (Backend)
- [ ] Go to railway.app
- [ ] Create new project from GitHub
- [ ] Select your MozhiSense repo
- [ ] Add all environment variables from `.env`
- [ ] Wait for deployment
- [ ] Note your backend domain from Railway settings
- [ ] Update Vercel `VITE_API_URL` with this domain

## Final Testing
- [ ] Open frontend URL in browser
- [ ] Try fetching a random challenge
- [ ] Check browser console for CORS errors
- [ ] Test backend health endpoint: `/`
- [ ] Test API endpoint: `/api/random-challenge`

## Going Live
- [ ] Verify both services show "Active" status
- [ ] Test on mobile device
- [ ] Share URL with users!

**Estimated time**: 20-30 minutes total

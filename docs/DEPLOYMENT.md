# Deployment Guide

This guide explains how to deploy the Polymarket Dependency Lab Control Tower.

## Architecture

The application consists of two parts:
1. **Frontend** (Next.js) - Control Tower UI
2. **Backend** (FastAPI) - Bot control API

## Frontend Deployment (GitHub Pages)

The frontend is automatically deployed to GitHub Pages when you push to the `main` branch.

### Automatic Deployment

1. **Enable GitHub Pages** in your repository settings:
   - Go to Settings → Pages
   - Source: "GitHub Actions"

2. **Push to main branch**:
   ```bash
   git push origin main
   ```

3. **Access your Control Tower**:
   - URL: https://neurallarkai.github.io/polymarket-dependency-lab/
   - The frontend will be live within 2-3 minutes

### Manual Deployment

If you want to deploy manually:

```bash
cd control_tower/frontend

# Install dependencies
pnpm install

# Build for production
pnpm build

# The static files will be in the 'out' directory
# You can deploy these to any static hosting service
```

## Backend Deployment

The FastAPI backend needs to run on a server. Here are your options:

### Option 1: Railway (Recommended - Free Tier Available)

1. Create account at [Railway.app](https://railway.app)
2. Create new project from GitHub repo
3. Set environment variables:
   ```
   PORT=8000
   RUNS_DIR=/app/runs
   ```
4. Deploy!
5. Copy your Railway URL (e.g., `https://your-app.railway.app`)
6. Update GitHub repository secret `PRODUCTION_API_URL` with this URL

### Option 2: Render (Free Tier Available)

1. Create account at [Render.com](https://render.com)
2. New → Web Service
3. Connect your GitHub repo
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd control_tower/backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Environment variables:
   ```
   PYTHON_VERSION=3.11
   RUNS_DIR=/app/runs
   ```
6. Copy your Render URL
7. Update GitHub repository secret `PRODUCTION_API_URL`

### Option 3: DigitalOcean App Platform

1. Create account at [DigitalOcean](https://www.digitalocean.com)
2. Create new App from GitHub
3. Configure:
   - HTTP Port: 8000
   - Run Command: `cd control_tower/backend && uvicorn app:app --host 0.0.0.0 --port 8000`
4. Deploy and copy URL
5. Update GitHub repository secret `PRODUCTION_API_URL`

### Option 4: Self-Hosted (VPS/Cloud)

If you have your own server:

```bash
# Install dependencies
pip install -r requirements.txt

# Run backend (use process manager like systemd or PM2)
cd control_tower/backend
uvicorn app:app --host 0.0.0.0 --port 8000

# Optional: Use nginx as reverse proxy
# Optional: Setup SSL with Let's Encrypt
```

## Setting Production API URL

After deploying your backend, configure the frontend to use it:

### Method 1: GitHub Secret (Recommended)

1. Go to your repo → Settings → Secrets and variables → Actions
2. Create new secret:
   - Name: `PRODUCTION_API_URL`
   - Value: Your backend URL (e.g., `https://your-backend.railway.app`)
3. Next deployment will use this URL

### Method 2: Update .env.example

Update the `.env.example` file with your production URL as the default.

## Local Development

For local development, both services run on your machine:

```bash
# Terminal 1: Backend
cd control_tower/backend
uvicorn app:app --reload --port 8000

# Terminal 2: Frontend
cd control_tower/frontend
pnpm dev

# Terminal 3: Bot
python run.py
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## CORS Configuration

The backend allows all origins by default (`allow_origins=["*"]`).

For production, you should restrict this in `control_tower/backend/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://neurallarkai.github.io",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Monitoring

- View deployment status: Actions tab on GitHub
- Check build logs: Click on workflow run
- Test API: Visit `YOUR_BACKEND_URL/docs` for Swagger UI
- View frontend: Visit your GitHub Pages URL

## Troubleshooting

### Frontend shows "Failed to fetch"
- Check if backend is running
- Verify CORS is configured correctly
- Check browser console for errors
- Ensure PRODUCTION_API_URL is set correctly

### Backend not responding
- Check if the service is running
- Verify environment variables
- Check server logs
- Ensure port 8000 is accessible

### GitHub Pages shows README
- Make sure GitHub Actions workflow ran successfully
- Check Pages settings: Source should be "GitHub Actions"
- Verify the deployment succeeded in Actions tab

## Cost Considerations

- **Frontend (GitHub Pages)**: Free
- **Backend Options**:
  - Railway: Free tier with 500 hours/month
  - Render: Free tier available
  - DigitalOcean: Starts at $5/month
  - Self-hosted: Variable (VPS costs)

## Security Notes

1. **Never commit API keys** to the repository
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** for production backends
4. **Restrict CORS** in production
5. **Keep dependencies updated** regularly

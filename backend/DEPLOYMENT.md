# Backend Deployment Guide - Render

## 🚀 **RENDER DEPLOYMENT INSTRUCTIONS**

### **Step 1: Prepare Repository**

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Production deployment preparation"
   git push origin main
   ```

### **Step 2: Deploy to Render**

1. **Go to [Render Dashboard](https://dashboard.render.com)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service:**

   **Basic Settings:**
   - **Name**: `website-intelligence-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

   **Advanced Settings:**
   - **Python Version**: `3.12`
   - **Root Directory**: `backend`

### **Step 3: Environment Variables**

Set these environment variables in Render dashboard:

**Required Variables:**
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# API Configuration
API_SECRET_KEY=your_secure_production_key_here

# LLM APIs
GEMINI_API_KEY=<SET_IN_RENDER>
OPENAI_API_KEY=<OPTIONAL_SET_IN_RENDER>

# Database
SUPABASE_URL=https://qeasoqfnkhrehqhfwwer.supabase.co
SUPABASE_KEY=<SET_IN_RENDER>

# Vector Database
QDRANT_URL=https://780c74cf-e62e-4209-8799-f88e0f377060.us-west-1-0.aws.cloud.qdrant.io
QDRANT_API_KEY=<SET_IN_RENDER>

# External Services
JINA_AI_API_KEY=<OPTIONAL_SET_IN_RENDER>

# Scraping Configuration
MIN_TEXT_LENGTH=500
MIN_TEXT_RATIO=0.1
MIN_KEYWORD_MATCHES=2
SCRAPING_TIMEOUT=10

# Rate Limiting
ANALYZE_RATE_LIMIT=20/minute
CHAT_RATE_LIMIT=60/minute
```

### **Step 4: Deploy**

1. **Click "Create Web Service"**
2. **Wait for deployment to complete** (5-10 minutes)
3. **Note the service URL** (e.g., `https://website-intelligence-api.onrender.com`)

### **Step 5: Test Deployment**

```bash
# Health check
curl https://your-service-url.onrender.com/health

# Test analysis endpoint
curl -X POST "https://your-service-url.onrender.com/api/v1/analyze-simple" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_secure_production_key_here" \
  -d '{"url": "https://github.com"}'
```

### **Step 6: Custom Domain (Optional)**

1. **Go to Settings → Custom Domains**
2. **Add your domain** (e.g., `api.website-intelligence.com`)
3. **Configure DNS** as instructed by Render
4. **Update CORS settings** in `main.py` with your domain

## 🔧 **TROUBLESHOOTING**

### **Common Issues:**

1. **Build Fails:**
   - Check Python version (should be 3.12)
   - Verify all dependencies in `requirements.txt`

2. **Service Won't Start:**
   - Check environment variables are set correctly
   - Verify start command is correct

3. **API Errors:**
   - Check logs in Render dashboard
   - Verify all API keys are valid

4. **CORS Issues:**
   - Update CORS origins in `main.py`
   - Ensure frontend URL is correct

### **Monitoring:**

- **Logs**: Available in Render dashboard
- **Metrics**: CPU, Memory, Response times
- **Health Check**: `/health` endpoint

## 📊 **PRODUCTION OPTIMIZATIONS**

### **Performance:**
- Rate limiting enabled (20 analyze/min, 60 chat/min)
- Async operations throughout
- Proper error handling and logging

### **Security:**
- Bearer token authentication
- CORS properly configured
- Environment variables secured

### **Monitoring:**
- Structured logging
- Health check endpoint
- Error tracking

## 🎯 **NEXT STEPS**

After successful deployment:
1. **Update frontend** with production API URL
2. **Deploy frontend** to Vercel
3. **Configure custom domains**
4. **Set up monitoring and alerts**
5. **Conduct load testing**

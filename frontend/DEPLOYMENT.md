# Frontend Deployment Guide - Vercel

## 🚀 **VERCEL DEPLOYMENT INSTRUCTIONS**

### **Step 1: Prepare Repository**

1. **Push to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Frontend production deployment preparation"
   git push origin main
   ```

### **Step 2: Deploy to Vercel**

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**
2. **Click "New Project"**
3. **Import your GitHub repository**
4. **Configure the project:**

   **Project Settings:**
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

### **Step 3: Environment Variables**

Set these environment variables in Vercel dashboard:

**Required Variables:**
```bash
NEXT_PUBLIC_API_BASE_URL=https://website-intelligence-api.onrender.com
NEXT_PUBLIC_API_SECRET_KEY=your_secure_production_key_here
```

**To set environment variables:**
1. Go to **Project Settings** → **Environment Variables**
2. Add each variable for **Production** environment
3. Click **Save**

### **Step 4: Deploy**

1. **Click "Deploy"**
2. **Wait for deployment to complete** (2-5 minutes)
3. **Note the deployment URL** (e.g., `https://website-intelligence-frontend.vercel.app`)

### **Step 5: Test Deployment**

1. **Visit your deployment URL**
2. **Test the analysis feature** with a sample URL (e.g., `https://github.com`)
3. **Verify the chat functionality** works
4. **Check mobile responsiveness**

### **Step 6: Custom Domain (Optional)**

1. **Go to Project Settings** → **Domains**
2. **Add your domain** (e.g., `website-intelligence.com`)
3. **Configure DNS** as instructed by Vercel
4. **Update backend CORS settings** with your domain

## 🔧 **TROUBLESHOOTING**

### **Common Issues:**

1. **Build Fails:**
   - Check Node.js version (should be 18+)
   - Verify all dependencies in `package.json`
   - Check for TypeScript errors

2. **Environment Variables Not Working:**
   - Ensure variables start with `NEXT_PUBLIC_`
   - Check they're set for the correct environment
   - Redeploy after adding variables

3. **API Connection Issues:**
   - Verify `NEXT_PUBLIC_API_BASE_URL` is correct
   - Check backend is deployed and accessible
   - Verify CORS settings in backend

4. **Styling Issues:**
   - Check Tailwind CSS configuration
   - Verify all components are properly imported

### **Monitoring:**

- **Analytics**: Available in Vercel dashboard
- **Performance**: Core Web Vitals tracking
- **Deployments**: Build logs and status

## 📊 **PRODUCTION OPTIMIZATIONS**

### **Performance:**
- Next.js 15 with App Router
- Automatic code splitting
- Image optimization
- Static generation where possible

### **Security:**
- Environment variables secured
- Security headers configured
- HTTPS enforced

### **SEO:**
- Meta tags configured
- Open Graph tags
- Structured data ready

## 🎯 **NEXT STEPS**

After successful deployment:
1. **Update backend CORS** with frontend URL
2. **Configure custom domains**
3. **Set up monitoring and analytics**
4. **Conduct user testing**
5. **Optimize performance**

## 🔄 **AUTOMATIC DEPLOYMENTS**

Vercel will automatically deploy when you push to your main branch:
- **Preview deployments** for pull requests
- **Production deployments** for main branch
- **Rollback capability** for quick fixes

## 📱 **MOBILE OPTIMIZATION**

The frontend is fully responsive and optimized for:
- **Mobile devices** (320px+)
- **Tablets** (768px+)
- **Desktop** (1024px+)
- **Touch interactions**
- **Fast loading** on mobile networks

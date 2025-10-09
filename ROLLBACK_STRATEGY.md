# Rollback Strategy - Critical Gaps Implementation

## 🚨 Quick Rollback Commands

### **Emergency Rollback (Disable Authentication & Rate Limiting)**
```bash
# 1. Re-disable authentication in analyze_simple.py
sed -i 's/current_user: str = Depends(get_current_user)/# current_user: str = Depends(get_current_user)  # ROLLBACK/' backend/app/api/v1/analyze_simple.py

# 2. Re-disable rate limiting in analyze_simple.py  
sed -i 's/@analyze_rate_limit/# @analyze_rate_limit  # ROLLBACK/' backend/app/api/v1/analyze_simple.py

# 3. Re-disable authentication in chat.py
sed -i 's/current_user: str = Depends(get_current_user)/# current_user: str = Depends(get_current_user)  # ROLLBACK/' backend/app/api/v1/chat.py

# 4. Re-disable rate limiting in chat.py
sed -i 's/@chat_rate_limit/# @chat_rate_limit  # ROLLBACK/' backend/app/api/v1/chat.py

# 5. Re-disable Swagger docs in production
sed -i 's|docs_url="/docs"|docs_url="/docs" if settings.environment == "development" else None|' backend/app/main.py
sed -i 's|redoc_url="/redoc"|redoc_url="/redoc" if settings.environment == "development" else None|' backend/app/main.py
```

### **Frontend Rollback (Remove Auth Headers)**
```bash
# Remove auth headers from analyze endpoint
sed -i '/Authorization.*Bearer.*API_TOKEN/d' frontend/src/app/page.tsx

# Remove auth error handling (optional)
sed -i '/response.status === 401/,+3d' frontend/src/app/page.tsx
sed -i '/response.status === 429/,+3d' frontend/src/app/page.tsx
```

---

## 🔄 **Rollback Scenarios**

### **Scenario 1: Authentication Issues**
**Symptoms:** 401 errors, users can't access API
**Rollback Steps:**
1. Run emergency rollback commands above
2. Deploy changes
3. Verify API works without auth
4. Debug auth issues in staging

### **Scenario 2: Rate Limiting Too Restrictive**
**Symptoms:** 429 errors, legitimate users blocked
**Rollback Steps:**
1. Disable rate limiting: `# @analyze_rate_limit`
2. Deploy changes
3. Adjust rate limits in config
4. Re-enable with new limits

### **Scenario 3: Chat Endpoint Issues**
**Symptoms:** Chat functionality broken, database errors
**Rollback Steps:**
1. Disable chat endpoint temporarily
2. Or enable mock mode for chat
3. Debug database connectivity
4. Re-enable when fixed

### **Scenario 4: Frontend Issues**
**Symptoms:** Frontend not working with auth
**Rollback Steps:**
1. Remove auth headers from frontend
2. Deploy frontend changes
3. Debug auth integration
4. Re-add when fixed

---

## 🛠️ **Rollback Verification**

### **Test Commands**
```bash
# Test API without auth (should work after rollback)
curl -X POST https://website-intelligence-api.onrender.com/api/v1/analyze-simple \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Test health endpoint
curl https://website-intelligence-api.onrender.com/health

# Test frontend
curl https://website-intelligence-0.vercel.app
```

### **Success Criteria**
- ✅ API responds without authentication
- ✅ Rate limiting disabled
- ✅ Frontend loads without errors
- ✅ Basic functionality works
- ✅ No 401/429 errors

---

## 📋 **Rollback Checklist**

### **Before Rollback**
- [ ] Identify the specific issue
- [ ] Document current state
- [ ] Notify stakeholders
- [ ] Prepare rollback commands

### **During Rollback**
- [ ] Execute rollback commands
- [ ] Deploy changes
- [ ] Verify functionality
- [ ] Test critical endpoints

### **After Rollback**
- [ ] Monitor for 24 hours
- [ ] Debug original issue
- [ ] Plan re-implementation
- [ ] Update documentation

---

## 🔧 **Configuration Rollback**

### **Rate Limits**
```bash
# Restore original rate limits
sed -i 's/analyze_rate_limit: str = Field(default="20\/minute"/analyze_rate_limit: str = Field(default="10\/minute"/' backend/app/core/config.py
sed -i 's/chat_rate_limit: str = Field(default="60\/minute"/chat_rate_limit: str = Field(default="30\/minute"/' backend/app/core/config.py
```

### **Environment Variables**
```bash
# Check current environment
curl https://website-intelligence-api.onrender.com/env-check

# Verify API keys are still set
# (No rollback needed for env vars)
```

---

## 📞 **Emergency Contacts & Escalation**

### **Level 1: Quick Rollback**
- Execute rollback commands
- Deploy changes
- Verify functionality

### **Level 2: Debug Issues**
- Check logs: `render logs --service website-intelligence-api`
- Verify environment variables
- Test locally with same config

### **Level 3: Full Investigation**
- Review code changes
- Check dependencies
- Test with different configurations

---

## 📝 **Rollback Log**

| Date | Issue | Action Taken | Status | Notes |
|------|-------|--------------|--------|-------|
| TBD | TBD | TBD | TBD | TBD |

---

**Last Updated:** January 8, 2025
**Next Review:** After any production deployment

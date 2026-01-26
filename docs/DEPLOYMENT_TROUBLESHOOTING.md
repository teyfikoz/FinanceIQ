# 🔧 Deployment Troubleshooting Guide

## Common Streamlit Cloud Deployment Errors

### ❌ "Some jobs were not successful"

This error typically indicates one of the following issues:

---

## ✅ Fixed Issues (2024-11-13)

### 1. Python Version Specification
**Problem:** Streamlit Cloud didn't know which Python version to use

**Solution:**
- ✅ Added `.python-version` file (Python 3.11)
- ✅ Added `runtime.txt` file
- ✅ Both files force Streamlit Cloud to use Python 3.11

### 2. System Dependencies
**Problem:** Missing system-level packages for lxml and beautifulsoup4

**Solution:**
- ✅ Created `packages.txt` with required system dependencies:
  ```
  build-essential
  libxml2-dev
  libxslt1-dev
  python3-dev
  ```

### 3. Import Error Handling
**Problem:** API config UI import could crash the app

**Solution:**
- ✅ Wrapped import in try-except block
- ✅ Graceful error messages instead of crashes

---

## 📊 Current Configuration

### Python Version
```
Python 3.11
```

### Dependencies
All dependencies in `requirements.txt` are:
- ✅ Streamlit Cloud compatible
- ✅ Python 3.11 compatible
- ✅ Lightweight (no TensorFlow, PyTorch, etc.)
- ✅ Fast to install

### System Packages
```txt
build-essential
libxml2-dev
libxslt1-dev
python3-dev
```

---

## 🔍 How to Debug Deployment Errors

### Step 1: Check Logs
1. Go to https://share.streamlit.io/
2. Click on your app (FinanceIQ)
3. Click on "⋮" menu → "Logs"
4. Look for error messages in red

### Browser Console Warning (Not App Bug)
If you see this in the browser console:
```
content.js:1 Uncaught (in promise) The message port closed before a response was received.
```
This is **not** caused by the FinanceIQ app. It comes from a browser extension’s content script.

**Why this happens**
- The console line points to `content.js`, which typically belongs to a Chrome/Brave extension.
- Streamlit app code doesn’t include `content.js`.

**How to confirm**
- Open the console link to see a `chrome-extension://.../content.js` URL.
- Disable extensions (or use an incognito window with extensions off) and reload the app.

### Theme Sidebar Color Warnings (Browser Console)
If you see warnings like:
```
Invalid color passed for widgetBackgroundColor in theme.sidebar: ""
Invalid color passed for widgetBorderColor in theme.sidebar: ""
Invalid color passed for skeletonBackgroundColor in theme.sidebar: ""
```
These are theme config issues (not runtime crashes).

**Fix**
- Ensure `.streamlit/config.toml` has valid hex colors for sidebar theme.
- If Streamlit Cloud theme settings were edited in the UI, clear any blank fields and re-save.

### Step 2: Common Error Messages

#### "ModuleNotFoundError: No module named 'X'"
**Solution:** Add the package to `requirements.txt`

#### "ImportError: cannot import name 'X'"
**Solution:** Check if the module/class name is correct

#### "TimeoutError" or "App took too long to start"
**Solution:**
- Reduce number of imports
- Use lazy loading
- Add `@st.cache_data` decorators

#### "MemoryError"
**Solution:**
- Remove heavy ML packages
- Use lighter alternatives
- Reduce cache sizes

---

## 🚀 Deployment Checklist

Before deploying, ensure:

```
☐ Python version specified (.python-version, runtime.txt)
☐ All packages in requirements.txt
☐ System dependencies in packages.txt
☐ No hardcoded secrets (use Streamlit secrets)
☐ All imports wrapped in try-except
☐ @st.cache_data used appropriately
☐ No heavy ML packages (TensorFlow, PyTorch, etc.)
☐ Streamlit config (.streamlit/config.toml) is correct
```

---

## 📝 Streamlit Cloud Secrets Configuration

After deployment succeeds, configure secrets:

1. Go to: https://share.streamlit.io/
2. Click on your app → Settings → Secrets
3. Add API keys in TOML format:

```toml
# API Keys
FRED_API_KEY = "your_key_here"
FINNHUB_API_KEY = "your_key_here"
ALPHA_VANTAGE_KEY = "your_key_here"
FMP_API_KEY = "your_key_here"
POLYGON_API_KEY = "your_key_here"
TRADINGECONOMICS_KEY = "your_key_here"
```

4. Click "Save"
5. App will automatically restart

---

## 🔄 Redeploying After Fixes

### Option 1: Push to GitHub
```bash
git add .
git commit -m "Fix deployment issues"
git push origin main
```
Streamlit Cloud will auto-deploy (2-5 minutes)

### Option 2: Manual Reboot
1. Go to https://share.streamlit.io/
2. Click on your app
3. Click "⋮" → "Reboot app"

---

## ⚡ Performance Optimization Tips

### 1. Use Caching
```python
@st.cache_data(ttl=300)
def expensive_function():
    # Your code here
    pass
```

### 2. Lazy Loading
```python
# Don't import at top if not always needed
def some_function():
    import heavy_module  # Import only when needed
    return heavy_module.do_something()
```

### 3. Reduce API Calls
- Use caching aggressively
- Batch requests when possible
- Use fallback chains

---

## 🆘 Still Having Issues?

### Check These:

1. **Streamlit Cloud Status**
   - https://status.streamlit.io/
   - Is there an outage?

2. **GitHub Repo**
   - Is the repo public?
   - Is Streamlit connected to the right repo?
   - Is the main branch selected?

3. **File Structure**
   ```
   ├── main.py (entry point)
   ├── requirements.txt
   ├── packages.txt
   ├── .python-version
   ├── runtime.txt
   ├── .streamlit/
   │   └── config.toml
   ├── modules/
   ├── utils/
   └── dashboard/
   ```

4. **App Settings**
   - Main file path: `main.py` ✅
   - Python version: 3.11 ✅
   - Branch: main ✅

---

## 📞 Support

**Streamlit Community:**
- Forum: https://discuss.streamlit.io/
- Docs: https://docs.streamlit.io/

**App Specific:**
- GitHub Issues: https://github.com/teyfikoz/FinanceIQ/issues
- Logs: https://share.streamlit.io/ → Your App → Logs

---

## ✅ Success Indicators

Your deployment succeeded if you see:

```
✅ App is running
✅ URL is accessible: https://financeiq.streamlit.app
✅ No error messages in logs
✅ All tabs load without crashes
✅ API calls work (after secrets configured)
```

---

## 🎯 Current Status (2024-11-13)

```
✅ Python 3.11 specified
✅ System dependencies added
✅ Import error handling improved
✅ All syntax checked
✅ Requirements.txt optimized
🔄 Deploying to production...
```

**Next:** Wait 2-5 minutes for deployment to complete, then check logs.

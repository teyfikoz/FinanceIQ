# 🚀 Streamlit Cloud Deployment Guide

## FinanceIQ - Streamlit Cloud Deployment

**Live URL**: https://financeiq.streamlit.app/

---

## 📋 Pre-Deployment Checklist

### ✅ **Completed**
- [x] Game Changer features integrated into `main.py` (Tab 12)
- [x] `.streamlit/config.toml` created with theme settings
- [x] `requirements.txt` optimized for Streamlit Cloud
- [x] CORS config fixed in `app/core/config.py`
- [x] `.gitignore` configured properly
- [x] All features are offline-compatible (no paid APIs required)

---

## 🔧 Streamlit Cloud Configuration

### **1. Repository Setup**

Your GitHub repository should contain:
```
global_liquidity_dashboard/
├── .streamlit/
│   ├── config.toml          # Theme & server config
│   └── secrets.toml         # Secrets template (not committed)
├── app/
│   ├── analytics/
│   │   ├── social_features.py
│   │   ├── visualization_tools.py
│   │   ├── ai_lite_tools.py
│   │   └── ... (other modules)
│   ├── ui/
│   │   ├── navigation.py
│   │   ├── export_tools.py
│   │   └── theme_toggle.py
│   └── core/
│       └── config.py        # Fixed CORS config
├── main.py                  # Main dashboard entry point
├── requirements.txt         # Cloud-optimized dependencies
├── .gitignore              # Excludes .env, secrets
└── README.md
```

---

### **2. Streamlit Cloud Settings**

#### **App URL**
- Primary URL: `https://financeiq.streamlit.app/`
- Custom domain (optional): Configure in Streamlit Cloud dashboard

#### **Python Version**
- **Recommended**: Python 3.10 or 3.11
- **Not recommended**: Python 3.13 (limited package support)

#### **Main File**
- **Entry point**: `main.py`
- **Alternative**: `game_changer_dashboard.py` (standalone version)

---

### **3. Environment Variables & Secrets**

#### **In Streamlit Cloud Dashboard → Settings → Secrets**

Add the following secrets (if you have API keys):

```toml
# Optional API Keys (all features work without these)
[api_keys]
FRED_API_KEY = "your-fred-api-key"
ALPHA_VANTAGE_API_KEY = "your-alpha-vantage-key"
FMP_API_KEY = "your-fmp-key"
FINNHUB_API_KEY = ""
POLYGON_API_KEY = ""
NEWSAPI_KEY = ""
COINGECKO_API_KEY = ""

# Database (optional - not required for basic functionality)
[database]
POSTGRES_SERVER = "your-postgres-host"
POSTGRES_USER = "your-db-user"
POSTGRES_PASSWORD = "your-db-password"
POSTGRES_DB = "liquidity_dashboard"

# Security
SECRET_KEY = "your-super-secret-jwt-key-here"

[ai]
HF_API_TOKEN = ""
HF_SUMMARY_MODEL = "facebook/bart-large-cnn"
HF_SENTIMENT_MODEL = "ProsusAI/finbert"
HF_RISK_MODEL = "google/flan-t5-base"

[app]
FINANCEIQ_ENV = "production"
FINANCEIQ_REQUIRE_AUTH = false
FINANCEIQ_DIRECT_ACCESS = true
FINANCEIQ_CREATE_DEMO_USER = false
```

**Important**: Core features work 100% **without any API keys** - they use free data from yfinance and fallback systems!

---

### **4. Resource Limits**

Streamlit Cloud Community Plan:
- **Memory**: 1 GB RAM
- **CPU**: Shared
- **Sleep**: Apps sleep after 7 days of inactivity
- **Bandwidth**: Unlimited

**Optimization Tips**:
- Use `@st.cache_data` for expensive operations (already implemented)
- Limit data fetch to last 1-2 years
- Use lazy loading for visualizations

---

## 🎯 Deployment Steps

### **Step 1: Push to GitHub**

```bash
cd /Users/teyfikoz/Downloads/Borsa\ Analiz/global_liquidity_dashboard

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Add Phase 1 Game Changer Features

- Social Layer: Portfolio Snapshots, Watchlists, Notes, Leaderboard
- Visualizations: Heatmap Calendar, Sector Rotation, Fear & Greed, 3D Portfolio
- AI Tools: Monte Carlo, Backtesting, Chart Annotation, News Sentiment
- Export: PDF, Excel, QR Codes
- Fixed CORS config for Streamlit Cloud
- Optimized requirements.txt for cloud deployment"

# Push to main branch
git push origin main
```

---

### **Step 2: Deploy on Streamlit Cloud**

1. **Go to**: https://share.streamlit.io/
2. **Sign in** with GitHub
3. **Click** "New app"
4. **Select**:
   - Repository: `your-username/global_liquidity_dashboard`
   - Branch: `main`
   - Main file: `main.py`
5. **Click** "Deploy!"

Streamlit Cloud will:
- Clone your repository
- Install dependencies from `requirements.txt`
- Start the app on `https://financeiq.streamlit.app/`

---

### **Step 3: Configure Secrets** (Optional)

1. Go to app dashboard
2. Click **Settings** → **Secrets**
3. Add your secrets in TOML format (see section 3 above)
4. Click **Save**
5. App will automatically restart

---

## 🔄 Auto-Deployment

Streamlit Cloud watches your GitHub repository:

- **Push to `main`** → Automatic redeployment
- **Change detection**: ~30-60 seconds
- **Build time**: 2-5 minutes (depending on dependencies)

---

## 🐛 Troubleshooting

### **Problem 1: "Port already in use"**
**Solution**: Not applicable on Streamlit Cloud (handled automatically)

---

### **Problem 2: "ModuleNotFoundError"**
**Solution**:
```bash
# Verify requirements.txt includes the module
# Example: If missing 'qrcode'
echo "qrcode[pil]>=7.4.0" >> requirements.txt
git add requirements.txt
git commit -m "Add missing dependency"
git push
```

---

### **Problem 3: "CORS Error"**
**Solution**: Already fixed in `app/core/config.py`
- Changed `List[AnyHttpUrl]` → `List[str]`
- Added fallback in `assemble_cors_origins()`

---

### **Problem 4: "App is slow or crashing"**
**Solutions**:
1. **Reduce cache TTL**:
   ```python
   @st.cache_data(ttl=600)  # 10 minutes instead of 5
   ```

2. **Limit data periods**:
   - Change default from "5y" to "1y"
   - Reduce Monte Carlo simulations from 10,000 to 5,000

3. **Check logs**: Streamlit Cloud → App → Logs

---

### **Problem 5: "Session state issues"**
**Solution**: Clear cache in Streamlit Cloud:
- Click **⋮** (three dots) → **Reboot app**

---

## 📊 Monitoring & Analytics

### **Streamlit Cloud Dashboard**

- **Analytics**: View usage stats
- **Logs**: Real-time application logs
- **Performance**: CPU/Memory usage
- **Viewers**: Number of active users

### **Access Logs**

```bash
# View logs in Streamlit Cloud UI
# Or add custom logging:
import logging
logging.info(f"User accessed Game Changer features at {datetime.now()}")
```

---

## 🎨 Customization

### **Change App Theme**

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#667eea"        # Purple (default)
backgroundColor = "#0e1117"      # Dark background
secondaryBackgroundColor = "#1e2130"
textColor = "#fafafa"
font = "sans serif"
```

Then push to GitHub:
```bash
git add .streamlit/config.toml
git commit -m "Update theme colors"
git push
```

---

### **Add Custom Domain**

1. Go to Streamlit Cloud app settings
2. Click **General** → **Custom domain**
3. Enter your domain (e.g., `financeiq.yourdomain.com`)
4. Configure DNS:
   ```
   CNAME record: financeiq → financeiq.streamlit.app
   ```

---

## 🚀 Performance Optimization

### **1. Data Caching**

Already implemented in all modules:
```python
@st.cache_data(ttl=300)  # 5 minutes
def fetch_market_data(ticker):
    # Expensive operation
    return data
```

### **2. Lazy Loading**

Load data only when needed:
```python
with st.spinner("Loading data..."):
    data = fetch_data()  # Only runs when tab is accessed
```

### **3. Session State**

Minimize session state size:
```python
# Good
st.session_state['ticker'] = "AAPL"

# Bad (large objects)
st.session_state['entire_dataframe'] = huge_df  # Avoid
```

---

## 📈 Usage Statistics

Monitor your app usage:

- **Daily Active Users (DAU)**
- **Monthly Active Users (MAU)**
- **Average Session Duration**
- **Most Used Features**

Access via: Streamlit Cloud Dashboard → Analytics

---

## 🔒 Security Best Practices

### **1. Never Commit Secrets**

✅ **Good**:
```bash
# Add to .gitignore
.env
.streamlit/secrets.toml
```

❌ **Bad**:
```bash
# Committing .env with API keys
git add .env  # NEVER DO THIS!
```

### **2. Use Streamlit Secrets**

✅ **Good**:
```python
import streamlit as st
api_key = st.secrets["api_keys"]["FRED_API_KEY"]
```

❌ **Bad**:
```python
api_key = "hardcoded-api-key-12345"  # NEVER DO THIS!
```

### **3. Validate User Input**

Already implemented in forms:
```python
ticker = st.text_input("Enter Ticker").upper()
if ticker and len(ticker) <= 10:  # Validate
    process_ticker(ticker)
```

---

## 🎯 Game Changer Features on Cloud

All Phase 1 features work **100% on Streamlit Cloud**:

### **✅ Fully Functional**
- ✅ Portfolio Snapshots (PNG generation)
- ✅ Public Watchlists (yfinance data)
- ✅ Ticker Notes (session state)
- ✅ Leaderboard (simulated data)
- ✅ Calendar Heatmap (Plotly)
- ✅ Sector Rotation (sector ETFs)
- ✅ Fear & Greed Gauge (VIX + RSI)
- ✅ 3D Portfolio (Treemap + Sunburst)
- ✅ Monte Carlo Simulation (NumPy)
- ✅ Backtesting (SMA/RSI/MACD)
- ✅ Chart Annotation (support/resistance)
- ✅ News Sentiment (keyword-based)
- ✅ PDF Export (HTML-based)
- ✅ Excel Export (openpyxl)
- ✅ QR Code Generator (qrcode library)

### **⚠️ Limitations**
- ⚠️ TA-Lib not available (using pandas/numpy instead)
- ⚠️ Prophet not included (heavy dependency)
- ⚠️ No real-time WebSocket (polling instead)

---

## 📞 Support

### **Streamlit Cloud Support**
- Documentation: https://docs.streamlit.io/streamlit-community-cloud
- Forum: https://discuss.streamlit.io/
- GitHub Issues: https://github.com/streamlit/streamlit/issues

### **FinanceIQ Support**
- Repository: Your GitHub repo
- Issues: Create GitHub issue
- Discussions: Enable GitHub Discussions

---

## 🎉 Next Steps

After successful deployment:

1. **Test all features** on https://financeiq.streamlit.app/
2. **Share URL** with users/stakeholders
3. **Monitor logs** for errors
4. **Collect feedback** from users
5. **Plan Phase 2** features

---

## 📝 Deployment Checklist

Before pushing to production:

- [ ] Test locally on `localhost:8502`
- [ ] Verify all imports work
- [ ] Check `requirements.txt` is complete
- [ ] Ensure `.env` is in `.gitignore`
- [ ] Test with demo user credentials
- [ ] Verify Game Changer tab appears
- [ ] Test at least 3 features from each category
- [ ] Check mobile responsiveness
- [ ] Review logs for errors
- [ ] Update README.md with new features
- [ ] Create GitHub release/tag
- [ ] Push to `main` branch
- [ ] Monitor Streamlit Cloud deployment
- [ ] Test live URL
- [ ] Share with team! 🎊

---

**🚀 Your FinanceIQ app with Game Changer features is ready for the world!**

**Live URL**: https://financeiq.streamlit.app/

**Demo Login**: demo / demo123

**Game Changer Features**: Tab 12 → 🚀 Game Changer

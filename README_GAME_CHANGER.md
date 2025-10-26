# 🚀 FinanceIQ - AI-Powered Financial Analysis Platform

## With Game Changer Features - Phase 1

**Live Demo**: [https://financeiq.streamlit.app/](https://financeiq.streamlit.app/)

**Demo Credentials**: `demo` / `demo123`

---

## 🎯 What's New - Phase 1 Game Changer Features

### **Cost: $0 | APIs Required: 0 | Offline-Ready: ✅**

We've added **15+ revolutionary features** to dramatically enhance engagement and analytical capabilities:

### **🎯 Social Layer (4 Features)**
- 📸 **Portfolio Snapshots**: Create shareable PNG cards
- 📋 **Public Watchlists**: 6 curated stock lists (ETFs, Blue Chips, etc.)
- 📝 **Ticker Notes**: Personal notes per stock
- 🏆 **Leaderboard**: Demo performance rankings

### **🎨 Advanced Visualizations (4 Features)**
- 📅 **Calendar Heatmap**: GitHub-style returns calendar
- 🔄 **Sector Rotation Wheel**: Interactive sector performance
- 😱 **Fear & Greed Gauge**: Market sentiment indicator
- 📊 **3D Portfolio**: Interactive treemap & sunburst charts

### **🤖 AI-Powered Tools (4 Features)**
- 🎲 **Monte Carlo Simulation**: 10,000+ portfolio paths
- ⚡ **Backtesting Engine**: Test SMA/RSI/MACD strategies
- 🎯 **Auto Chart Annotation**: Support/resistance detection
- 📰 **News Sentiment**: Keyword-based sentiment scoring

### **📤 Export & Sharing (3 Features)**
- 📄 **PDF Export**: Professional reports
- 📊 **Excel Export**: Data downloads
- 📱 **QR Codes**: Share dashboard URLs

---

## 🚀 Quick Start

### **Option 1: Access Live Demo**
```
🌐 https://financeiq.streamlit.app/
👤 Login: demo / demo123
🎯 Navigate to Tab 12: "🚀 Game Changer"
```

### **Option 2: Run Locally**
```bash
# Clone repository
git clone https://github.com/your-username/global_liquidity_dashboard.git
cd global_liquidity_dashboard

# Install dependencies
pip install -r requirements.txt

# Run main dashboard
streamlit run main.py

# OR run standalone Game Changer dashboard
streamlit run game_changer_dashboard.py
```

---

## 📊 Features Overview

### **Tab 1-11: Original FinanceIQ Features**
- 🎯 Executive Dashboard
- 🔍 Comprehensive Stock Research
- 📡 Advanced Stock Screener
- 🧪 Strategy Lab (Backtesting & Neural Networks)
- 📊 ETFs & Mutual Funds Analysis
- 🏛️ Institutional Holdings Tracker
- 🇹🇷 Turkish Markets (BIST)
- 💼 Portfolio Management
- 👁️ Watchlist Management
- 🔔 Price Alerts
- 🔒 Privacy & GDPR Compliance

### **Tab 12: 🚀 Game Changer Features** (NEW!)
All Phase 1 features listed above, organized in 4 categories:
1. Social Features
2. Advanced Visualizations
3. AI Tools
4. Export & Share

---

## 🛠️ Tech Stack

### **Core**
- **Framework**: Streamlit 1.31+
- **Data Processing**: Pandas, NumPy
- **Visualizations**: Plotly, Seaborn, Matplotlib
- **ML**: Scikit-learn, Statsmodels, SciPy

### **Data Sources (All Free)**
- **Market Data**: yfinance (Yahoo Finance)
- **Economic Data**: FRED API
- **Alternative Data**: pandas-datareader

### **Game Changer Additions**
- **Image Processing**: Pillow (PNG snapshots)
- **QR Codes**: qrcode[pil]
- **Excel Export**: openpyxl
- **PDF Export**: HTML-to-PDF conversion

---

## 📂 Project Structure

```
global_liquidity_dashboard/
├── .streamlit/
│   ├── config.toml                 # Streamlit Cloud config
│   └── secrets.toml                # Secrets template
├── app/
│   ├── analytics/
│   │   ├── social_features.py      # 🆕 Social layer
│   │   ├── visualization_tools.py  # 🆕 Advanced charts
│   │   ├── ai_lite_tools.py        # 🆕 AI tools
│   │   └── ... (other modules)
│   ├── ui/
│   │   ├── navigation.py           # 🆕 Navigation
│   │   ├── export_tools.py         # 🆕 Export utilities
│   │   └── theme_toggle.py         # 🆕 Theme system
│   ├── core/
│   │   └── config.py               # App configuration
│   ├── data_collectors/            # Data fetching modules
│   ├── database/                   # Database models
│   └── utils/                      # Utility functions
├── utils/                          # Additional utilities
├── main.py                         # 🆕 Main dashboard (12 tabs)
├── game_changer_dashboard.py       # 🆕 Standalone dashboard
├── requirements.txt                # 🆕 Cloud-optimized
├── GAME_CHANGER_FEATURES.md        # 🆕 Features documentation
├── STREAMLIT_CLOUD_DEPLOYMENT.md   # 🆕 Deployment guide
└── README.md                       # This file
```

---

## 🎯 Usage Examples

### **1. Create Portfolio Snapshot**
```python
from app.analytics.social_features import SocialFeatures

social = SocialFeatures()
portfolio = pd.DataFrame({
    'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
    'Shares': [100, 50, 30],
    'Price': [178.50, 378.91, 140.22],
    'Value': [17850, 18945, 4207]
})

img_bytes = social.create_portfolio_snapshot(portfolio, "My Portfolio")
# Returns PNG bytes for download
```

### **2. Run Monte Carlo Simulation**
```python
from app.analytics.ai_lite_tools import AILiteTools

ai = AILiteTools()
ai.monte_carlo_simulation(
    ticker="AAPL",
    initial_investment=10000,
    num_simulations=10000,
    time_horizon=252  # 1 year
)
```

### **3. Backtest Trading Strategy**
```python
from app.analytics.ai_lite_tools import AILiteTools

ai = AILiteTools()
ai.backtest_strategy(
    ticker="SPY",
    strategy_type="SMA_Crossover",
    period="2y"
)
```

---

## 🌐 Deployment

### **Streamlit Cloud** (Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add Game Changer features"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to https://share.streamlit.io/
   - Connect GitHub repository
   - Select `main.py` as entry point
   - Click Deploy!

3. **Configure Secrets** (Optional):
   - Add API keys in Streamlit Cloud dashboard
   - Settings → Secrets → Add TOML config

**See detailed guide**: [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md)

---

## 📈 Performance

### **Benchmarks** (Streamlit Cloud)
- **Startup Time**: ~15-30 seconds
- **Page Load**: <2 seconds (cached)
- **Monte Carlo (10K sims)**: ~3-5 seconds
- **Sector Rotation**: <1 second
- **Portfolio Snapshot**: <2 seconds

### **Resource Usage**
- **Memory**: ~400-600 MB
- **CPU**: Low (mostly I/O bound)
- **Data Transfer**: ~5-10 MB per session

---

## 🔒 Security & Privacy

### **GDPR/KVKK Compliance** ✅
- User consent management
- Data encryption at rest
- Right to be forgotten
- Data portability
- Audit logging

### **Authentication** ✅
- JWT-based authentication
- Password hashing (bcrypt)
- Session management
- Demo user: `demo / demo123`

### **No Paid APIs Required** ✅
All features work with free data sources:
- Yahoo Finance (yfinance)
- FRED API (free tier)
- No API keys needed!

---

## 🐛 Troubleshooting

### **Problem: Import errors**
```bash
pip install -r requirements.txt --upgrade
```

### **Problem: Config errors (BACKEND_CORS_ORIGINS)**
✅ **Already fixed** in `app/core/config.py` - uses `List[str]` instead of `List[AnyHttpUrl]`

### **Problem: Port already in use**
```bash
# Kill existing Streamlit processes
lsof -ti:8501 | xargs kill -9

# Start on different port
streamlit run main.py --server.port 8502
```

### **Problem: Data not loading**
- Check internet connection
- Verify ticker symbols are correct
- Try different time period (e.g., "1y" instead of "5y")

---

## 📚 Documentation

- **Features Guide**: [GAME_CHANGER_FEATURES.md](GAME_CHANGER_FEATURES.md)
- **Deployment Guide**: [STREAMLIT_CLOUD_DEPLOYMENT.md](STREAMLIT_CLOUD_DEPLOYMENT.md)
- **API Documentation**: See code docstrings
- **Streamlit Docs**: https://docs.streamlit.io/

---

## 🎯 Roadmap

### **Phase 1 - ✅ Completed**
- [x] Social Layer (4 features)
- [x] Advanced Visualizations (4 features)
- [x] AI Tools (4 features)
- [x] Export & Share (3 features)
- [x] Streamlit Cloud deployment
- [x] CORS config fix
- [x] Documentation

### **Phase 2 - Planned**
- [ ] Real-time collaboration
- [ ] Advanced ML models (LSTM predictions)
- [ ] Custom alerts system
- [ ] Backtesting optimizer
- [ ] Social sharing (Twitter/LinkedIn)
- [ ] Portfolio database persistence
- [ ] Dark/Light theme toggle (UI)

### **Phase 3 - Future**
- [ ] Mobile app
- [ ] WebSocket real-time data
- [ ] Advanced portfolio analytics
- [ ] Options trading tools
- [ ] Crypto integration
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

**Code Style**:
- Follow PEP 8
- Add docstrings (Google style)
- Include type hints
- Write unit tests

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

- **yfinance**: Free Yahoo Finance data
- **Plotly**: Interactive visualizations
- **Streamlit**: Rapid dashboard development
- **NumPy/Pandas**: Data processing backbone
- **Community**: Open-source contributors

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/global_liquidity_dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/global_liquidity_dashboard/discussions)
- **Email**: your-email@example.com

---

## 🎉 Quick Links

- 🌐 **Live Demo**: https://financeiq.streamlit.app/
- 📚 **Documentation**: [Docs](GAME_CHANGER_FEATURES.md)
- 🚀 **Deploy Guide**: [Streamlit Cloud](STREAMLIT_CLOUD_DEPLOYMENT.md)
- 💬 **Community**: [Discussions](https://github.com/your-username/global_liquidity_dashboard/discussions)

---

**Built with ❤️ using Streamlit, Plotly, and open-source tools**

**🚀 Game Changer Features | 💰 $0 Cost | 🌐 Offline-Ready**

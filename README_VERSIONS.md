# 🐋 FinanceIQ Pro - Version Guide

## Current: Whale Intelligence Only (main.py)

**Live:** https://financeiq.streamlit.app/

**What's included:**
- 10 Whale Intelligence modules
- No authentication
- 188 lines, super fast

## Alternative: Full Platform (main_with_auth_BACKUP.py)

**What's included:**
- Everything above PLUS
- Dashboard, Stock Research, Screener
- Authentication system
- Game Changer AI tools
- 12 original tabs

**To switch back:**
```bash
cp main_with_auth_BACKUP.py main.py
git add main.py && git commit -m "Restore full platform" && git push
```

**Trade-off:** Old version had 4800 lines and rendering issues. 
New version is clean but focused only on Whale Intelligence.

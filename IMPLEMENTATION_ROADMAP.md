# 🚀 FinanceIQ - 90-Day Implementation Roadmap
## "Turkish Investor Co-Pilot" Strategy

---

## 🎯 MISSION
Transform FinanceIQ from generic dashboard → **#1 platform for Turkish retail investors**

**Target:** 1,000 paying users (₺99K/month revenue) by Day 180

---

## 📅 PHASE 1: Foundation (Days 1-30)

### Week 1-2: Core Moat Features - Data Collection

#### Feature 1: BIST Sentiment Tracker 🇹🇷
**File:** `app/analytics/turkish_sentiment.py`

```python
class TurkishSentimentTracker:
    """Real-time sentiment analysis for BIST stocks"""

    def scrape_eksisozluk(self, ticker: str):
        """Scrape Ekşi Sözlük entries for stock discussions"""
        # Parse threads like "thyao hisse yorumları"
        # Sentiment scoring: positive/negative keywords
        # Return: sentiment_score, buzz_volume, key_topics

    def scrape_twitter_turkish(self, ticker: str):
        """Turkish financial Twitter accounts"""
        # Track: @bloomberght, @ekonomim, @paraanaliz
        # Detect: "alım fırsatı", "satış baskısı", etc.

    def detect_insider_rumors(self, ticker: str):
        """Flag potential insider trading rumors"""
        # Pattern: "içeriden duydum", "kulaktan dolma", etc.
        # Alert confidence score

    def create_sentiment_dashboard(self):
        """Streamlit UI with real-time sentiment feed"""
        # Turkish stock sentiment heatmap
        # Top buzzed stocks today
        # Rumor alert feed
```

**Implementation Steps:**
1. [ ] Setup Selenium/BeautifulSoup for Ekşi scraping
2. [ ] Twitter API integration (free tier)
3. [ ] Turkish NLP library (spaCy-tr or custom)
4. [ ] Build keyword dictionaries (bullish/bearish Turkish terms)
5. [ ] Create real-time sentiment chart UI
6. [ ] Add alert system for sentiment spikes

**Tech Stack:**
- `selenium` or `requests` + `beautifulsoup4`
- `tweepy` (Twitter API)
- `spacy` with Turkish model
- `streamlit` for UI

**Success Metric:** Detect 5+ sentiment spikes per day with 70%+ accuracy

---

#### Feature 2: Tax Optimization Calculator 💰
**File:** `app/analytics/turkish_tax_calculator.py`

```python
class TurkishTaxCalculator:
    """Turkish capital gains & dividend tax optimization"""

    def calculate_stopaj(self, dividend_amount: float, holding_period: int):
        """Calculate dividend withholding tax (stopaj)"""
        # 0% if held 2+ years
        # 15% if held < 2 years
        # Return: net_dividend, tax_paid

    def calculate_capital_gains(self, buy_price: float, sell_price: float,
                                 holding_period: int):
        """Capital gains tax scenarios"""
        # Exempt if < ₺53,000 annual gain (2025)
        # Progressive tax rates
        # Return: tax_owed, net_profit

    def optimal_selling_strategy(self, portfolio: pd.DataFrame):
        """Recommend which stocks to sell first for tax efficiency"""
        # Tax-loss harvesting opportunities
        # Timing recommendations (2-year exemption)
        # Return: actionable trade list

    def usd_try_timing_optimizer(self, target_amount_usd: float):
        """Best time to buy/sell USD for stock purchases"""
        # Historical USD/TRY volatility analysis
        # TCMB intervention pattern detection
        # Return: probability of better rate in next 7/30 days
```

**Implementation Steps:**
1. [ ] Research latest Turkish tax laws (2025 rates)
2. [ ] Build progressive tax calculation engine
3. [ ] Create holding period tracker
4. [ ] Develop tax-loss harvesting algorithm
5. [ ] USD/TRY forecasting model (simple ARIMA)
6. [ ] Interactive tax scenario UI

**Success Metric:** Save users avg ₺500-1000/year in taxes

---

#### Feature 3: TCMB Decision Impact Simulator 🏦
**File:** `app/analytics/tcmb_impact_simulator.py`

```python
class TCMBImpactSimulator:
    """Simulate portfolio impact from TCMB interest rate decisions"""

    def get_tcmb_calendar(self):
        """Fetch upcoming TCMB meeting dates"""
        # Scrape from TCMB website or manual calendar
        # Return: next 3 meeting dates

    def historical_impact_analysis(self, decision_type: str, portfolio: pd.DataFrame):
        """Analyze how BIST sectors reacted to past decisions"""
        # decision_type: "rate_hike", "rate_cut", "hold"
        # Sector performance: Banking, Industrial, Tech, etc.
        # Return: expected impact % by sector

    def stress_test_portfolio(self, portfolio: pd.DataFrame, scenario: str):
        """Monte Carlo simulation for rate decision scenarios"""
        # Scenarios: +500bp, +250bp, 0bp, -250bp
        # Calculate portfolio VaR
        # Return: distribution of portfolio values

    def create_pre_meeting_report(self, portfolio: pd.DataFrame):
        """Generate PDF report before TCMB meeting"""
        # Your portfolio's risk exposure
        # Hedging recommendations
        # Historical precedent analysis
```

**Implementation Steps:**
1. [ ] Scrape TCMB website for meeting calendar
2. [ ] Collect historical BIST data around past meetings
3. [ ] Statistical analysis of sector reactions
4. [ ] Build Monte Carlo stress testing engine
5. [ ] PDF report generator
6. [ ] Email/WhatsApp alert integration

**Success Metric:** 70%+ accuracy predicting sector movements

---

### Week 3-4: Communication Layer

#### Feature 4: WhatsApp/Telegram Alert Bot 📱
**File:** `app/bots/turkish_alert_bot.py`

```python
class TurkishAlertBot:
    """WhatsApp & Telegram alert delivery system"""

    def setup_whatsapp_bot(self):
        """Using Twilio WhatsApp Business API"""
        # Free tier: 1,000 messages/month
        # Turkish language support

    def setup_telegram_bot(self):
        """Telegram Bot API (unlimited free)"""
        # Create @FinanceIQBot
        # Turkish commands: /portfoy, /uyarılar

    def send_smart_alert(self, user_id: str, alert_type: str, data: dict):
        """Send personalized alerts"""
        # Alert types:
        # - price_target: "THYAO hedef fiyatınıza ulaştı"
        # - sentiment_spike: "SASA'da anormal sosyal medya aktivitesi"
        # - insider_trade: "PETKM'de içeriden satış yapıldı"
        # - tcmb_meeting: "Yarın TCMB toplantısı - portföyünüz risk altında"

    def voice_alert_generator(self, message: str):
        """Text-to-speech in Turkish"""
        # Use Google TTS or ElevenLabs
        # Send voice message via WhatsApp
```

**Implementation Steps:**
1. [ ] Setup Twilio WhatsApp sandbox (free)
2. [ ] Create Telegram bot via BotFather
3. [ ] Build alert queue system
4. [ ] Turkish TTS integration
5. [ ] User preference management (alert frequency)
6. [ ] Testing with 10 beta users

**Success Metric:** 90%+ message delivery rate, <5 sec latency

---

## 📅 PHASE 2: Beta Launch (Days 31-60)

### Week 5-6: Turkish Broker Integration

#### Feature 5: Portfolio Auto-Import 🔗
**File:** `app/integrations/turkish_brokers.py`

**Supported Brokers:**
1. İş Yatırım (API available)
2. Enpara (CSV import)
3. Gedik Yatırım (screen scraping)
4. QNB Finans Yatırım

```python
class TurkishBrokerIntegration:
    def connect_is_yatirim(self, username: str, password: str):
        """İş Yatırım API integration"""
        # OAuth2 flow
        # Fetch: positions, transactions, cash balance

    def import_enpara_csv(self, file: UploadedFile):
        """Parse Enpara CSV exports"""
        # Map Turkish column names to standard format

    def scrape_gedik_positions(self, session_cookie: str):
        """Screen scraping Gedik portfolio"""
        # Selenium automation
        # Privacy: credentials never stored
```

**Implementation Steps:**
1. [ ] Research broker API documentation
2. [ ] Build OAuth2 flows (İş Yatırım)
3. [ ] CSV parser for manual imports
4. [ ] Selenium scraper (last resort)
5. [ ] Data normalization layer
6. [ ] Security audit (encrypt credentials)

**Success Metric:** Support 3+ brokers, 80%+ successful imports

---

### Week 7-8: Beta Testing & Iteration

**Recruitment:**
1. [ ] Post on r/BIST (Reddit)
2. [ ] Ekşi Sözlük: "fintech girişimleri" entry
3. [ ] Twitter: Reach out to @paraanaliz, @ekonomim followers
4. [ ] Facebook: Turkish stock investor groups

**Beta Program:**
- 100 beta users
- Free premium access for 3 months
- Weekly feedback surveys
- Bug bounty: ₺500 for critical bugs

**Key Metrics to Track:**
- Daily Active Users (DAU)
- Feature usage (which features most loved?)
- Churn rate
- NPS (Net Promoter Score)

**Iterate:**
- Fix top 10 bugs
- Add most-requested features
- Improve Turkish UX (language, terminology)

---

## 📅 PHASE 3: Monetization (Days 61-90)

### Week 9-10: Premium Tier Launch 💳

#### Pricing Strategy:
**Free Tier:**
- Basic dashboard
- 5 stocks in portfolio
- 3 alerts/month
- Delayed sentiment data (1 hour)

**Premium Tier - ₺99/month ($3.50):**
- Unlimited portfolio stocks
- Unlimited alerts
- Real-time sentiment data
- Tax optimization tools
- TCMB impact simulator
- WhatsApp/Telegram alerts
- Priority support

**Annual Plan - ₺999/year (₺83/month, 16% discount):**
- All Premium features
- Early access to new features
- 1-on-1 onboarding call

**Payment Methods:**
- Turkish credit cards (İyzico payment gateway)
- PayPal
- Crypto (USDT/USDC) for privacy

**Implementation:**
1. [ ] Integrate İyzico payment gateway
2. [ ] Build subscription management system
3. [ ] Create pricing page (Turkish)
4. [ ] Setup automated billing
5. [ ] Design cancellation flow (minimize churn)

---

### Week 11-12: Growth & Partnerships 🚀

#### Marketing Channels:

**1. Turkish Influencer Partnerships:**
- Target: Finance YouTubers (10K-100K subs)
- Offer: 30% revenue share on referrals
- Example: @paraanaliz, @borsahocasi

**2. Broker Partnerships:**
- İş Yatırım, Enpara: Co-marketing
- Offer: ₺50-100 per new account referral
- Integration: "Powered by FinanceIQ" badge

**3. Content Marketing:**
- Turkish blog: "BIST Stratejileri"
- Weekly newsletter: "Piyasa Analizi"
- YouTube: Short explainer videos

**4. Community Building:**
- Telegram group: "FinanceIQ Kullanıcıları"
- Monthly webinars: "TCMB Kararları Nasıl Yorumlanır?"

**Growth Target:**
- Day 90: 500 free users, 50 premium users (₺5K MRR)
- Day 180: 2,000 free users, 200 premium users (₺20K MRR)
- Day 365: 10,000 free users, 1,000 premium users (₺100K MRR)

---

## 🛠️ Technical Implementation Priorities

### Must-Have (Phase 1):
1. ✅ BIST sentiment tracker
2. ✅ Tax calculator
3. ✅ TCMB simulator
4. ✅ WhatsApp/Telegram bot

### Should-Have (Phase 2):
5. ✅ Broker integrations
6. ✅ Beta testing infrastructure
7. ⬜ Mobile-responsive UI improvements
8. ⬜ Performance optimization (caching)

### Nice-to-Have (Phase 3):
9. ⬜ AI chatbot (GPT-4o-mini integration)
10. ⬜ Dark pool tracking for BIST
11. ⬜ Community features (public portfolios)
12. ⬜ API for developers

---

## 💰 Financial Projections

### Costs (Monthly):
| Item | Cost |
|------|------|
| Streamlit Cloud Pro | $20 |
| Database (Supabase) | $25 |
| Twilio WhatsApp | $50 |
| Twitter API | Free |
| Domain + SSL | $5 |
| Marketing | ₺5,000 (~$180) |
| **Total** | **~$280/month** |

### Revenue (Month 6):
| Tier | Users | Price | Revenue |
|------|-------|-------|---------|
| Free | 1,500 | ₺0 | ₺0 |
| Premium | 200 | ₺99 | ₺19,800 (~$700) |
| Annual | 50 | ₺999 | ₺4,150/mo (~$145) |
| Broker Referrals | 50 | ₺100 | ₺5,000 (~$180) |
| **Total** | | | **₺29K (~$1,025/mo)** |

**Break-even:** ~100 premium users (Month 3-4)
**Profitable:** 200+ users (Month 6)

---

## 🎯 Success Metrics (KPIs)

### Product Metrics:
- **DAU/MAU Ratio:** >20% (sticky product)
- **Churn Rate:** <5% monthly
- **NPS Score:** >50
- **Feature Adoption:** 60%+ users use core moats

### Business Metrics:
- **MRR Growth:** 20% month-over-month
- **Customer Acquisition Cost (CAC):** <₺300
- **Lifetime Value (LTV):** >₺1,200 (12 months)
- **LTV/CAC Ratio:** >4

### Moat Metrics:
- **Sentiment Accuracy:** 70%+ correct predictions
- **Tax Savings:** Avg ₺750/user/year
- **TCMB Prediction:** 65%+ accuracy on sector moves

---

## 🚨 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Low user adoption | High | 100 beta users validate before launch |
| Scraping blocked (Ekşi) | Medium | Multiple data sources (Twitter, Telegram) |
| Broker API changes | Medium | CSV import fallback |
| Regulatory issues (SPK) | High | Legal consultation, disclaimer |
| Competitors copy features | Medium | Build community moat, fast iteration |

---

## 🏁 Decision Time: Next Steps

### If You Choose "Business Path":
1. **Immediate (This Week):**
   - [ ] Validate with 10 Turkish investors (interviews)
   - [ ] Choose 2 core moat features to build first
   - [ ] Setup project management (Trello/Notion)

2. **Month 1:**
   - [ ] Build Phase 1 features (sentiment + tax)
   - [ ] Create landing page (Turkish)
   - [ ] Start beta recruitment

3. **Month 2-3:**
   - [ ] Launch beta, iterate rapidly
   - [ ] Build remaining moat features
   - [ ] Prepare monetization infrastructure

### If You Choose "Hobby Path":
- Focus on features YOU find interesting
- No pressure on monetization
- Open-source the project for community contributions

---

## 📞 Support for Implementation

If you decide to pursue the business path, I can help you:
1. **Code the 4 core moat features** (sentiment, tax, TCMB, bot)
2. **Setup payment integration** (İyzico)
3. **Build landing page** (Turkish)
4. **Create marketing materials**
5. **Setup analytics tracking**

**Time Estimate:** 60-90 days with focused effort (20-30 hrs/week)

---

**Question:** Do you want to proceed with the "Turkish Investor Co-Pilot" strategy?
If yes, which 2 features should we build first?

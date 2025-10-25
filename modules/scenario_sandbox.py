"""
Scenario Sandbox Module
Macro economic scenario simulation and portfolio impact analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class ScenarioSandbox:
    """
    Scenario Sandbox for Portfolio Impact Analysis

    Simulates macro scenarios and calculates expected portfolio impact
    based on historical correlations and sensitivity analysis.
    """

    # Scenario Types and Parameters
    SCENARIO_TYPES = {
        'interest_rate': {
            'name': 'Faiz Oranı Değişimi',
            'name_en': 'Interest Rate Change',
            'parameters': ['tcmb_change_bp', 'fed_change_bp'],
            'affected_markets': ['BIST', 'USD/TRY', 'Bonds', 'US_Stocks']
        },
        'currency_shock': {
            'name': 'Döviz Kuru Şoku',
            'name_en': 'Currency Shock',
            'parameters': ['usd_try_change_pct', 'eur_try_change_pct'],
            'affected_markets': ['BIST', 'Exporters', 'Importers']
        },
        'commodity_price': {
            'name': 'Emtia Fiyat Değişimi',
            'name_en': 'Commodity Price Change',
            'parameters': ['oil_change_pct', 'gold_change_pct'],
            'affected_markets': ['Energy', 'Mining', 'Transportation']
        },
        'equity_shock': {
            'name': 'Piyasa Şoku',
            'name_en': 'Equity Market Shock',
            'parameters': ['sp500_change_pct', 'bist100_change_pct'],
            'affected_markets': ['All_Stocks']
        },
        'combined': {
            'name': 'Kombine Senaryo',
            'name_en': 'Combined Scenario',
            'parameters': ['custom'],
            'affected_markets': ['All']
        }
    }

    # Historical Correlation Matrix (based on 2018-2024 data)
    # These are simplified correlations - in production, use actual historical data
    CORRELATIONS = {
        # TCMB Interest Rate Impact
        'tcmb_rate_vs_bist': {
            'BIST_Finans': -0.68,      # Banks negatively correlated
            'BIST_Sanayi': -0.52,      # Industrials
            'BIST_Teknoloji': -0.45,   # Technology
            'BIST_Tüketim': -0.38,     # Consumer
            'BIST_Enerji': -0.30,      # Energy
            'USD/TRY': 0.75            # Currency positively correlated
        },

        # FED Rate Impact on US Markets
        'fed_rate_vs_us': {
            'US_Tech': -0.55,          # Tech sensitive to rates
            'US_Finance': 0.35,        # Banks benefit from higher rates
            'US_Consumer': -0.40,
            'US_Energy': -0.25
        },

        # USD/TRY Impact on BIST Sectors
        'usd_try_vs_bist': {
            'BIST_Exporters': 0.65,    # Exporters benefit from weak TRY
            'BIST_Importers': -0.70,   # Importers hurt by weak TRY
            'BIST_Tourism': 0.55,      # Tourism benefits
            'BIST_Energy': -0.60       # Energy (oil import heavy)
        },

        # Oil Price Impact
        'oil_vs_sectors': {
            'Energy': 0.85,            # Strong positive
            'Airlines': -0.75,         # Strong negative
            'Transportation': -0.60,
            'Petrochemicals': 0.70
        },

        # Gold Price Impact
        'gold_vs_sectors': {
            'Mining': 0.90,            # Very strong
            'Gold_Producers': 0.95,
            'Tech': -0.15,             # Weak negative (safe haven rotation)
            'Financials': -0.25
        }
    }

    # Sector Classification (Turkish stocks)
    SECTOR_CLASSIFICATION = {
        'BIST_Finans': ['GARAN', 'YKBNK', 'AKBNK', 'ISCTR', 'VAKBN', 'HALKB'],
        'BIST_Sanayi': ['THYAO', 'DOAS', 'PGSUS', 'TTKOM', 'ARCLK'],
        'BIST_Teknoloji': ['ASELS', 'LOGO', 'KAREL', 'NETAS', 'INDES'],
        'BIST_Tüketim': ['BIMAS', 'MGROS', 'SOKM', 'CCOLA', 'ULKER'],
        'BIST_Enerji': ['TUPRS', 'PETKM', 'AKSA', 'AKENR', 'ZOREN'],
        'BIST_Exporters': ['VESTL', 'EREGL', 'KRDMD', 'FROTO'],
        'BIST_Importers': ['THYAO', 'TTKOM', 'PETKM']
    }

    def __init__(self):
        self.scenarios = []
        self.results = []

    def create_scenario(
        self,
        scenario_type: str,
        scenario_name: str = None,
        **parameters
    ) -> Dict:
        """
        Create a macro economic scenario

        Args:
            scenario_type: Type from SCENARIO_TYPES
            scenario_name: Custom name for scenario
            **parameters: Scenario-specific parameters

        Returns:
            Scenario configuration dict
        """
        if scenario_type not in self.SCENARIO_TYPES:
            raise ValueError(f"Unknown scenario type: {scenario_type}")

        scenario = {
            'id': len(self.scenarios) + 1,
            'type': scenario_type,
            'name': scenario_name or self.SCENARIO_TYPES[scenario_type]['name'],
            'created_at': datetime.now().isoformat(),
            'parameters': parameters,
            'config': self.SCENARIO_TYPES[scenario_type]
        }

        self.scenarios.append(scenario)
        return scenario

    def simulate_portfolio_impact(
        self,
        portfolio: pd.DataFrame,
        scenario: Dict
    ) -> pd.DataFrame:
        """
        Calculate expected portfolio impact from scenario

        Args:
            portfolio: DataFrame with columns [Symbol, Shares, Price, Value, Weight, Sector]
            scenario: Scenario dict from create_scenario()

        Returns:
            DataFrame with impact analysis per position
        """
        # Calculate Value and Weight if missing
        if 'Value' not in portfolio.columns and 'Shares' in portfolio.columns:
            # Calculate Value from Shares * Price
            price_col = 'Current_Price' if 'Current_Price' in portfolio.columns else 'Purchase_Price'
            portfolio['Value'] = portfolio['Shares'] * portfolio[price_col]

        if 'Weight' not in portfolio.columns:
            total_value = portfolio['Value'].sum()
            portfolio['Weight'] = portfolio['Value'] / total_value

        # Add Sector if missing
        if 'Sector' not in portfolio.columns:
            portfolio['Sector'] = portfolio['Symbol'].apply(self._classify_stock_sector)

        results = portfolio.copy()

        # Calculate expected change per position
        scenario_type = scenario['type']
        params = scenario['parameters']

        if scenario_type == 'interest_rate':
            results['Expected_Change'] = results.apply(
                lambda row: self._calc_interest_rate_impact(row, params),
                axis=1
            )

        elif scenario_type == 'currency_shock':
            results['Expected_Change'] = results.apply(
                lambda row: self._calc_currency_impact(row, params),
                axis=1
            )

        elif scenario_type == 'commodity_price':
            results['Expected_Change'] = results.apply(
                lambda row: self._calc_commodity_impact(row, params),
                axis=1
            )

        elif scenario_type == 'equity_shock':
            results['Expected_Change'] = results.apply(
                lambda row: self._calc_equity_shock_impact(row, params),
                axis=1
            )

        elif scenario_type == 'combined':
            # Sum all impact types
            results['Expected_Change'] = 0.0

            # Interest rate impact
            ir_impact = results.apply(
                lambda row: self._calc_interest_rate_impact(row, params),
                axis=1
            )
            results['Expected_Change'] += ir_impact

            # Currency impact
            curr_impact = results.apply(
                lambda row: self._calc_currency_impact(row, params),
                axis=1
            )
            results['Expected_Change'] += curr_impact

            # Commodity impact
            comm_impact = results.apply(
                lambda row: self._calc_commodity_impact(row, params),
                axis=1
            )
            results['Expected_Change'] += comm_impact

            # Equity shock impact
            eq_impact = results.apply(
                lambda row: self._calc_equity_shock_impact(row, params),
                axis=1
            )
            results['Expected_Change'] += eq_impact

        else:
            # Default: no change
            results['Expected_Change'] = 0.0

        # Calculate new values
        price_col = 'Current_Price' if 'Current_Price' in results.columns else 'Purchase_Price'
        results['Price'] = results[price_col]  # Set Price column
        results['Estimated_New_Price'] = results['Price'] * (1 + results['Expected_Change'] / 100)
        results['New_Value'] = results['Estimated_New_Price'] * results['Shares']
        results['Value_Change'] = results['New_Value'] - results['Value']
        results['Impact_Pct'] = (results['New_Value'] - results['Value']) / results['Value'] * 100

        # Portfolio-level metrics
        total_old_value = results['Value'].sum()
        total_new_value = results['New_Value'].sum()
        portfolio_change_pct = ((total_new_value - total_old_value) / total_old_value) * 100

        results.attrs['portfolio_old_value'] = total_old_value
        results.attrs['portfolio_new_value'] = total_new_value
        results.attrs['portfolio_change_pct'] = portfolio_change_pct
        results.attrs['scenario'] = scenario

        return results

    def _classify_stock_sector(self, symbol: str) -> str:
        """Classify stock into sector"""
        symbol_clean = symbol.replace('.IS', '').upper()

        for sector, stocks in self.SECTOR_CLASSIFICATION.items():
            if symbol_clean in stocks:
                return sector

        # Default classifications based on common patterns
        if symbol_clean in ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD']:
            return 'US_Tech'
        elif symbol_clean in ['JPM', 'BAC', 'WFC', 'C']:
            return 'US_Finance'
        elif symbol_clean in ['XOM', 'CVX', 'COP']:
            return 'US_Energy'
        else:
            return 'Other'

    def _calc_interest_rate_impact(self, row: pd.Series, params: Dict) -> float:
        """Calculate interest rate change impact"""
        tcmb_change_bp = params.get('tcmb_change_bp', 0)
        fed_change_bp = params.get('fed_change_bp', 0)

        sector = row['Sector']
        impact = 0.0

        # TCMB impact
        if sector in self.CORRELATIONS['tcmb_rate_vs_bist']:
            correlation = self.CORRELATIONS['tcmb_rate_vs_bist'][sector]
            # Rule of thumb: 100bp rate change → correlation% stock change
            impact += (tcmb_change_bp / 100) * correlation

        # FED impact on US stocks
        if sector in self.CORRELATIONS['fed_rate_vs_us']:
            correlation = self.CORRELATIONS['fed_rate_vs_us'][sector]
            impact += (fed_change_bp / 100) * correlation

        # USD/TRY indirect impact (rates affect currency)
        if tcmb_change_bp != 0:
            usd_try_impact = (tcmb_change_bp / 100) * 0.75  # From correlation matrix
            if sector in self.CORRELATIONS['usd_try_vs_bist']:
                currency_correlation = self.CORRELATIONS['usd_try_vs_bist'][sector]
                impact += usd_try_impact * currency_correlation * 0.5  # Dampened effect

        return impact

    def _calc_currency_impact(self, row: pd.Series, params: Dict) -> float:
        """Calculate currency shock impact"""
        usd_try_change_pct = params.get('usd_try_change_pct', 0)
        sector = row['Sector']

        if sector in self.CORRELATIONS['usd_try_vs_bist']:
            correlation = self.CORRELATIONS['usd_try_vs_bist'][sector]
            impact = usd_try_change_pct * correlation
        else:
            # Default: slight negative for most stocks (imported inputs)
            impact = usd_try_change_pct * -0.15

        return impact

    def _calc_commodity_impact(self, row: pd.Series, params: Dict) -> float:
        """Calculate commodity price impact"""
        oil_change_pct = params.get('oil_change_pct', 0)
        gold_change_pct = params.get('gold_change_pct', 0)
        sector = row['Sector']

        impact = 0.0

        # Oil impact
        if oil_change_pct != 0:
            if sector in self.CORRELATIONS['oil_vs_sectors']:
                oil_correlation = self.CORRELATIONS['oil_vs_sectors'][sector]
                impact += oil_change_pct * oil_correlation
            elif sector == 'BIST_Enerji':
                impact += oil_change_pct * 0.70  # Energy sector benefits

        # Gold impact
        if gold_change_pct != 0:
            if sector in self.CORRELATIONS['gold_vs_sectors']:
                gold_correlation = self.CORRELATIONS['gold_vs_sectors'][sector]
                impact += gold_change_pct * gold_correlation

        return impact

    def _calc_equity_shock_impact(self, row: pd.Series, params: Dict) -> float:
        """Calculate equity market shock impact"""
        sp500_change = params.get('sp500_change_pct', 0)
        bist100_change = params.get('bist100_change_pct', 0)
        sector = row['Sector']

        # Turkish stocks follow BIST
        if sector.startswith('BIST_'):
            # Beta assumption: most stocks ~1.0 to index
            beta = 1.0
            if sector == 'BIST_Finans':
                beta = 1.2  # Banks more volatile
            elif sector == 'BIST_Tüketim':
                beta = 0.8  # Consumer defensive

            return bist100_change * beta

        # US stocks follow S&P500
        elif sector.startswith('US_'):
            beta = 1.0
            if sector == 'US_Tech':
                beta = 1.3
            elif sector == 'US_Finance':
                beta = 1.1

            return sp500_change * beta

        else:
            # Default: follow both markets weighted
            return (sp500_change * 0.6 + bist100_change * 0.4)

    def stress_test_portfolio(
        self,
        portfolio: pd.DataFrame,
        scenarios: List[str] = None
    ) -> Dict:
        """
        Run multiple stress test scenarios

        Args:
            portfolio: Portfolio DataFrame
            scenarios: List of predefined scenario names or None for all

        Returns:
            Dict with stress test results
        """
        predefined_scenarios = {
            '2018_currency_crisis': {
                'type': 'currency_shock',
                'name': '2018 Kur Krizi Tekrarı',
                'parameters': {'usd_try_change_pct': 40}
            },
            '2020_covid_crash': {
                'type': 'equity_shock',
                'name': '2020 COVID Şoku Tekrarı',
                'parameters': {'sp500_change_pct': -30, 'bist100_change_pct': -25}
            },
            'tcmb_hike_500bp': {
                'type': 'interest_rate',
                'name': 'TCMB 500bp Faiz Artışı',
                'parameters': {'tcmb_change_bp': 500}
            },
            'oil_shock_50pct': {
                'type': 'commodity_price',
                'name': 'Petrol %50 Artış',
                'parameters': {'oil_change_pct': 50}
            }
        }

        if scenarios is None:
            scenarios = list(predefined_scenarios.keys())

        results = {}

        for scenario_key in scenarios:
            if scenario_key in predefined_scenarios:
                scenario_config = predefined_scenarios[scenario_key]
                scenario = self.create_scenario(**scenario_config)
                impact_df = self.simulate_portfolio_impact(portfolio, scenario)

                results[scenario_key] = {
                    'scenario': scenario,
                    'portfolio_change_pct': impact_df.attrs['portfolio_change_pct'],
                    'new_value': impact_df.attrs['portfolio_new_value'],
                    'worst_stock': impact_df.nsmallest(1, 'Expected_Change').iloc[0]['Symbol'],
                    'best_stock': impact_df.nlargest(1, 'Expected_Change').iloc[0]['Symbol']
                }

        return results

    def calculate_var(
        self,
        portfolio_df: pd.DataFrame,
        confidence_level: float = 0.95,
        num_simulations: int = 1000,
        time_horizon_days: int = 10
    ) -> Dict:
        """
        Calculate Value at Risk (VaR) using Monte Carlo simulation

        Args:
            portfolio: Portfolio DataFrame
            confidence_level: Confidence level (default 95%)
            num_simulations: Number of Monte Carlo simulations

        Returns:
            Dict with VaR metrics
        """
        simulation_returns = []

        # Calculate initial portfolio value
        if 'Value' not in portfolio_df.columns:
            price_col = 'Current_Price' if 'Current_Price' in portfolio_df.columns else 'Purchase_Price'
            portfolio_df['Value'] = portfolio_df['Shares'] * portfolio_df[price_col]

        initial_value = portfolio_df['Value'].sum()

        for _ in range(num_simulations):
            # Generate random scenario
            scenario = self._generate_random_scenario()
            impact_df = self.simulate_portfolio_impact(portfolio_df, scenario)
            new_value = impact_df['New_Value'].sum()

            # Calculate return percentage
            return_pct = ((new_value - initial_value) / initial_value) * 100
            simulation_returns.append(return_pct)

        simulation_returns = np.array(simulation_returns)

        # Calculate VaR (Value at Risk)
        sorted_returns = np.sort(simulation_returns)
        var_index = int((1 - confidence_level) * num_simulations)
        var_pct = sorted_returns[var_index]

        # Calculate CVaR (Conditional VaR / Expected Shortfall)
        cvar_pct = sorted_returns[:var_index].mean() if var_index > 0 else var_pct

        # Calculate monetary amounts
        var_amount = initial_value * (var_pct / 100)
        cvar_amount = initial_value * (cvar_pct / 100)

        return {
            'confidence_level': confidence_level,
            'time_horizon_days': time_horizon_days,
            'num_simulations': num_simulations,
            'portfolio_value': initial_value,
            'var_pct': var_pct,
            'var_amount': var_amount,
            'cvar_pct': cvar_pct,
            'cvar_amount': cvar_amount,
            'simulation_returns': simulation_returns.tolist(),
            'mean_return': np.mean(simulation_returns),
            'std_return': np.std(simulation_returns),
            'worst_case': np.min(simulation_returns),
            'best_case': np.max(simulation_returns)
        }

    def _generate_random_scenario(self) -> Dict:
        """Generate random scenario for Monte Carlo"""
        scenario_types = ['interest_rate', 'currency_shock', 'commodity_price', 'equity_shock']
        scenario_type = np.random.choice(scenario_types)

        if scenario_type == 'interest_rate':
            params = {
                'tcmb_change_bp': np.random.normal(0, 200),  # Mean 0, std 200bp
                'fed_change_bp': np.random.normal(0, 100)
            }
        elif scenario_type == 'currency_shock':
            params = {
                'usd_try_change_pct': np.random.normal(0, 10)  # Mean 0, std 10%
            }
        elif scenario_type == 'commodity_price':
            params = {
                'oil_change_pct': np.random.normal(0, 20),
                'gold_change_pct': np.random.normal(0, 15)
            }
        else:  # equity_shock
            params = {
                'sp500_change_pct': np.random.normal(0, 15),
                'bist100_change_pct': np.random.normal(0, 20)
            }

        return self.create_scenario(scenario_type, "Random Scenario", **params)


# Convenience functions
def quick_scenario(
    portfolio: pd.DataFrame,
    scenario_type: str,
    **params
) -> pd.DataFrame:
    """Quick scenario simulation"""
    sandbox = ScenarioSandbox()
    scenario = sandbox.create_scenario(scenario_type, **params)
    return sandbox.simulate_portfolio_impact(portfolio, scenario)


def stress_test(portfolio: pd.DataFrame) -> Dict:
    """Quick stress test"""
    sandbox = ScenarioSandbox()
    return sandbox.stress_test_portfolio(portfolio)

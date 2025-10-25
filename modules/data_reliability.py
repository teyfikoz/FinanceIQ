"""
Data Reliability Audit System
Verify ETF holdings data integrity and detect anomalies
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class DataReliabilityAuditor:
    """
    Data Reliability Auditor for ETF Holdings

    Features:
    - Detect weight jumps (>20% change)
    - Validate data freshness
    - Check for missing critical data
    - Generate audit reports
    """

    def __init__(self, db_path: str = "data/etf_holdings.db"):
        self.db_path = db_path
        self.audit_log = []

    def run_full_audit(self) -> Dict:
        """
        Run comprehensive data audit

        Returns:
            Dict with audit results and recommendations
        """
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'checks_passed': 0,
            'checks_failed': 0,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }

        # Check 1: Database connectivity
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            audit_results['checks_passed'] += 1
        except Exception as e:
            audit_results['checks_failed'] += 1
            audit_results['errors'].append(f"Database connection failed: {e}")
            return audit_results

        # Check 2: Data freshness
        freshness_result = self._check_data_freshness()
        if freshness_result['status'] == 'pass':
            audit_results['checks_passed'] += 1
        elif freshness_result['status'] == 'warning':
            audit_results['warnings'].append(freshness_result['message'])
        else:
            audit_results['checks_failed'] += 1
            audit_results['errors'].append(freshness_result['message'])

        # Check 3: Weight consistency
        weight_result = self._check_weight_consistency()
        audit_results['checks_passed'] += weight_result['passed']
        audit_results['checks_failed'] += weight_result['failed']
        audit_results['warnings'].extend(weight_result['warnings'])

        # Check 4: Anomaly detection
        anomaly_result = self._detect_weight_anomalies()
        if len(anomaly_result['anomalies']) > 0:
            audit_results['warnings'].append(
                f"Found {len(anomaly_result['anomalies'])} weight anomalies"
            )

        # Check 5: Data coverage
        coverage_result = self._check_data_coverage()
        if coverage_result['coverage_pct'] < 80:
            audit_results['warnings'].append(
                f"Data coverage only {coverage_result['coverage_pct']:.0f}% (target: 80%+)"
            )

        # Generate recommendations
        if audit_results['checks_failed'] > 0:
            audit_results['recommendations'].append("❌ Critical issues found - immediate action required")

        if len(audit_results['warnings']) > 3:
            audit_results['recommendations'].append("⚠️ Multiple warnings - schedule data refresh")

        days_old = freshness_result.get('days_old')
        if days_old is not None and days_old > 7:
            audit_results['recommendations'].append("🔄 Data is stale - run ETF update")

        # Calculate overall health score
        total_checks = audit_results['checks_passed'] + audit_results['checks_failed']
        if total_checks > 0:
            health_score = (audit_results['checks_passed'] / total_checks) * 100
            audit_results['health_score'] = round(health_score, 1)
        else:
            audit_results['health_score'] = 0

        return audit_results

    def _check_data_freshness(self) -> Dict:
        """Check if data is recent (< 7 days old)"""
        conn = sqlite3.connect(self.db_path)

        try:
            query = "SELECT MAX(report_date) as latest_date FROM holdings"
            result = pd.read_sql_query(query, conn)

            if result.empty or pd.isna(result['latest_date'].iloc[0]):
                conn.close()
                return {
                    'status': 'fail',
                    'message': 'No data found in database',
                    'days_old': None
                }

            latest_date = pd.to_datetime(result['latest_date'].iloc[0])
            days_old = (datetime.now() - latest_date).days

            conn.close()

            if days_old <= 7:
                return {
                    'status': 'pass',
                    'message': f'Data is fresh ({days_old} days old)',
                    'days_old': days_old
                }
            elif days_old <= 30:
                return {
                    'status': 'warning',
                    'message': f'Data is {days_old} days old (recommended: <7 days)',
                    'days_old': days_old
                }
            else:
                return {
                    'status': 'fail',
                    'message': f'Data is stale ({days_old} days old) - update required',
                    'days_old': days_old
                }

        except Exception as e:
            conn.close()
            return {
                'status': 'fail',
                'message': f'Freshness check failed: {e}',
                'days_old': None
            }

    def _check_weight_consistency(self) -> Dict:
        """Check if weights are valid (0-100, sum to ~100%)"""
        conn = sqlite3.connect(self.db_path)
        result = {'passed': 0, 'failed': 0, 'warnings': []}

        try:
            # Get latest holdings per fund
            query = """
                SELECT fund_code, SUM(weight_pct) as total_weight
                FROM holdings
                WHERE report_date = (SELECT MAX(report_date) FROM holdings)
                GROUP BY fund_code
            """

            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                result['failed'] += 1
                result['warnings'].append("No holdings data to validate")
                return result

            # Check each fund
            for idx, row in df.iterrows():
                fund_code = row['fund_code']
                total_weight = row['total_weight']

                # Weight should be between 90-110% (allowing some tolerance)
                if 90 <= total_weight <= 110:
                    result['passed'] += 1
                else:
                    result['failed'] += 1
                    result['warnings'].append(
                        f"{fund_code}: Total weight {total_weight:.1f}% (expected ~100%)"
                    )

            return result

        except Exception as e:
            conn.close()
            result['failed'] += 1
            result['warnings'].append(f"Weight consistency check failed: {e}")
            return result

    def _detect_weight_anomalies(self, threshold: float = 20.0) -> Dict:
        """
        Detect unusual weight changes (>20% jump)

        Args:
            threshold: Minimum weight change to flag (default 20%)
        """
        conn = sqlite3.connect(self.db_path)
        anomalies = []

        try:
            # Get weight changes
            query = """
                WITH ranked_holdings AS (
                    SELECT
                        fund_code,
                        stock_symbol,
                        weight_pct,
                        report_date,
                        LAG(weight_pct) OVER (
                            PARTITION BY fund_code, stock_symbol
                            ORDER BY report_date
                        ) as prev_weight
                    FROM holdings
                )
                SELECT
                    fund_code,
                    stock_symbol,
                    prev_weight,
                    weight_pct as current_weight,
                    (weight_pct - prev_weight) as weight_change,
                    report_date
                FROM ranked_holdings
                WHERE prev_weight IS NOT NULL
                AND ABS(weight_pct - prev_weight) > ?
                ORDER BY ABS(weight_pct - prev_weight) DESC
                LIMIT 50
            """

            df = pd.read_sql_query(query, conn, params=(threshold,))
            conn.close()

            for idx, row in df.iterrows():
                anomalies.append({
                    'fund': row['fund_code'],
                    'stock': row['stock_symbol'],
                    'prev_weight': row['prev_weight'],
                    'current_weight': row['current_weight'],
                    'change': row['weight_change'],
                    'date': row['report_date'],
                    'severity': 'high' if abs(row['weight_change']) > 50 else 'medium'
                })

            return {
                'anomalies': anomalies,
                'count': len(anomalies)
            }

        except Exception as e:
            conn.close()
            return {
                'anomalies': [],
                'count': 0,
                'error': str(e)
            }

    def _check_data_coverage(self) -> Dict:
        """Check what percentage of tracked ETFs have recent data"""
        from modules.etf_weight_tracker import ETFWeightTracker

        tracker = ETFWeightTracker(db_path=self.db_path)
        tracked_etfs = list(tracker.TRACKED_ETFS.keys())

        conn = sqlite3.connect(self.db_path)

        try:
            # Get ETFs with recent data (< 30 days)
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            query = """
                SELECT DISTINCT fund_code
                FROM holdings
                WHERE report_date >= ?
            """

            df = pd.read_sql_query(query, conn, params=(cutoff_date,))
            conn.close()

            etfs_with_data = set(df['fund_code'].tolist())
            coverage_pct = (len(etfs_with_data) / len(tracked_etfs)) * 100

            return {
                'tracked_etfs': len(tracked_etfs),
                'etfs_with_data': len(etfs_with_data),
                'coverage_pct': coverage_pct,
                'missing_etfs': [etf for etf in tracked_etfs if etf not in etfs_with_data]
            }

        except Exception as e:
            conn.close()
            return {
                'tracked_etfs': len(tracked_etfs),
                'etfs_with_data': 0,
                'coverage_pct': 0,
                'error': str(e)
            }

    def generate_audit_report(self) -> str:
        """Generate human-readable audit report"""
        audit_results = self.run_full_audit()

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║        FinanceIQ Pro - Data Reliability Audit Report        ║
╚══════════════════════════════════════════════════════════════╝

Timestamp: {audit_results['timestamp']}
Health Score: {audit_results['health_score']:.1f}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 AUDIT SUMMARY:
  ✅ Checks Passed: {audit_results['checks_passed']}
  ❌ Checks Failed: {audit_results['checks_failed']}
  ⚠️  Warnings: {len(audit_results['warnings'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        if audit_results['errors']:
            report += "🔴 ERRORS:\n"
            for error in audit_results['errors']:
                report += f"  • {error}\n"
            report += "\n"

        if audit_results['warnings']:
            report += "⚠️  WARNINGS:\n"
            for warning in audit_results['warnings']:
                report += f"  • {warning}\n"
            report += "\n"

        if audit_results['recommendations']:
            report += "💡 RECOMMENDATIONS:\n"
            for rec in audit_results['recommendations']:
                report += f"  • {rec}\n"
            report += "\n"

        report += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        if audit_results['health_score'] >= 90:
            report += "✅ Status: EXCELLENT - Data is reliable and up-to-date\n"
        elif audit_results['health_score'] >= 70:
            report += "⚠️  Status: GOOD - Minor issues detected, monitoring recommended\n"
        elif audit_results['health_score'] >= 50:
            report += "⚠️  Status: FAIR - Action recommended to improve data quality\n"
        else:
            report += "🔴 Status: POOR - Immediate action required\n"

        report += "\n"

        return report

    def save_audit_log(self, output_path: str = "data/audit_log.txt"):
        """Save audit report to file"""
        report = self.generate_audit_report()

        with open(output_path, 'a') as f:
            f.write(report)
            f.write("\n" + "="*70 + "\n\n")

        return output_path


def verify_data_integrity():
    """
    Main verification function
    Can be run as cron job
    """
    auditor = DataReliabilityAuditor()

    print("🔍 Running Data Reliability Audit...\n")

    report = auditor.generate_audit_report()
    print(report)

    # Save to log file
    log_path = auditor.save_audit_log()
    print(f"📝 Audit log saved to: {log_path}")

    # Return results for programmatic access
    return auditor.run_full_audit()


if __name__ == "__main__":
    verify_data_integrity()

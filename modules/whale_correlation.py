"""
Whale Correlation Engine - Portfolio correlation and investment DNA analysis
Analyzes relationships between legendary investors and user portfolios
"""

import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple, Optional
import functools


class WhaleCorrelationEngine:
    """
    Analyzes portfolio correlations between whale investors
    and compares user portfolios to legendary investors
    """

    def __init__(self):
        """Initialize Whale Correlation Engine"""
        self.correlation_threshold_high = 0.7
        self.correlation_threshold_medium = 0.5
        self.correlation_threshold_low = 0.3

    def calculate_portfolio_correlation(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        weight_col: str = 'portfolio_weight'
    ) -> float:
        """
        Calculate correlation between two portfolios based on holdings weights

        Args:
            df_a: First portfolio DataFrame with 'ticker' and weight column
            df_b: Second portfolio DataFrame with 'ticker' and weight column
            weight_col: Name of weight column (default: 'portfolio_weight')

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if df_a is None or df_b is None or len(df_a) == 0 or len(df_b) == 0:
            return 0.0

        # Merge on ticker
        merged = pd.merge(
            df_a[['ticker', weight_col]],
            df_b[['ticker', weight_col]],
            on='ticker',
            how='inner',
            suffixes=('_a', '_b')
        )

        if len(merged) == 0:
            return 0.0

        # Calculate Pearson correlation
        corr = merged[f'{weight_col}_a'].corr(merged[f'{weight_col}_b'])

        return corr if not np.isnan(corr) else 0.0

    def calculate_overlap_percentage(
        self,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate overlap metrics between two portfolios

        Returns:
            Dict with overlap_percentage and common_holdings_count
        """
        if df_a is None or df_b is None or len(df_a) == 0 or len(df_b) == 0:
            return {'overlap_percentage': 0.0, 'common_holdings': 0}

        tickers_a = set(df_a['ticker'].unique())
        tickers_b = set(df_b['ticker'].unique())

        common = tickers_a.intersection(tickers_b)
        total_unique = tickers_a.union(tickers_b)

        overlap_pct = (len(common) / len(total_unique)) * 100 if len(total_unique) > 0 else 0.0

        return {
            'overlap_percentage': overlap_pct,
            'common_holdings': len(common)
        }

    def build_correlation_matrix(
        self,
        whale_data_dict: Dict[str, pd.DataFrame],
        weight_col: str = 'portfolio_weight'
    ) -> pd.DataFrame:
        """
        Build correlation matrix for all whale investors

        Args:
            whale_data_dict: Dictionary mapping investor names to portfolio DataFrames
            weight_col: Weight column name

        Returns:
            Correlation matrix DataFrame (NxN where N is number of investors)
        """
        investor_names = list(whale_data_dict.keys())
        n = len(investor_names)

        # Initialize correlation matrix
        corr_matrix = pd.DataFrame(
            np.eye(n),  # Diagonal = 1.0 (self-correlation)
            index=investor_names,
            columns=investor_names
        )

        # Calculate pairwise correlations
        for i, name_a in enumerate(investor_names):
            for j, name_b in enumerate(investor_names):
                if i < j:  # Only calculate upper triangle (symmetric)
                    corr = self.calculate_portfolio_correlation(
                        whale_data_dict[name_a],
                        whale_data_dict[name_b],
                        weight_col
                    )
                    corr_matrix.loc[name_a, name_b] = corr
                    corr_matrix.loc[name_b, name_a] = corr  # Symmetry

        return corr_matrix

    def build_overlap_matrix(
        self,
        whale_data_dict: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Build overlap matrix showing common holdings percentage

        Returns:
            Overlap matrix DataFrame
        """
        investor_names = list(whale_data_dict.keys())
        n = len(investor_names)

        overlap_matrix = pd.DataFrame(
            100.0 * np.eye(n),  # Diagonal = 100% (self-overlap)
            index=investor_names,
            columns=investor_names
        )

        for i, name_a in enumerate(investor_names):
            for j, name_b in enumerate(investor_names):
                if i < j:
                    metrics = self.calculate_overlap_percentage(
                        whale_data_dict[name_a],
                        whale_data_dict[name_b]
                    )
                    overlap_pct = metrics['overlap_percentage']
                    overlap_matrix.loc[name_a, name_b] = overlap_pct
                    overlap_matrix.loc[name_b, name_a] = overlap_pct

        return overlap_matrix

    def compare_user_to_whales(
        self,
        user_df: pd.DataFrame,
        whale_data_dict: Dict[str, pd.DataFrame],
        weight_col: str = 'portfolio_weight'
    ) -> pd.DataFrame:
        """
        Compare user portfolio to all whale investors

        Returns:
            DataFrame with columns: Investor, Correlation, Overlap%, Common_Holdings
            Sorted by correlation (descending)
        """
        results = []

        for name, whale_df in whale_data_dict.items():
            # Calculate correlation
            corr = self.calculate_portfolio_correlation(user_df, whale_df, weight_col)

            # Calculate overlap
            overlap_metrics = self.calculate_overlap_percentage(user_df, whale_df)

            results.append({
                'Investor': name,
                'Similarity_Score': round(corr * 100, 1),
                'Overlap_Percentage': round(overlap_metrics['overlap_percentage'], 1),
                'Common_Holdings': overlap_metrics['common_holdings']
            })

        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('Similarity_Score', ascending=False)

        return df_results

    def identify_whale_clusters(
        self,
        corr_matrix: pd.DataFrame,
        threshold: float = 0.6
    ) -> List[List[str]]:
        """
        Identify clusters of highly correlated investors

        Args:
            corr_matrix: Correlation matrix
            threshold: Minimum correlation to form a cluster

        Returns:
            List of clusters (each cluster is a list of investor names)
        """
        # Build graph
        G = nx.Graph()

        for i in corr_matrix.index:
            for j in corr_matrix.columns:
                if i != j and corr_matrix.loc[i, j] >= threshold:
                    G.add_edge(i, j, weight=corr_matrix.loc[i, j])

        # Find connected components (clusters)
        clusters = list(nx.connected_components(G))

        # Convert sets to lists and sort by size
        clusters = [sorted(list(cluster)) for cluster in clusters]
        clusters = sorted(clusters, key=len, reverse=True)

        return clusters

    def plot_correlation_heatmap(
        self,
        corr_matrix: pd.DataFrame,
        title: str = "Whale Portfolio Correlation Matrix"
    ) -> go.Figure:
        """
        Create interactive heatmap of correlation matrix

        Returns:
            Plotly Figure object
        """
        fig = px.imshow(
            corr_matrix,
            color_continuous_scale='RdYlGn',
            zmin=-1,
            zmax=1,
            text_auto='.2f',
            aspect='auto',
            title=title
        )

        fig.update_layout(
            xaxis_title="",
            yaxis_title="",
            height=500
        )

        fig.update_traces(
            hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.3f}<extra></extra>"
        )

        return fig

    def plot_overlap_heatmap(
        self,
        overlap_matrix: pd.DataFrame,
        title: str = "Whale Portfolio Overlap (%)"
    ) -> go.Figure:
        """
        Create interactive heatmap of overlap matrix

        Returns:
            Plotly Figure object
        """
        fig = px.imshow(
            overlap_matrix,
            color_continuous_scale='Blues',
            zmin=0,
            zmax=100,
            text_auto='.1f',
            aspect='auto',
            title=title
        )

        fig.update_layout(
            xaxis_title="",
            yaxis_title="",
            height=500
        )

        fig.update_traces(
            hovertemplate="<b>%{x}</b> & <b>%{y}</b><br>Overlap: %{z:.1f}%<extra></extra>"
        )

        return fig

    def plot_whale_network(
        self,
        corr_matrix: pd.DataFrame,
        threshold: float = 0.5,
        title: str = "Whale Relationship Network"
    ) -> go.Figure:
        """
        Create network graph showing whale relationships

        Args:
            corr_matrix: Correlation matrix
            threshold: Minimum correlation to draw edge

        Returns:
            Plotly Figure object
        """
        # Build graph
        G = nx.Graph()

        for name in corr_matrix.index:
            G.add_node(name)

        for i in corr_matrix.index:
            for j in corr_matrix.columns:
                if i != j and corr_matrix.loc[i, j] >= threshold:
                    G.add_edge(i, j, weight=corr_matrix.loc[i, j])

        if len(G.edges()) == 0:
            # No connections above threshold
            pos = nx.spring_layout(G, k=1, iterations=50)
        else:
            pos = nx.spring_layout(G, k=0.8, iterations=50)

        # Create edge traces
        edge_traces = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            weight = G.edges[edge]['weight']

            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(
                    width=weight * 5,
                    color=f'rgba(102, 126, 234, {weight})'
                ),
                hoverinfo='none',
                showlegend=False
            )
            edge_traces.append(edge_trace)

        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_size = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            # Node size based on degree (number of connections)
            node_size.append(20 + G.degree(node) * 10)

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            textfont=dict(size=12, color='black'),
            marker=dict(
                size=node_size,
                color='#667eea',
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>%{text}</b><br>Connections: %{marker.size}<extra></extra>',
            showlegend=False
        )

        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])

        fig.update_layout(
            title=title,
            showlegend=False,
            hovermode='closest',
            margin=dict(l=20, r=20, t=60, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=500,
            plot_bgcolor='rgba(240,240,240,0.5)'
        )

        return fig

    def get_top_correlated_pairs(
        self,
        corr_matrix: pd.DataFrame,
        n: int = 5
    ) -> List[Dict]:
        """
        Get top N most correlated investor pairs

        Returns:
            List of dicts with keys: investor_a, investor_b, correlation
        """
        pairs = []

        for i, name_a in enumerate(corr_matrix.index):
            for j, name_b in enumerate(corr_matrix.columns):
                if i < j:  # Only upper triangle
                    pairs.append({
                        'investor_a': name_a,
                        'investor_b': name_b,
                        'correlation': corr_matrix.loc[name_a, name_b]
                    })

        # Sort by correlation (descending)
        pairs = sorted(pairs, key=lambda x: x['correlation'], reverse=True)

        return pairs[:n]

    def get_correlation_interpretation(self, corr: float) -> str:
        """
        Get human-readable interpretation of correlation value

        Returns:
            String description
        """
        if corr >= 0.8:
            return "Çok Yüksek Benzerlik"
        elif corr >= 0.6:
            return "Yüksek Benzerlik"
        elif corr >= 0.4:
            return "Orta Benzerlik"
        elif corr >= 0.2:
            return "Düşük Benzerlik"
        else:
            return "Çok Düşük Benzerlik"

    def analyze_user_dna(
        self,
        user_df: pd.DataFrame,
        whale_data_dict: Dict[str, pd.DataFrame]
    ) -> Dict:
        """
        Comprehensive user DNA analysis

        Returns:
            Dict with top_match, similarity_breakdown, recommendations
        """
        # Compare to all whales
        comparison = self.compare_user_to_whales(user_df, whale_data_dict)

        if len(comparison) == 0:
            return {
                'top_match': None,
                'similarity_score': 0,
                'similarity_breakdown': comparison,
                'recommendations': []
            }

        # Top match
        top_match = comparison.iloc[0]

        # Recommendations based on similarity
        recommendations = []

        if top_match['Similarity_Score'] >= 70:
            recommendations.append(
                f"🎯 Yatırım tarzınız {top_match['Investor']}'a çok benziyor! "
                f"Bu yatırımcının son hareketlerini yakından takip edin."
            )
        elif top_match['Similarity_Score'] >= 50:
            recommendations.append(
                f"📊 {top_match['Investor']} ile benzer pozisyonlarınız var. "
                f"Diversifikasyon için diğer sektörlere bakabilirsiniz."
            )
        else:
            recommendations.append(
                f"🔍 Portföyünüz tüm balina yatırımcılardan farklı. "
                f"Benzersiz bir strateji izliyorsunuz!"
            )

        # Common holdings recommendation
        if top_match['Common_Holdings'] > 5:
            recommendations.append(
                f"🤝 {top_match['Investor']} ile {top_match['Common_Holdings']} "
                f"ortak hisseniz var. Consensus plays!"
            )

        return {
            'top_match': top_match['Investor'],
            'similarity_score': top_match['Similarity_Score'],
            'similarity_breakdown': comparison,
            'recommendations': recommendations
        }


def quick_correlation_analysis(
    whale_data_dict: Dict[str, pd.DataFrame],
    user_df: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Quick correlation analysis for all whales and optionally user

    Returns:
        Dict with corr_matrix, clusters, top_pairs, user_dna (if provided)
    """
    engine = WhaleCorrelationEngine()

    # Build correlation matrix
    corr_matrix = engine.build_correlation_matrix(whale_data_dict)

    # Identify clusters
    clusters = engine.identify_whale_clusters(corr_matrix, threshold=0.6)

    # Get top correlated pairs
    top_pairs = engine.get_top_correlated_pairs(corr_matrix, n=5)

    results = {
        'correlation_matrix': corr_matrix,
        'clusters': clusters,
        'top_pairs': top_pairs,
        'num_investors': len(whale_data_dict)
    }

    # User DNA analysis (if provided)
    if user_df is not None:
        user_dna = engine.analyze_user_dna(user_df, whale_data_dict)
        results['user_dna'] = user_dna

    return results

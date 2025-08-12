"""
High-level chart creation functions for the Streamlit interface.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Optional
from .plotting import (
    create_portfolio_performance_chart,
    create_asset_allocation_pie_chart,
    create_comparison_bar_chart,
    create_data_quality_plot,
    create_multi_asset_comparison,
    create_time_series_plot
)

def display_portfolio_performance(portfolio_df: pd.DataFrame, 
                                title: str = "Portfolio Performance"):
    """Display portfolio performance chart in Streamlit."""
    if portfolio_df.empty:
        st.warning("No portfolio performance data available")
        return
    
    fig = create_portfolio_performance_chart(portfolio_df, title)
    st.plotly_chart(fig, use_container_width=True)
    
    # Additional metrics
    if len(portfolio_df) > 1:
        col1, col2, col3 = st.columns(3)
        
        initial_value = portfolio_df['Value'].iloc[0]
        final_value = portfolio_df['Value'].iloc[-1]
        total_return = (final_value / initial_value - 1) * 100
        
        with col1:
            st.metric("Initial Value", f"${initial_value:,.2f}")
        with col2:
            st.metric("Final Value", f"${final_value:,.2f}")
        with col3:
            st.metric("Total Return", f"{total_return:.2f}%", 
                     delta=f"{total_return:.2f}%")

def display_asset_allocation(weights_dict: Dict[str, float], 
                           title: str = "Asset Allocation"):
    """Display asset allocation pie chart in Streamlit."""
    if not weights_dict:
        st.warning("No allocation data available")
        return
    
    fig = create_asset_allocation_pie_chart(weights_dict, title)
    st.plotly_chart(fig, use_container_width=True)

def display_portfolio_comparison(comparison_df: pd.DataFrame):
    """Display target vs current portfolio comparison."""
    if comparison_df.empty:
        st.warning("No comparison data available")
        return
    
    # Show the comparison table
    st.dataframe(comparison_df, use_container_width=True)
    
    # Show the comparison chart
    fig = create_comparison_bar_chart(comparison_df)
    st.plotly_chart(fig, use_container_width=True)

def display_backtest_summary(summary_df: pd.DataFrame):
    """Display backtest summary metrics in a clean format."""
    if summary_df.empty:
        st.warning("No backtest summary available")
        return
    
    # Convert to columns for better display
    metrics = {}
    for _, row in summary_df.iterrows():
        metrics[row['Metric']] = row['Value']
    
    # Create columns for metrics
    cols = st.columns(len(metrics))
    
    for i, (metric, value) in enumerate(metrics.items()):
        with cols[i]:
            # Extract numeric value for delta calculation if possible
            try:
                if "%" in value:
                    numeric_value = float(value.replace("%", "").replace(",", ""))
                    st.metric(metric, value, delta=f"{numeric_value:.2f}%" if "Return" in metric else None)
                elif "$" in value:
                    numeric_value = float(value.replace("$", "").replace(",", ""))
                    st.metric(metric, value)
                else:
                    st.metric(metric, value)
            except:
                st.metric(metric, value)

def display_data_explorer(data_dict: Dict[str, pd.DataFrame]):
    """Display interactive data explorer with multiple visualization options."""
    if not data_dict:
        st.warning("No data available")
        return
    
    st.subheader("Data Explorer")
    
    # Asset selection
    selected_assets = st.multiselect(
        "Select assets to visualize:",
        options=list(data_dict.keys()),
        default=list(data_dict.keys())[:3] if len(data_dict) >= 3 else list(data_dict.keys())
    )
    
    if not selected_assets:
        st.info("Please select at least one asset to visualize")
        return
    
    # Visualization type selection
    viz_type = st.selectbox(
        "Visualization type:",
        options=["Normalized Comparison (Start at 100)", "Individual Time Series", "Percentage Returns Comparison", "Data Quality Check"]
    )
    
    if viz_type == "Individual Time Series":
        for asset in selected_assets:
            if asset in data_dict and not data_dict[asset].empty:
                st.subheader(f"{asset} Time Series")
                df = data_dict[asset]
                
                # Determine date and value columns
                date_col = 'Date' if 'Date' in df.columns else df.columns[0]
                value_col = 'Value' if 'Value' in df.columns else df.columns[-1]
                
                fig = create_time_series_plot(df, date_col, value_col, f"{asset} Price History", "plotly")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Show data summary
                with st.expander(f"Data Summary - {asset}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Data Range:**")
                        st.write(f"From: {df[date_col].min()}")
                        st.write(f"To: {df[date_col].max()}")
                    with col2:
                        st.write("**Statistics:**")
                        st.write(f"Records: {len(df)}")
                        st.write(f"Missing: {df[value_col].isna().sum()}")
    
    elif viz_type == "Normalized Comparison (Start at 100)":
        filtered_data = {asset: data_dict[asset] for asset in selected_assets if asset in data_dict}
        fig = create_multi_asset_comparison(filtered_data, normalize_to_100=True)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            # Show summary statistics
            with st.expander("Performance Summary"):
                summary_data = []
                for asset in selected_assets:
                    if asset in data_dict and not data_dict[asset].empty:
                        df = data_dict[asset]
                        first_value = df['Value'].iloc[0]
                        last_value = df['Value'].iloc[-1]
                        total_return = (last_value / first_value - 1) * 100
                        
                        # Calculate volatility (annualized standard deviation of daily returns)
                        daily_returns = df['Value'].pct_change().dropna()
                        volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized
                        
                        summary_data.append({
                            "Asset": asset,
                            "Total Return": f"{total_return:.2f}%",
                            "Final Value": f"{last_value / first_value * 100:.2f}",
                            "Annualized Volatility": f"{volatility:.2f}%"
                        })
                
                if summary_data:
                    summary_df = pd.DataFrame(summary_data)
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    elif viz_type == "Percentage Returns Comparison":
        filtered_data = {asset: data_dict[asset] for asset in selected_assets if asset in data_dict}
        fig = create_multi_asset_comparison(filtered_data, normalize_to_100=False)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    elif viz_type == "Data Quality Check":
        for asset in selected_assets:
            if asset in data_dict and not data_dict[asset].empty:
                st.subheader(f"Data Quality - {asset}")
                df = data_dict[asset]
                
                date_col = 'Date' if 'Date' in df.columns else df.columns[0]
                value_col = 'Value' if 'Value' in df.columns else df.columns[-1]
                
                fig = create_data_quality_plot(df, date_col, value_col)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

def display_strategy_weights_table(weights_dict: Dict[str, float], 
                                 strategy_name: str = "Selected Strategy"):
    """Display strategy weights in a formatted table."""
    if not weights_dict:
        st.warning(f"No weights available for {strategy_name}")
        return
    
    # Convert to DataFrame for display
    weights_df = pd.DataFrame([
        {"Asset": asset, "Weight": f"{weight:.2%}"}
        for asset, weight in weights_dict.items()
    ])
    
    st.subheader(f"{strategy_name} - Asset Weights")
    st.dataframe(weights_df, use_container_width=True, hide_index=True)
    
    # Also show as pie chart
    display_asset_allocation(weights_dict, f"{strategy_name} Allocation")

def create_metrics_dashboard(backtest_results: Dict):
    """Create a comprehensive metrics dashboard."""
    if not backtest_results:
        st.warning("No backtest results available")
        return
    
    st.subheader("Performance Metrics Dashboard")
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Final Value",
            f"${backtest_results.get('final_value', 0):,.2f}",
            delta=f"{backtest_results.get('total_return', 0):.2f}%"
        )
    
    with col2:
        st.metric(
            "Annualized Return",
            f"{backtest_results.get('annualized_return', 0):.2f}%"
        )
    
    with col3:
        st.metric(
            "Max Drawdown",
            f"{backtest_results.get('max_drawdown', 0):.2f}%",
            delta=f"{backtest_results.get('max_drawdown', 0):.2f}%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Sharpe Ratio",
            f"{backtest_results.get('sharpe_ratio', 0):.3f}"
        )
    
    # Additional details in expandable section
    with st.expander("Detailed Metrics"):
        metrics_df = pd.DataFrame([
            {"Metric": k.replace("_", " ").title(), "Value": str(v)}
            for k, v in backtest_results.items()
            if k not in ['portfolio_dates', 'portfolio_values']
        ])
        st.dataframe(metrics_df, hide_index=True)
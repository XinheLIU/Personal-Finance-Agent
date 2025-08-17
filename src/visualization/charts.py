"""
High-level chart creation functions for the Streamlit interface.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Optional, Any
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

def display_data_explorer():
    """Display interactive data explorer with multiple visualization options."""
    # Load data for visualization inside function to ensure it's reactive to changes
    from src.streamlit_app import load_data_for_visualization
    data_dict = load_data_for_visualization()
    
    if not data_dict:
        st.warning("No data available")
        return
    
    st.subheader("Data Explorer")
    
    # Configuration section with three columns
    config_col1, config_col2, config_col3 = st.columns([1.2, 1, 1])
    
    with config_col1:
        # Asset selection
        selected_assets = st.multiselect(
            "Select assets to visualize:",
            options=list(data_dict.keys()),
            default=list(data_dict.keys())[:3] if len(data_dict) >= 3 else list(data_dict.keys())
        )
    
    with config_col2:
        # Visualization type selection
        viz_type = st.selectbox(
            "Visualization type:",
            options=["Normalized Comparison (Start at 100)", "Individual Time Series", "Percentage Returns Comparison", "Data Quality Check"]
        )
    
    with config_col3:
        # Start date selection for filtering data
        st.write("**Date Range Filter**")
        
        # Find the earliest and latest dates across all selected assets
        min_date, max_date = None, None
        if selected_assets:
            all_dates = []
            for asset in selected_assets:
                if asset in data_dict and not data_dict[asset].empty:
                    df = data_dict[asset]
                    date_col = 'Date' if 'Date' in df.columns else df.columns[0]
                    if pd.api.types.is_datetime64_any_dtype(df[date_col]):
                        all_dates.extend(df[date_col].tolist())
            
            if all_dates:
                min_date = min(all_dates).date() if hasattr(min(all_dates), 'date') else min(all_dates)
                max_date = max(all_dates).date() if hasattr(max(all_dates), 'date') else max(all_dates)
        
        # Default to last 3 years or available range
        from datetime import date, timedelta
        default_start = date.today() - timedelta(days=3*365)
        if min_date and default_start < min_date:
            default_start = min_date
        
        start_date = st.date_input(
            "Start Date:",
            value=default_start,
            min_value=min_date if min_date else date(2010, 1, 1),
            max_value=max_date if max_date else date.today(),
            help="Filter data from this date forward"
        )
    
    if not selected_assets:
        st.info("Please select at least one asset to visualize")
        return
    
    # Helper function to filter data by start date
    def filter_data_by_date(df: pd.DataFrame, start_date_filter) -> pd.DataFrame:
        """Filter dataframe by start date."""
        if df.empty:
            return df
        
        date_col = 'Date' if 'Date' in df.columns else df.columns[0]
        
        # Ensure the date column is datetime and timezone-naive
        if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
            try:
                df[date_col] = pd.to_datetime(df[date_col], utc=True).dt.tz_localize(None)
            except:
                try:
                    df[date_col] = pd.to_datetime(df[date_col])
                except:
                    return df  # Return original if conversion fails
        else:
            # If already datetime, ensure it's timezone-naive
            if df[date_col].dt.tz is not None:
                df[date_col] = df[date_col].dt.tz_localize(None)
        
        # Convert start_date to timezone-naive datetime for comparison
        start_datetime = pd.to_datetime(start_date_filter)
        if start_datetime.tz is not None:
            start_datetime = start_datetime.tz_localize(None)
        
        # Filter data
        filtered_df = df[df[date_col] >= start_datetime].copy()
        return filtered_df
    
    # Apply date filtering to selected assets
    filtered_data_dict = {}
    for asset in selected_assets:
        if asset in data_dict and not data_dict[asset].empty:
            filtered_data_dict[asset] = filter_data_by_date(data_dict[asset], start_date)
    
    if viz_type == "Individual Time Series":
        for asset in selected_assets:
            if asset in filtered_data_dict and not filtered_data_dict[asset].empty:
                st.subheader(f"{asset} Time Series (from {start_date})")
                df = filtered_data_dict[asset]
                
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
                        st.write("**Filtered Data Range:**")
                        st.write(f"From: {df[date_col].min()}")
                        st.write(f"To: {df[date_col].max()}")
                    with col2:
                        st.write("**Statistics:**")
                        st.write(f"Records: {len(df)}")
                        st.write(f"Missing: {df[value_col].isna().sum()}")
            elif asset in selected_assets:
                st.warning(f"No data available for {asset} from {start_date}")
    
    elif viz_type == "Normalized Comparison (Start at 100)":
        if filtered_data_dict:
            fig = create_multi_asset_comparison(filtered_data_dict, normalize_to_100=True)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                # Show summary statistics
                with st.expander("Performance Summary"):
                    summary_data = []
                    for asset in selected_assets:
                        if asset in filtered_data_dict and not filtered_data_dict[asset].empty:
                            df = filtered_data_dict[asset]
                            if len(df) > 1:  # Need at least 2 data points
                                first_value = df['Value'].iloc[0]
                                last_value = df['Value'].iloc[-1]
                                total_return = (last_value / first_value - 1) * 100
                                
                                # Calculate volatility (annualized standard deviation of daily returns)
                                daily_returns = df['Value'].pct_change().dropna()
                                volatility = daily_returns.std() * np.sqrt(252) * 100 if len(daily_returns) > 1 else 0
                                
                                summary_data.append({
                                    "Asset": asset,
                                    "Total Return": f"{total_return:.2f}%",
                                    "Final Value": f"{last_value / first_value * 100:.2f}",
                                    "Annualized Volatility": f"{volatility:.2f}%",
                                    "Data Points": len(df)
                                })
                    
                    if summary_data:
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True, hide_index=True)
                        
                        # Show the date range information
                        st.info(f"📅 Analysis period: from {start_date} to latest available data")
        else:
            st.warning("No data available for the selected assets and date range")
    
    elif viz_type == "Percentage Returns Comparison":
        if filtered_data_dict:
            fig = create_multi_asset_comparison(filtered_data_dict, normalize_to_100=False)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                st.info(f"📅 Analysis period: from {start_date} to latest available data")
        else:
            st.warning("No data available for the selected assets and date range")
    
    elif viz_type == "Data Quality Check":
        for asset in selected_assets:
            if asset in filtered_data_dict and not filtered_data_dict[asset].empty:
                st.subheader(f"Data Quality - {asset} (from {start_date})")
                df = filtered_data_dict[asset]
                
                date_col = 'Date' if 'Date' in df.columns else df.columns[0]
                value_col = 'Value' if 'Value' in df.columns else df.columns[-1]
                
                fig = create_data_quality_plot(df, date_col, value_col)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            elif asset in selected_assets:
                st.warning(f"No data available for {asset} from {start_date}")

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

def display_attribution_analysis(attribution_data: Dict, strategy_name: str):
    """Display performance attribution analysis with interactive visualizations."""
    if not attribution_data or 'error' in attribution_data:
        st.error(f"Attribution analysis failed: {attribution_data.get('error', 'Unknown error')}")
        return
    
    st.subheader("📊 Performance Attribution Analysis")
    
    # Attribution period selection
    available_periods = []
    if 'daily_analysis' in attribution_data:
        available_periods.append('Daily')
    if 'weekly_analysis' in attribution_data:
        available_periods.append('Weekly')
    if 'monthly_analysis' in attribution_data:
        available_periods.append('Monthly')
    
    if not available_periods:
        st.warning("No attribution periods available for analysis")
        return
    
    # Let user select attribution period
    selected_period = st.selectbox(
        "Select Attribution Period:",
        options=available_periods,
        help="Choose the time period for attribution analysis"
    )
    
    period_key = f"{selected_period.lower()}_analysis"
    if period_key not in attribution_data:
        st.error(f"No {selected_period.lower()} attribution data available")
        return
    
    period_data = attribution_data[period_key]
    
    # Summary Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    summary_stats = period_data.get('summary_statistics', {})
    
    with col1:
        st.metric(
            "Total Portfolio Return", 
            f"{float(summary_stats.get('total_portfolio_return', 0)):.1%}"
        )
    
    with col2:
        st.metric(
            "Total Asset Contribution", 
            f"{float(summary_stats.get('total_asset_contribution', 0)):.1%}"
        )
    
    with col3:
        st.metric(
            "Total Rebalancing Impact", 
            f"{float(summary_stats.get('total_rebalancing_impact', 0)):.1%}"
        )
    
    with col4:
        st.metric(
            "Attribution Accuracy", 
            f"{float(summary_stats.get('attribution_accuracy', 0)):.2%}",
            help="Lower is better - measures attribution reconciliation quality"
        )
    
    # Create two columns for charts
    chart_col1, chart_col2 = st.columns(2)
    
    # Top Contributors Chart
    with chart_col1:
        st.subheader("Top Contributors")
        top_contributors = period_data.get('top_contributors', {})
        
        if top_contributors:
            contrib_data = []
            for asset, data in top_contributors.items():
                contrib_data.append({
                    'Asset': str(asset),
                    'Net Impact': float(data.get('net_impact', 0)),
                    'Asset Contribution': float(data.get('total_contribution', 0)),
                    'Rebalancing Impact': float(data.get('total_rebalancing_impact', 0))
                })
            
            contrib_df = pd.DataFrame(contrib_data)
            
            # Create stacked bar chart
            fig = go.Figure(data=[
                go.Bar(
                    name='Asset Contribution',
                    x=contrib_df['Asset'],
                    y=contrib_df['Asset Contribution'],
                    marker_color='lightblue'
                ),
                go.Bar(
                    name='Rebalancing Impact',
                    x=contrib_df['Asset'],
                    y=contrib_df['Rebalancing Impact'],
                    marker_color='orange'
                )
            ])
            
            fig.update_layout(
                title=f"{selected_period} Attribution Breakdown",
                xaxis_title="Assets",
                yaxis_title="Contribution",
                barmode='stack',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No contribution data available")
    
    # Asset Analysis Table
    with chart_col2:
        st.subheader("Asset-Level Analysis")
        asset_analysis = period_data.get('asset_analysis', {})
        
        if asset_analysis:
            analysis_data = []
            for asset, data in asset_analysis.items():
                # Convert numpy types to native Python types to fix Arrow serialization
                total_contrib = float(data.get('total_contribution', 0))
                avg_contrib = float(data.get('average_contribution', 0))
                rebal_impact = float(data.get('total_rebalancing_impact', 0))
                net_impact = float(data.get('net_impact', 0))
                
                analysis_data.append({
                    'Asset': str(asset),  # Ensure asset name is string
                    'Total Contribution': f"{total_contrib:.3%}",
                    'Avg Contribution': f"{avg_contrib:.3%}",
                    'Rebalancing Impact': f"{rebal_impact:.3%}",
                    'Net Impact': f"{net_impact:.3%}"
                })
            
            analysis_df = pd.DataFrame(analysis_data)
            st.dataframe(analysis_df, use_container_width=True, hide_index=True)
        else:
            st.info("No asset analysis data available")
    
    # Detailed Attribution Time Series
    st.subheader("Attribution Time Series")
    attribution_records = period_data.get('attribution_data', [])
    
    if attribution_records:
        ts_df = pd.DataFrame(attribution_records)
        ts_df['date'] = pd.to_datetime(ts_df['date'])
        
        # Create time series chart of total returns vs attribution components
        fig = go.Figure()
        
        if 'total_return' in ts_df.columns:
            fig.add_trace(go.Scatter(
                x=ts_df['date'],
                y=ts_df['total_return'],
                mode='lines',
                name='Total Return',
                line=dict(color='blue', width=2)
            ))
        
        if 'weight_change_impact' in ts_df.columns:
            fig.add_trace(go.Scatter(
                x=ts_df['date'],
                y=ts_df['weight_change_impact'],
                mode='lines',
                name='Rebalancing Impact',
                line=dict(color='orange', width=1)
            ))
        
        fig.update_layout(
            title=f"{selected_period} Attribution Time Series",
            xaxis_title="Date",
            yaxis_title="Return",
            height=400,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Export options
        st.subheader("📥 Export Attribution Data")
        
        col1, col2 = st.columns(2)
        with col1:
            csv_data = ts_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"{strategy_name}_{selected_period}_attribution.csv",
                mime="text/csv"
            )
        
        with col2:
            if st.button("View Raw Data", key=f"raw_data_{selected_period}"):
                with st.expander("Raw Attribution Data", expanded=True):
                    st.dataframe(ts_df, use_container_width=True)
    
    else:
        st.info("No detailed attribution time series data available")

def create_sector_attribution_table(sector_summary: Dict[str, Any]) -> pd.DataFrame:
    """Create a professional sector attribution table similar to institutional reports."""
    if not sector_summary:
        return pd.DataFrame()
    
    table_data = []
    for sector, data in sector_summary.items():
        # Format data similar to the provided image
        table_data.append({
            'Sector': sector,
            'Portfolio Weight': data.get('portfolio_weight', 0),
            'Index Weight': data.get('benchmark_weight', 0),  
            'Portfolio ROR': data.get('portfolio_return', 0),
            'Index ROR': data.get('benchmark_return', 0),
            'Allocation': data.get('allocation_effect', 0),
            'Selection': data.get('selection_effect', 0),
            'Interaction': data.get('interaction_effect', 0)
        })
    
    df = pd.DataFrame(table_data)
    
    # Format as percentages
    percentage_cols = ['Portfolio Weight', 'Index Weight', 'Portfolio ROR', 'Index ROR', 
                      'Allocation', 'Selection', 'Interaction']
    for col in percentage_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.2%}")
    
    return df


def create_attribution_waterfall_chart(attribution_effects: Dict[str, float]) -> go.Figure:
    """Create a waterfall chart showing attribution effects."""
    categories = list(attribution_effects.keys())
    values = list(attribution_effects.values())
    
    # Calculate cumulative values for waterfall
    cumulative = [0]
    for value in values[:-1]:  # Exclude the last value (total)
        cumulative.append(cumulative[-1] + value)
    
    # Create waterfall chart
    fig = go.Figure()
    
    # Add bars for each effect
    colors = ['lightblue' if v >= 0 else 'lightcoral' for v in values]
    
    fig.add_trace(go.Waterfall(
        name="Attribution Effects",
        orientation="v",
        measure=["relative"] * (len(values) - 1) + ["total"],
        x=categories,
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "lightcoral"}},
        increasing={"marker": {"color": "lightblue"}},
        totals={"marker": {"color": "lightgreen"}}
    ))
    
    fig.update_layout(
        title="Performance Attribution Waterfall",
        xaxis_title="Attribution Components",
        yaxis_title="Return Contribution",
        showlegend=False,
        height=400
    )
    
    return fig


def create_sector_allocation_comparison(portfolio_weights: Dict[str, float], 
                                      benchmark_weights: Dict[str, float]) -> go.Figure:
    """Create a comparison chart of portfolio vs benchmark sector allocations."""
    sectors = list(set(portfolio_weights.keys()) | set(benchmark_weights.keys()))
    
    portfolio_vals = [portfolio_weights.get(sector, 0) for sector in sectors]
    benchmark_vals = [benchmark_weights.get(sector, 0) for sector in sectors]
    
    fig = go.Figure(data=[
        go.Bar(name='Portfolio', x=sectors, y=portfolio_vals, marker_color='lightblue'),
        go.Bar(name='Benchmark', x=sectors, y=benchmark_vals, marker_color='orange')
    ])
    
    fig.update_layout(
        title="Sector Allocation: Portfolio vs Benchmark",
        xaxis_title="Sectors",
        yaxis_title="Weight",
        barmode='group',
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    return fig


def create_attribution_time_series(attribution_data: List[Dict]) -> go.Figure:
    """Create time series chart of attribution effects over time."""
    if not attribution_data:
        return go.Figure()
    
    df = pd.DataFrame(attribution_data)
    df['date'] = pd.to_datetime(df['date'])
    
    fig = go.Figure()
    
    # Add traces for different attribution effects
    if 'allocation_effect' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['allocation_effect'],
            mode='lines',
            name='Allocation Effect',
            line=dict(color='lightblue', width=2)
        ))
    
    if 'selection_effect' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['selection_effect'],
            mode='lines',
            name='Selection Effect',
            line=dict(color='orange', width=2)
        ))
    
    if 'interaction_effect' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['interaction_effect'],
            mode='lines',
            name='Interaction Effect',
            line=dict(color='lightgreen', width=2)
        ))
    
    if 'total_effect' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['total_effect'],
            mode='lines',
            name='Total Effect',
            line=dict(color='red', width=3)
        ))
    
    fig.update_layout(
        title="Attribution Effects Over Time",
        xaxis_title="Date",
        yaxis_title="Attribution Effect",
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    return fig


def display_sector_attribution_dashboard(attribution_summary: Dict[str, Any], 
                                       attribution_results: List,
                                       strategy_name: str):
    """Display a comprehensive sector attribution dashboard."""
    st.subheader(f"🎯 Sector Attribution Dashboard - {strategy_name}")
    
    if not attribution_summary or 'error' in attribution_summary:
        st.error(f"Attribution analysis failed: {attribution_summary.get('error', 'Unknown error')}")
        return
    
    # Summary metrics
    total_effects = attribution_summary.get('total_effects', {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🎯 Total Excess Return",
            f"{total_effects.get('total_excess_return', 0):.2%}",
            help="Total portfolio outperformance vs benchmark"
        )
    
    with col2:
        st.metric(
            "⚖️ Allocation Effect",
            f"{total_effects.get('total_allocation_effect', 0):.2%}",
            help="Impact of sector over/under-weighting decisions"
        )
    
    with col3:
        st.metric(
            "🎪 Selection Effect",
            f"{total_effects.get('total_selection_effect', 0):.2%}",
            help="Impact of asset selection within sectors"
        )
    
    with col4:
        st.metric(
            "🔗 Interaction Effect",
            f"{total_effects.get('total_interaction_effect', 0):.2%}",
            help="Combined allocation and selection interaction"
        )
    
    # Professional attribution table (styled like institutional reports)
    st.subheader("📋 Sector Attribution Analysis")
    
    sector_summary = attribution_summary.get('sector_summary', {})
    if sector_summary:
        attribution_table = create_sector_attribution_table(sector_summary)
        
        # Style the table to look professional
        styled_table = attribution_table.style.format({
            'Portfolio Weight': '{:.1%}',
            'Index Weight': '{:.1%}',
            'Portfolio ROR': '{:.2%}',
            'Index ROR': '{:.2%}',
            'Allocation': '{:.3%}',
            'Selection': '{:.3%}',
            'Interaction': '{:.3%}'
        }).background_gradient(subset=['Allocation', 'Selection', 'Interaction'], cmap='RdYlGn', center=0)
        
        st.dataframe(styled_table, use_container_width=True)
    
    # Visualization section
    st.subheader("📊 Attribution Visualizations")
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Attribution waterfall chart
        if total_effects:
            waterfall_data = {
                'Allocation Effect': total_effects.get('total_allocation_effect', 0),
                'Selection Effect': total_effects.get('total_selection_effect', 0),
                'Interaction Effect': total_effects.get('total_interaction_effect', 0),
                'Total Excess Return': total_effects.get('total_excess_return', 0)
            }
            
            waterfall_fig = create_attribution_waterfall_chart(waterfall_data)
            st.plotly_chart(waterfall_fig, use_container_width=True)
    
    with chart_col2:
        # Top contributors chart
        top_contributors = attribution_summary.get('top_contributors', {})
        if top_contributors:
            sectors = list(top_contributors.keys())
            effects = list(top_contributors.values())
            
            fig = go.Figure(go.Bar(
                x=effects,
                y=sectors,
                orientation='h',
                marker_color=['green' if x >= 0 else 'red' for x in effects],
                text=[f"{x:.2%}" for x in effects],
                textposition='auto'
            ))
            
            fig.update_layout(
                title="🏆 Top Contributing Sectors",
                xaxis_title="Total Attribution Effect",
                yaxis_title="Sectors",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Time series analysis
    st.subheader("📈 Attribution Trends Over Time")
    
    attribution_data = attribution_summary.get('attribution_data', [])
    if attribution_data:
        # Group by sector for time series
        df = pd.DataFrame(attribution_data)
        
        if not df.empty and 'sector' in df.columns:
            selected_sectors = st.multiselect(
                "Select sectors to display:",
                options=df['sector'].unique(),
                default=df['sector'].unique()[:3],  # Default to first 3 sectors
                help="Choose which sectors to show in the time series chart"
            )
            
            if selected_sectors:
                filtered_df = df[df['sector'].isin(selected_sectors)]
                
                # Create individual time series for each sector
                fig = go.Figure()
                
                from config.sectors import get_sector_color
                
                for sector in selected_sectors:
                    sector_data = filtered_df[filtered_df['sector'] == sector]
                    sector_data = sector_data.sort_values('date')
                    
                    fig.add_trace(go.Scatter(
                        x=pd.to_datetime(sector_data['date']),
                        y=sector_data['total_effect'],
                        mode='lines+markers',
                        name=sector,
                        line=dict(color=get_sector_color(sector), width=2),
                        hovertemplate=f'<b>{sector}</b><br>Date: %{{x}}<br>Attribution: %{{y:.3%}}<extra></extra>'
                    ))
                
                fig.update_layout(
                    title="Sector Attribution Effects Over Time",
                    xaxis_title="Date",
                    yaxis_title="Attribution Effect",
                    height=400,
                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Export and download section
    st.subheader("💾 Export Attribution Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if sector_summary:
            # Prepare CSV data
            csv_data = create_sector_attribution_table(sector_summary).to_csv(index=False)
            st.download_button(
                label="📄 Download Attribution Table (CSV)",
                data=csv_data,
                file_name=f"{strategy_name}_sector_attribution.csv",
                mime="text/csv"
            )
    
    with col2:
        if attribution_summary:
            # Prepare JSON summary
            import json
            json_data = json.dumps(attribution_summary, indent=2, default=str)
            st.download_button(
                label="📋 Download Summary (JSON)",
                data=json_data,
                file_name=f"{strategy_name}_attribution_summary.json",
                mime="application/json"
            )
    
    with col3:
        # Option to view raw data
        if st.button("👁️ View Raw Attribution Data"):
            with st.expander("Raw Attribution Data", expanded=True):
                if attribution_results:
                    raw_data = []
                    for result in attribution_results[:100]:  # Limit display to first 100 records
                        raw_data.append({
                            'Date': result.date.strftime('%Y-%m-%d'),
                            'Sector': result.sector,
                            'Portfolio Weight': f"{result.portfolio_weight:.3%}",
                            'Benchmark Weight': f"{result.benchmark_weight:.3%}",
                            'Allocation Effect': f"{result.allocation_effect:.4%}",
                            'Selection Effect': f"{result.selection_effect:.4%}",
                            'Interaction Effect': f"{result.interaction_effect:.4%}",
                            'Total Effect': f"{result.total_effect:.4%}"
                        })
                    
                    raw_df = pd.DataFrame(raw_data)
                    st.dataframe(raw_df, use_container_width=True, height=400)


def create_attribution_summary_chart(attribution_data: Dict) -> go.Figure:
    """Create a summary chart comparing attribution across different periods."""
    periods = []
    total_returns = []
    asset_contributions = []
    rebalancing_impacts = []
    
    for period_name, period_data in attribution_data.items():
        if period_name.endswith('_analysis') and isinstance(period_data, dict):
            summary_stats = period_data.get('summary_statistics', {})
            periods.append(period_name.replace('_analysis', '').title())
            total_returns.append(summary_stats.get('total_portfolio_return', 0))
            asset_contributions.append(summary_stats.get('total_asset_contribution', 0))
            rebalancing_impacts.append(summary_stats.get('total_rebalancing_impact', 0))
    
    if not periods:
        return go.Figure()
    
    fig = go.Figure(data=[
        go.Bar(
            name='Asset Contribution',
            x=periods,
            y=asset_contributions,
            marker_color='lightblue'
        ),
        go.Bar(
            name='Rebalancing Impact',
            x=periods,
            y=rebalancing_impacts,
            marker_color='orange'
        )
    ])
    
    fig.update_layout(
        title="Attribution Summary Across Periods",
        xaxis_title="Period",
        yaxis_title="Contribution",
        barmode='stack',
        height=400
    )
    
    return fig

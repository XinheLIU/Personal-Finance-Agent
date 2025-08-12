"""
Core plotting utilities for data visualization.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from bokeh.plotting import figure
from bokeh.models import HoverTool
import streamlit as st
from typing import Dict, List, Optional, Union
import numpy as np

# Set consistent style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def create_time_series_plot(df: pd.DataFrame, 
                          x_col: str = 'Date', 
                          y_col: str = 'Value', 
                          title: str = "Time Series",
                          plot_type: str = "matplotlib") -> Union[plt.Figure, go.Figure]:
    """
    Create a time series plot using different backends.
    
    Args:
        df: DataFrame with time series data
        x_col: Column name for x-axis (dates)
        y_col: Column name for y-axis (values)
        title: Plot title
        plot_type: 'matplotlib', 'plotly', or 'bokeh'
    
    Returns:
        Plot figure object
    """
    if df.empty:
        st.warning("No data available for plotting")
        return None
        
    if plot_type == "matplotlib":
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(pd.to_datetime(df[x_col]), df[y_col], linewidth=2)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
        
    elif plot_type == "plotly":
        fig = px.line(df, x=x_col, y=y_col, title=title)
        fig.update_layout(
            xaxis_title=x_col,
            yaxis_title=y_col,
            hovermode='x unified'
        )
        return fig
        
    elif plot_type == "bokeh":
        p = figure(title=title, x_axis_type='datetime', 
                  width=800, height=400)
        p.line(pd.to_datetime(df[x_col]), df[y_col], line_width=2)
        hover = HoverTool(tooltips=[('Date', '@x{%F}'), ('Value', '@y{0.2f}')],
                         formatters={'@x': 'datetime'})
        p.add_tools(hover)
        return p

def create_portfolio_performance_chart(portfolio_df: pd.DataFrame, 
                                     title: str = "Portfolio Performance") -> go.Figure:
    """Create an interactive portfolio performance chart with Plotly."""
    if portfolio_df.empty:
        st.warning("No portfolio data available")
        return go.Figure()
    
    fig = go.Figure()
    
    # Main portfolio line
    fig.add_trace(go.Scatter(
        x=portfolio_df['Date'],
        y=portfolio_df['Value'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#2E86AB', width=3),
        hovertemplate='<b>Date</b>: %{x}<br><b>Value</b>: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add peak markers for drawdown visualization
    if len(portfolio_df) > 1:
        portfolio_df['Peak'] = portfolio_df['Value'].expanding().max()
        peak_mask = portfolio_df['Value'] == portfolio_df['Peak']
        
        fig.add_trace(go.Scatter(
            x=portfolio_df[peak_mask]['Date'],
            y=portfolio_df[peak_mask]['Value'],
            mode='markers',
            name='New Peaks',
            marker=dict(color='green', size=6),
            hovertemplate='<b>New Peak</b><br><b>Date</b>: %{x}<br><b>Value</b>: $%{y:,.2f}<extra></extra>'
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        height=500,
        template="plotly_white"
    )
    
    return fig

def create_asset_allocation_pie_chart(weights_dict: Dict[str, float], 
                                    title: str = "Asset Allocation") -> go.Figure:
    """Create a pie chart for asset allocation."""
    if not weights_dict:
        return go.Figure()
    
    assets = list(weights_dict.keys())
    weights = [w * 100 for w in weights_dict.values()]  # Convert to percentages
    
    fig = go.Figure(data=[go.Pie(
        labels=assets,
        values=weights,
        hole=0.3,
        textinfo='label+percent',
        textfont_size=12,
        hovertemplate='<b>%{label}</b><br>Weight: %{value:.1f}%<extra></extra>'
    )])
    
    fig.update_layout(
        title=title,
        height=500,
        template="plotly_white"
    )
    
    return fig

def create_comparison_bar_chart(comparison_df: pd.DataFrame) -> go.Figure:
    """Create a bar chart comparing target vs current weights."""
    if comparison_df.empty:
        return go.Figure()
    
    # Extract numeric values from percentage strings
    target_values = []
    current_values = []
    assets = []
    
    for _, row in comparison_df.iterrows():
        try:
            target = float(row['Target Weight'].replace('%', ''))
            current = float(row['Current Weight'].replace('%', ''))
            target_values.append(target)
            current_values.append(current)
            assets.append(row['Asset'])
        except (ValueError, KeyError):
            continue
    
    if not assets:
        return go.Figure()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Target Weight',
        x=assets,
        y=target_values,
        marker_color='#2E86AB',
        hovertemplate='<b>%{x}</b><br>Target: %{y:.1f}%<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        name='Current Weight',
        x=assets,
        y=current_values,
        marker_color='#A23B72',
        hovertemplate='<b>%{x}</b><br>Current: %{y:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title="Target vs Current Allocation",
        xaxis_title="Assets",
        yaxis_title="Weight (%)",
        barmode='group',
        height=500,
        template="plotly_white"
    )
    
    return fig

def create_data_quality_plot(df: pd.DataFrame, 
                           date_col: str = 'Date', 
                           value_col: str = 'Value') -> go.Figure:
    """Create a data quality visualization showing missing data and trends."""
    if df.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Main data line
    fig.add_trace(go.Scatter(
        x=df[date_col],
        y=df[value_col],
        mode='lines',
        name='Data',
        line=dict(color='#2E86AB', width=2),
        hovertemplate='<b>Date</b>: %{x}<br><b>Value</b>: %{y:.4f}<extra></extra>'
    ))
    
    # Identify and mark missing data points
    df_sorted = df.sort_values(date_col)
    date_range = pd.date_range(start=df_sorted[date_col].min(), 
                              end=df_sorted[date_col].max(), 
                              freq='D')
    missing_dates = set(date_range) - set(df_sorted[date_col])
    
    if missing_dates:
        # Add markers for missing data (approximate positions)
        missing_sample = sorted(list(missing_dates))[:10]  # Show up to 10 missing points
        fig.add_trace(go.Scatter(
            x=missing_sample,
            y=[np.nan] * len(missing_sample),
            mode='markers',
            name='Missing Data',
            marker=dict(color='red', size=8, symbol='x'),
            hovertemplate='<b>Missing Data</b><br><b>Date</b>: %{x}<extra></extra>'
        ))
    
    fig.update_layout(
        title="Data Quality Overview",
        xaxis_title="Date",
        yaxis_title="Value",
        hovermode='x unified',
        height=400,
        template="plotly_white"
    )
    
    return fig

def create_multi_asset_comparison(data_dict: Dict[str, pd.DataFrame],
                                date_col: str = 'Date',
                                value_col: str = 'Value',
                                normalize_to_100: bool = True) -> go.Figure:
    """Create a comparison chart for multiple assets."""
    if not data_dict:
        return go.Figure()
    
    fig = go.Figure()
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#8B1538', '#5D737E', 
              '#00B4D8', '#90E0EF', '#F72585', '#B5179E', '#7209B7', '#480CA8']
    
    for i, (asset_name, df) in enumerate(data_dict.items()):
        if df.empty:
            continue
            
        if len(df) > 0:
            if normalize_to_100:
                # Normalize values to start at 100 (rebased index)
                first_value = df[value_col].iloc[0]
                normalized_values = (df[value_col] / first_value) * 100
                y_title = "Normalized Value (Base=100)"
                hover_template = f'<b>{asset_name}</b><br><b>Date</b>: %{{x}}<br><b>Value</b>: %{{y:.2f}}<extra></extra>'
            else:
                # Show percentage returns
                first_value = df[value_col].iloc[0]
                normalized_values = ((df[value_col] / first_value) - 1) * 100
                y_title = "Cumulative Return (%)"
                hover_template = f'<b>{asset_name}</b><br><b>Date</b>: %{{x}}<br><b>Return</b>: %{{y:.2f}}%<extra></extra>'
            
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=normalized_values,
                mode='lines',
                name=asset_name,
                line=dict(color=colors[i % len(colors)], width=2),
                hovertemplate=hover_template
            ))
    
    title = "Multi-Asset Comparison (All Start at 100)" if normalize_to_100 else "Multi-Asset Performance Comparison"
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_title,
        hovermode='x unified',
        height=500,
        template="plotly_white",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )
    
    return fig
"""
Analytics Transparency Module
Provides detailed, step-by-step transparency for portfolio calculations, PE data analysis,
and investment decision-making processes.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

from src.ui.app_logger import LOG
from src.modules.portfolio.strategies.utils import calculate_pe_percentile, calculate_yield_percentile, get_current_yield
from src.modules.data_management.data_center.data_loader import DataLoader, load_market_data, load_pe_data
from config.assets import ASSETS, PE_ASSETS, YIELD_ASSETS


class TransparencyAnalyzer:
    """
    Main class for generating detailed transparency analysis of portfolio calculations
    """
    
    def __init__(self, output_dir: str = "analytics/transparency"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data loaders
        self.data_loader = DataLoader()
        self.market_data = None
        self.pe_data = None
        
        # Storage for analysis results
        self.analysis_results = {}
        
    def load_data(self):
        """Load market data and PE data for analysis"""
        try:
            self.market_data = load_market_data()
            self.pe_data = load_pe_data()
            LOG.info("Market data and PE data loaded successfully")
        except Exception as e:
            LOG.error(f"Error loading data: {e}")
            raise
    
    def analyze_pe_data_transparency(self, 
                                   current_date: Optional[str] = None,
                                   years_back: int = 10) -> Dict[str, Any]:
        """
        Detailed analysis of PE data processing and percentile calculations
        
        Args:
            current_date: Analysis date (defaults to latest available)
            years_back: Years of historical data to analyze
            
        Returns:
            Comprehensive PE analysis results
        """
        if self.pe_data is None:
            self.load_data()
            
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
        analysis_date = pd.to_datetime(current_date)
        LOG.info(f"Starting PE data transparency analysis for {analysis_date.date()}")
        
        pe_analysis = {
            'analysis_date': current_date,
            'years_back': years_back,
            'assets': {}
        }
        
        # Analyze each asset's PE data
        for asset_name in PE_ASSETS.keys():
            if asset_name not in self.pe_data or self.pe_data[asset_name].empty:
                LOG.warning(f"No PE data available for {asset_name}")
                continue
                
            asset_analysis = self._analyze_asset_pe_data(
                asset_name, 
                self.pe_data[asset_name], 
                analysis_date, 
                years_back
            )
            pe_analysis['assets'][asset_name] = asset_analysis
            
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"pe_analysis_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            # Convert numpy types to JSON serializable
            json_data = self._serialize_for_json(pe_analysis)
            json.dump(json_data, f, indent=2)
            
        LOG.info(f"PE transparency analysis saved to {output_file}")
        self.analysis_results['pe_analysis'] = pe_analysis
        return pe_analysis
    
    def analyze_weight_calculation_transparency(self,
                                              strategy_name: str = "Dynamic Allocation",
                                              current_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Detailed breakdown of target weight calculations
        
        Args:
            strategy_name: Name of strategy to analyze
            current_date: Calculation date (defaults to latest available)
            
        Returns:
            Comprehensive weight calculation breakdown
        """
        if self.market_data is None or self.pe_data is None:
            self.load_data()
            
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
            
        analysis_date = pd.to_datetime(current_date)
        LOG.info(f"Starting weight calculation transparency analysis for {strategy_name} on {analysis_date.date()}")
        
        weight_analysis = {
            'strategy_name': strategy_name,
            'analysis_date': current_date,
            'calculation_steps': {},
            'final_weights': {},
            'intermediate_values': {}
        }
        
        try:
            # Step 1: PE Percentile Calculations
            LOG.info("Step 1: Calculating PE percentiles...")
            pe_percentiles = {}
            pe_details = {}
            
            for asset in ['CSI300', 'CSI500', 'HSI', 'HSTECH', 'SP500', 'NASDAQ100']:
                if asset in PE_ASSETS:
                    years_back = 20 if asset in ['SP500', 'NASDAQ100'] else 10
                    
                    try:
                        percentile = calculate_pe_percentile(asset, self.pe_data, current_date, years_back)
                        pe_percentiles[asset] = percentile
                        
                        # Get detailed breakdown
                        pe_details[asset] = self._get_pe_calculation_details(
                            asset, self.pe_data[asset], analysis_date, years_back
                        )
                        
                        LOG.info(f"  {asset}: PE percentile = {percentile:.1%}")
                        
                    except Exception as e:
                        LOG.warning(f"  {asset}: Failed to calculate PE percentile - {e}")
                        pe_percentiles[asset] = 0.5  # Default to median
                        
            weight_analysis['calculation_steps']['pe_percentiles'] = pe_percentiles
            weight_analysis['intermediate_values']['pe_details'] = pe_details
            
            # Step 2: Yield Analysis
            LOG.info("Step 2: Calculating yield percentile...")
            try:
                yield_percentile = calculate_yield_percentile(self.market_data, current_date, 20)
                current_yield = get_current_yield(self.market_data, current_date)
                
                weight_analysis['calculation_steps']['yield_percentile'] = yield_percentile
                weight_analysis['calculation_steps']['current_yield'] = current_yield
                
                LOG.info(f"  Yield percentile: {yield_percentile:.1%}, Current yield: {current_yield:.2f}%")
                
            except Exception as e:
                LOG.warning(f"  Yield analysis failed: {e}")
                yield_percentile = 0.5
                current_yield = 4.0
                
            # Step 3: Raw Weight Calculations
            LOG.info("Step 3: Calculating raw target weights...")
            raw_weights = {}
            
            # Equity weights based on PE percentiles
            raw_weights['CSI300'] = 0.15 * (1 - pe_percentiles.get('CSI300', 0.5))
            raw_weights['CSI500'] = 0.15 * (1 - pe_percentiles.get('CSI500', 0.5))
            raw_weights['HSI'] = 0.10 * (1 - pe_percentiles.get('HSI', 0.5))
            raw_weights['HSTECH'] = 0.10 * (1 - pe_percentiles.get('HSTECH', 0.5))
            raw_weights['SP500'] = 0.15 * (1 - pe_percentiles.get('SP500', 0.5))
            raw_weights['NASDAQ100'] = 0.15 * (1 - pe_percentiles.get('NASDAQ100', 0.5))
            
            # Bond weight based on yield
            raw_weights['TLT'] = 0.15 * (yield_percentile ** 2)
            
            # Cash allocation based on yield threshold
            if current_yield >= 4.0:
                raw_weights['CASH'] = current_yield / 100.0
            else:
                raw_weights['CASH'] = 0.0
                
            # Fixed gold allocation
            raw_weights['GLD'] = 0.10
            
            weight_analysis['calculation_steps']['raw_weights'] = raw_weights
            
            # Step 4: Weight Normalization
            LOG.info("Step 4: Normalizing weights...")
            total_weight = sum(raw_weights.values())
            scale_factor = 1.0 / total_weight if total_weight > 0 else 1.0
            
            normalized_weights = {}
            for asset, weight in raw_weights.items():
                normalized_weights[asset] = weight * scale_factor
                
            weight_analysis['calculation_steps']['total_raw_weight'] = total_weight
            weight_analysis['calculation_steps']['scale_factor'] = scale_factor
            weight_analysis['final_weights'] = normalized_weights
            
            # Log final weights
            LOG.info("Final normalized weights:")
            for asset, weight in normalized_weights.items():
                LOG.info(f"  {asset}: {weight:.1%}")
                
        except Exception as e:
            LOG.error(f"Error in weight calculation analysis: {e}")
            weight_analysis['error'] = str(e)
            
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"weight_calculation_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json_data = self._serialize_for_json(weight_analysis)
            json.dump(json_data, f, indent=2)
            
        LOG.info(f"Weight calculation transparency analysis saved to {output_file}")
        self.analysis_results['weight_analysis'] = weight_analysis
        return weight_analysis
    
    def run_comprehensive_transparency_analysis(self, 
                                              strategy_name: str = "Dynamic Allocation",
                                              current_date: Optional[str] = None,
                                              generate_notebooks: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive transparency analysis including PE data, weight calculation,
        and notebook generation
        
        Args:
            strategy_name: Strategy to analyze
            current_date: Analysis date
            generate_notebooks: Whether to generate Jupyter notebooks
            
        Returns:
            Complete analysis results
        """
        LOG.info(f"Starting comprehensive transparency analysis for {strategy_name}")
        
        comprehensive_results = {
            'strategy_name': strategy_name,
            'analysis_date': current_date or datetime.now().strftime('%Y-%m-%d'),
            'analyses': {},
            'notebooks': {}
        }
        
        try:
            # 1. PE Data Analysis
            pe_analysis = self.analyze_pe_data_transparency(current_date=current_date)
            comprehensive_results['analyses']['pe_data'] = pe_analysis
            
            # 2. Weight Calculation Analysis
            weight_analysis = self.analyze_weight_calculation_transparency(
                strategy_name=strategy_name, 
                current_date=current_date
            )
            comprehensive_results['analyses']['weight_calculation'] = weight_analysis
            
            # 3. Generate notebooks if requested
            if generate_notebooks:
                LOG.info("Generating transparency notebooks...")
                
                # PE Analysis notebook
                pe_notebook = self.generate_transparency_notebook(
                    'pe_data', pe_analysis, 'pe_data_transparency'
                )
                comprehensive_results['notebooks']['pe_analysis'] = pe_notebook
                
                # Weight calculation notebook
                weight_notebook = self.generate_transparency_notebook(
                    'weight_calculation', weight_analysis, 'weight_calculation_transparency'
                )
                comprehensive_results['notebooks']['weight_calculation'] = weight_notebook
                
        except Exception as e:
            LOG.error(f"Error in comprehensive transparency analysis: {e}")
            comprehensive_results['error'] = str(e)
            
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"comprehensive_analysis_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json_data = self._serialize_for_json(comprehensive_results)
            json.dump(json_data, f, indent=2)
            
        LOG.info(f"Comprehensive transparency analysis completed and saved to {output_file}")
        return comprehensive_results
    
    def _analyze_asset_pe_data(self, 
                              asset_name: str, 
                              pe_data: pd.DataFrame,
                              analysis_date: pd.Timestamp, 
                              years_back: int) -> Dict[str, Any]:
        """Detailed analysis of individual asset PE data"""
        
        # Timezone handling
        if analysis_date.tz is not None:
            analysis_date = analysis_date.tz_localize(None)
        
        if hasattr(pe_data.index, 'tz') and pe_data.index.tz is not None:
            pe_data = pe_data.copy()
            pe_data.index = pe_data.index.tz_localize(None)
            
        start_date = analysis_date - pd.DateOffset(years=years_back)
        
        analysis = {
            'asset_name': asset_name,
            'data_range': {
                'start': pe_data.index.min().strftime('%Y-%m-%d'),
                'end': pe_data.index.max().strftime('%Y-%m-%d'),
                'total_records': len(pe_data)
            },
            'analysis_period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': analysis_date.strftime('%Y-%m-%d'),
                'years_back': years_back
            }
        }
        
        # Find available PE columns
        pe_columns = []
        for col in ['pe_ratio', 'avg_pe', 'median_pe', 'equal_weight_pe', 'pe', 'estimated_pe']:
            if col in pe_data.columns:
                pe_columns.append(col)
                
        if not pe_columns:
            numeric_cols = pe_data.select_dtypes(include=[np.number]).columns
            pe_columns = list(numeric_cols)
            
        analysis['available_pe_columns'] = pe_columns
        
        if pe_columns:
            pe_col = pe_columns[0]  # Use first available
            analysis['pe_column_used'] = pe_col
            
            # Get period data
            period_data = pe_data.loc[start_date:analysis_date]
            analysis['period_records'] = len(period_data)
            
            if not period_data.empty:
                valid_pe = period_data[pe_col].dropna()
                valid_pe = valid_pe[(valid_pe > 0) & (valid_pe < 200)]
                
                analysis['pe_statistics'] = {
                    'valid_records': len(valid_pe),
                    'mean': valid_pe.mean(),
                    'median': valid_pe.median(),
                    'std': valid_pe.std(),
                    'min': valid_pe.min(),
                    'max': valid_pe.max(),
                    'percentiles': {
                        '10th': valid_pe.quantile(0.1),
                        '25th': valid_pe.quantile(0.25),
                        '75th': valid_pe.quantile(0.75),
                        '90th': valid_pe.quantile(0.9)
                    }
                }
                
                # Current PE analysis
                recent_data = pe_data.loc[:analysis_date][pe_col].dropna()
                if not recent_data.empty:
                    current_pe = recent_data.iloc[-1]
                    current_date = recent_data.index[-1]
                    percentile = (valid_pe <= current_pe).mean()
                    
                    analysis['current_pe_analysis'] = {
                        'current_pe': current_pe,
                        'current_date': current_date.strftime('%Y-%m-%d'),
                        'percentile': percentile,
                        'percentile_clamped': min(max(percentile, 0.1), 0.9)
                    }
        
        return analysis
    
    def _get_pe_calculation_details(self,
                                  asset_name: str,
                                  pe_data: pd.DataFrame,
                                  analysis_date: pd.Timestamp,
                                  years_back: int) -> Dict[str, Any]:
        """Get detailed PE calculation breakdown"""
        
        details = {
            'calculation_steps': [],
            'data_quality': {},
            'historical_context': {}
        }
        
        # Step-by-step calculation details
        details['calculation_steps'] = [
            f"1. Loading PE data for {asset_name}",
            f"2. Filtering data from {analysis_date - pd.DateOffset(years=years_back)} to {analysis_date}",
            f"3. Identifying valid PE column in data",
            f"4. Cleaning data (removing NaN, values <= 0, values >= 200)",
            f"5. Finding most recent PE value up to analysis date",
            f"6. Calculating percentile against historical distribution",
            f"7. Clamping percentile to range [0.1, 0.9] for stability"
        ]
        
        return details
    
    def generate_transparency_notebook(self, 
                                     analysis_type: str,
                                     analysis_results: Dict[str, Any],
                                     notebook_name: str) -> str:
        """
        Generate a Jupyter notebook with detailed transparency analysis
        """
        notebook_dir = Path("notebooks/transparency")
        notebook_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        notebook_path = notebook_dir / f"{notebook_name}_{timestamp}.ipynb"
        
        # Generate a basic notebook structure
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"# {analysis_type.replace('_', ' ').title()} Transparency Analysis\n\n",
                        f"Generated automatically by the Personal Finance Agent Transparency System.\n\n",
                        f"This notebook provides detailed analysis of {analysis_type.replace('_', ' ')} calculations."
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "import matplotlib.pyplot as plt\n",
                        "import json\n",
                        "\n",
                        f"# Analysis results loaded\n",
                        f"analysis_data = {json.dumps(analysis_results, indent=2, default=str)}\n",
                        "print('Analysis data loaded successfully')"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        # Save notebook
        with open(notebook_path, 'w') as f:
            json.dump(notebook_content, f, indent=2)
            
        LOG.info(f"Transparency notebook generated: {notebook_path}")
        return str(notebook_path)
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict()
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        else:
            return obj
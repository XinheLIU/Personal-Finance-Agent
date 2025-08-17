"""
Sector classification configuration for performance attribution analysis.

This module defines how assets are mapped to sectors for sector-based attribution analysis,
following institutional standards similar to GICS (Global Industry Classification Standard).
"""

# Sector definitions based on GICS-like classification
SECTORS = {
    'Technology': {
        'description': 'Technology hardware, software, semiconductors, and tech services',
        'color': '#1f77b4'  # Blue
    },
    'Finance': {
        'description': 'Banks, insurance, real estate, and financial services',
        'color': '#ff7f0e'  # Orange
    },
    'Government_Bonds': {
        'description': 'Government treasury bonds and inflation-protected securities',
        'color': '#2ca02c'  # Green
    },
    'Commodities': {
        'description': 'Precious metals, energy, and commodity-based investments',
        'color': '#d62728'  # Red
    },
    'International_Equity': {
        'description': 'International developed and emerging market equities',
        'color': '#9467bd'  # Purple
    },
    'Cash_Equivalents': {
        'description': 'Money market funds and short-term treasury instruments',
        'color': '#8c564b'  # Brown
    },
    'China_Equity': {
        'description': 'Chinese A-shares and Hong Kong listed equities',
        'color': '#e377c2'  # Pink
    },
    'US_Equity': {
        'description': 'US large-cap and technology-focused equity indices',
        'color': '#7f7f7f'  # Gray
    },
    'Real_Estate': {
        'description': 'Real Estate Investment Trusts (REITs)',
        'color': '#bcbd22'  # Olive
    }
}

# Asset to sector mapping
ASSET_SECTOR_MAPPING = {
    # Chinese Equity
    'CSI300': 'China_Equity',
    'CSI500': 'China_Equity', 
    'HSI': 'China_Equity',
    'HSTECH': 'Technology',  # Hang Seng Tech specifically classified as Technology
    
    # US Equity
    'SP500': 'US_Equity',
    'NASDAQ100': 'Technology',  # NASDAQ 100 is tech-heavy, classify as Technology
    
    # Government Bonds
    'TLT': 'Government_Bonds',
    'TIP': 'Government_Bonds',
    'IEF': 'Government_Bonds',
    'SHY': 'Government_Bonds',
    
    # Cash and Cash Equivalents
    'CASH': 'Cash_Equivalents',
    
    # Commodities
    'GLD': 'Commodities',
    'DBC': 'Commodities',
    
    # International Equity
    'VEA': 'International_Equity',
    'VWO': 'International_Equity',
    
    # Real Estate
    'VNQ': 'Real_Estate'
}

# Reverse mapping: sector to assets
SECTOR_ASSET_MAPPING = {}
for asset, sector in ASSET_SECTOR_MAPPING.items():
    if sector not in SECTOR_ASSET_MAPPING:
        SECTOR_ASSET_MAPPING[sector] = []
    SECTOR_ASSET_MAPPING[sector].append(asset)

# Benchmark sector weights for attribution analysis
# These represent a typical balanced portfolio allocation for comparison
BENCHMARK_SECTOR_WEIGHTS = {
    'US_Equity': 0.35,          # 35% US equity
    'Technology': 0.15,         # 15% Technology (NASDAQ, HSTECH)
    'China_Equity': 0.10,       # 10% China equity (CSI300, CSI500, HSI)
    'International_Equity': 0.15, # 15% International equity
    'Government_Bonds': 0.20,   # 20% Government bonds
    'Cash_Equivalents': 0.02,   # 2% Cash
    'Commodities': 0.02,        # 2% Commodities
    'Real_Estate': 0.01         # 1% Real Estate
}

def get_asset_sector(asset: str) -> str:
    """
    Get the sector classification for a given asset.
    
    Args:
        asset: Asset symbol (e.g., 'SP500', 'CSI300')
        
    Returns:
        Sector name, or 'Other' if not classified
    """
    return ASSET_SECTOR_MAPPING.get(asset, 'Other')

def get_sector_assets(sector: str) -> list:
    """
    Get all assets classified under a given sector.
    
    Args:
        sector: Sector name
        
    Returns:
        List of asset symbols in the sector
    """
    return SECTOR_ASSET_MAPPING.get(sector, [])

def get_sector_color(sector: str) -> str:
    """
    Get the display color for a sector.
    
    Args:
        sector: Sector name
        
    Returns:
        Hex color code for visualization
    """
    return SECTORS.get(sector, {}).get('color', '#17becf')  # Default cyan

def get_all_sectors() -> list:
    """
    Get list of all defined sectors.
    
    Returns:
        List of sector names
    """
    return list(SECTORS.keys())

def calculate_sector_weights(asset_weights: dict) -> dict:
    """
    Calculate sector weights from individual asset weights.
    
    Args:
        asset_weights: Dictionary of {asset: weight}
        
    Returns:
        Dictionary of {sector: total_weight}
    """
    sector_weights = {}
    
    for asset, weight in asset_weights.items():
        sector = get_asset_sector(asset)
        if sector not in sector_weights:
            sector_weights[sector] = 0.0
        sector_weights[sector] += weight
    
    return sector_weights

def validate_sector_mapping() -> dict:
    """
    Validate the sector mapping configuration.
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'valid': True,
        'issues': [],
        'coverage': {},
        'total_benchmark_weight': sum(BENCHMARK_SECTOR_WEIGHTS.values())
    }
    
    # Check if all assets are mapped to sectors
    from config.assets import TRADABLE_ASSETS
    unmapped_assets = []
    for asset in TRADABLE_ASSETS.keys():
        if asset not in ASSET_SECTOR_MAPPING:
            unmapped_assets.append(asset)
    
    if unmapped_assets:
        validation_results['valid'] = False
        validation_results['issues'].append(f"Unmapped assets: {unmapped_assets}")
    
    # Check benchmark weights sum to reasonable total (should be close to 1.0)
    total_benchmark = validation_results['total_benchmark_weight']
    if abs(total_benchmark - 1.0) > 0.05:  # Allow 5% tolerance
        validation_results['issues'].append(f"Benchmark weights sum to {total_benchmark:.3f}, expected ~1.0")
    
    # Calculate sector coverage
    for sector in SECTORS.keys():
        assets_in_sector = get_sector_assets(sector)
        validation_results['coverage'][sector] = len(assets_in_sector)
    
    return validation_results
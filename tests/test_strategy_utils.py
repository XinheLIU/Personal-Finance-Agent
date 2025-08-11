import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from strategies.utils import calculate_pe_percentile, calculate_yield_percentile, get_current_yield

class TestStrategyUtils(unittest.TestCase):

    def setUp(self):
        """Set up mock data for tests."""
        # Mock PE data
        self.pe_cache = {
            'CSI300': pd.DataFrame({
                'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
                'pe_ratio': [10, 12, 11]
            }).set_index('date'),
            'SP500': pd.DataFrame({
                'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
                'pe': [20, 22, 21]
            }).set_index('date')
        }

        # Mock Market data
        self.market_data = {
            'US10Y': pd.DataFrame({
                'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
                'yield': [3.5, 3.6, 3.4]
            }).set_index('date')
        }

    def test_calculate_pe_percentile(self):
        """Test the PE percentile calculation."""
        # Test with valid data
        percentile = calculate_pe_percentile('CSI300', self.pe_cache, '2023-01-03', years=1)
        self.assertAlmostEqual(percentile, 0.6666666666666666)

        # Test with another valid data
        percentile = calculate_pe_percentile('SP500', self.pe_cache, '2023-01-03', years=1)
        self.assertAlmostEqual(percentile, 0.6666666666666666)

        # Test with missing asset
        with self.assertRaises(ValueError):
            calculate_pe_percentile('NASDAQ100', self.pe_cache, '2023-01-03', years=1)

    def test_calculate_yield_percentile(self):
        """Test the yield percentile calculation."""
        # Test with valid data
        percentile = calculate_yield_percentile(self.market_data, '2023-01-03', years=1)
        self.assertAlmostEqual(percentile, 0.3333333333333333)

        # Test with missing data
        with self.assertRaises(ValueError):
            calculate_yield_percentile({'US10Y': pd.DataFrame()}, '2023-01-03', years=1)

    def test_get_current_yield(self):
        """Test getting the current yield."""
        # Test with valid data
        current_yield = get_current_yield(self.market_data, '2023-01-03')
        self.assertEqual(current_yield, 3.4)

        # Test with missing data
        self.assertEqual(get_current_yield({'US10Y': pd.DataFrame()}, '2023-01-03'), 4.0)

if __name__ == '__main__':
    unittest.main()

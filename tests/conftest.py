"""Test configuration for statx."""

import io
import pytest
import pandas as pd


@pytest.fixture
def sample_data():
    """Create a sample dataframe for testing."""
    data = """x,y,group
1,3.4,A
2,5.7,A
3,6.3,B
4,8.1,B
"""
    return pd.read_csv(io.StringIO(data))


@pytest.fixture
def sample_data_no_header():
    """Create a sample dataframe without headers for testing."""
    data = """1,3.4,A
2,5.7,A
3,6.3,B
4,8.1,B
"""
    return data

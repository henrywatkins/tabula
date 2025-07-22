from io import StringIO

import matplotlib.pyplot as plt
import pandas as pd
import pytest
from click.testing import CliRunner

from tabula_cli import plotx
from tabula_cli.plots import parse_plots_script


@pytest.fixture
def runner():
    """Fixture for CliRunner."""
    return CliRunner()


@pytest.fixture
def sample_data():
    """Sample CSV data for testing."""
    return "col1,col2,col3\n1,2,3\n4,5,6\n7,8,9"


def test_parse_script_valid():
    """Test parsing a valid script string."""
    script = "plot:relplot,kind:scatter,x:col1,y:col2,hue:col3"
    plot_func, args = parse_plots_script(script)
    assert args == {"kind": "scatter", "x": "col1", "y": "col2", "hue": "col3"}


def test_parse_script_missing_plot():
    """Test parsing script without plot type defaults to relplot."""
    script = "kind:scatter,x:col1,y:col2"
    plot_func, args = parse_plots_script(script)
    assert args == {"kind": "scatter", "x": "col1", "y": "col2"}


def test_parse_script_invalid():
    """Test parsing invalid script raises ValueError."""
    with pytest.raises(ValueError):
        parse_plots_script("invalid script format")


def test_parse_script_empty():
    """Test parsing empty script raises ValueError."""
    with pytest.raises(ValueError):
        parse_plots_script("")


def test_cli_with_error_handling(runner, sample_data, monkeypatch):
    """Test CLI with invalid script format."""
    # Mock plt.show to prevent actual plot display
    monkeypatch.setattr(plt, "show", lambda: None)

    # Pass empty script string which will trigger ValueError
    result = runner.invoke(plotx, ["--program", "::"], input=sample_data)
    assert result.exit_code == 1
    assert "Error: Invalid script format: Empty script string" in result.output

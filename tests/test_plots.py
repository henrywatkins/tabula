from io import StringIO
import pytest
from click.testing import CliRunner
import pandas as pd
import matplotlib.pyplot as plt

from gullplot.cli import gull, parse_script, parse_columns


@pytest.fixture
def runner():
    """Fixture for CliRunner."""
    return CliRunner()


@pytest.fixture
def sample_data():
    """Sample CSV data for testing."""
    return "col1,col2,col3\n1,2,3\n4,5,6\n7,8,9"


def test_parse_columns_with_values():
    """Test parsing column names with values."""
    result = parse_columns("col1,col2,col3")
    assert result == ["col1", "col2", "col3"]


def test_parse_columns_empty():
    """Test parsing empty column names."""
    result = parse_columns(None)
    assert result == []
    result = parse_columns("")
    assert result == []


def test_parse_script_valid():
    """Test parsing a valid script string."""
    script = "plot:relplot,kind:scatter,x:col1,y:col2,hue:col3"
    plot_func, args = parse_script(script)
    assert args == {"kind": "scatter", "x": "col1", "y": "col2", "hue": "col3"}


def test_parse_script_missing_plot():
    """Test parsing script without plot type defaults to relplot."""
    script = "kind:scatter,x:col1,y:col2"
    plot_func, args = parse_script(script)
    assert args == {"kind": "scatter", "x": "col1", "y": "col2"}


def test_parse_script_invalid():
    """Test parsing invalid script raises ValueError."""
    with pytest.raises(ValueError):
        parse_script("invalid script format")


def test_parse_script_empty():
    """Test parsing empty script raises ValueError."""
    with pytest.raises(ValueError):
        parse_script("")


def test_cli_with_error_handling(runner, sample_data, monkeypatch):
    """Test CLI with invalid script format."""
    # Mock plt.show to prevent actual plot display
    monkeypatch.setattr(plt, "show", lambda: None)

    # Pass empty script string which will trigger ValueError
    result = runner.invoke(
        gull, ["--program", "", "--columns", "col1,col2,col3"], input=sample_data
    )
    assert result.exit_code == 1
    assert "Error: Invalid script format: Empty script string" in result.output


def test_cli_with_output_file(runner, sample_data, monkeypatch, tmp_path):
    """Test CLI with output file."""
    # Mock savefig to avoid actual file creation
    monkeypatch.setattr(plt.Figure, "savefig", lambda self, path: None)

    output_path = str(tmp_path / "test_plot.png")
    result = runner.invoke(
        gull,
        [
            "--program",
            "plot:relplot,kind:scatter,x:col1,y:col2",
            "--columns",
            "col1,col2,col3",
            "--output",
            output_path,
        ],
        input=sample_data,
    )
    assert result.exit_code == 0
    assert f"Plot saved to {output_path}" in result.output

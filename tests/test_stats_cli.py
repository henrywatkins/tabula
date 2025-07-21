"""Tests for the CLI interface."""

import io
import pytest
from click.testing import CliRunner
from statx.cli import statx, parse_script, parse_columns


def test_version():
    """Test the --version flag."""
    runner = CliRunner()
    result = runner.invoke(statx, ["--version"])
    assert result.exit_code == 0
    assert "statx, version" in result.output


def test_help():
    """Test the --help flag."""
    runner = CliRunner()
    result = runner.invoke(statx, ["--help"])
    assert result.exit_code == 0
    assert "Terminal-based statistical testing with statsmodels" in result.output


def test_parse_columns():
    """Test the parse_columns function."""
    assert parse_columns("x,y,z") == ["x", "y", "z"]
    assert parse_columns("  x, y, z  ") == ["x", "y", "z"]
    assert parse_columns(None) == []
    assert parse_columns("") == []


def test_parse_script():
    """Test the parse_script function."""
    # OLS test
    func, args = parse_script("test:ols,dependent:y,independent:x")
    assert func.__name__ == "run_ols"
    assert args == {"dependent": "y", "independent": "x"}

    # Logit test
    func, args = parse_script("test:logit,dependent:y,independent:x+z")
    assert func.__name__ == "run_logit"
    assert args == {"dependent": "y", "independent": "x+z"}

    # t-test with alternative
    func, args = parse_script("test:ttest,sample1:a,sample2:b,alternative:larger")
    assert func.__name__ == "run_ttest"
    assert args == {"sample1": "a", "sample2": "b", "alternative": "larger"}

    # ANOVA test
    func, args = parse_script("test:anova,formula:y ~ C(group)")
    assert func.__name__ == "run_anova"
    assert args == {"formula": "y ~ C(group)"}

    # Default to OLS if test not specified
    func, args = parse_script("dependent:y,independent:x")
    assert func.__name__ == "run_ols"
    assert args == {"dependent": "y", "independent": "x"}


def test_invalid_script_format():
    """Test the parse_script function with invalid input."""
    with pytest.raises(ValueError, match="Empty script string"):
        parse_script("")

    with pytest.raises(ValueError, match="Invalid format"):
        parse_script("test,dependent:y,independent:x")

    with pytest.raises(ValueError, match="Invalid test type"):
        parse_script("test:invalid,dependent:y,independent:x")

    with pytest.raises(ValueError, match="ols requires 'dependent' and 'independent'"):
        parse_script("test:ols,dependent:y")

    with pytest.raises(ValueError, match="ttest requires 'sample1' and 'sample2'"):
        parse_script("test:ttest,sample1:a")

    with pytest.raises(ValueError, match="anova requires 'formula'"):
        parse_script("test:anova")

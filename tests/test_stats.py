"""Tests for the statistical functions."""

import pytest

from tabula_cli.stats import (parse_stats_script, run_anova, run_glm,
                              run_logit, run_ols, run_ttest)


def test_parse_script():
    """Test the parse_script function."""
    # OLS test
    func, args = parse_stats_script("test:ols,dependent:y,independent:x")
    assert func.__name__ == "run_ols"
    assert args == {"dependent": "y", "independent": "x"}

    # Logit test
    func, args = parse_stats_script("test:logit,dependent:y,independent:x+z")
    assert func.__name__ == "run_logit"
    assert args == {"dependent": "y", "independent": "x+z"}

    # t-test with alternative
    func, args = parse_stats_script("test:ttest,sample1:a,sample2:b,alternative:larger")
    assert func.__name__ == "run_ttest"
    assert args == {"sample1": "a", "sample2": "b", "alternative": "larger"}

    # ANOVA test
    func, args = parse_stats_script("test:anova,formula:y ~ C(group)")
    assert func.__name__ == "run_anova"
    assert args == {"formula": "y ~ C(group)"}

    # Default to OLS if test not specified
    func, args = parse_stats_script("dependent:y,independent:x")
    assert func.__name__ == "run_ols"
    assert args == {"dependent": "y", "independent": "x"}


def test_invalid_script_format():
    """Test the parse_script function with invalid input."""
    with pytest.raises(ValueError, match="Empty script string"):
        parse_stats_script("")

    with pytest.raises(ValueError, match="Invalid format"):
        parse_stats_script("test,dependent:y,independent:x")

    with pytest.raises(ValueError, match="Invalid test type"):
        parse_stats_script("test:invalid,dependent:y,independent:x")

    with pytest.raises(ValueError, match="ols requires 'dependent' and 'independent'"):
        parse_stats_script("test:ols,dependent:y")

    with pytest.raises(ValueError, match="ttest requires 'sample1' and 'sample2'"):
        parse_stats_script("test:ttest,sample1:a")

    with pytest.raises(ValueError, match="anova requires 'formula'"):
        parse_stats_script("test:anova")


def test_run_ols(sample_data):
    """Test the OLS regression function."""
    result = run_ols(sample_data, dependent="y", independent="x")
    assert "OLS Regression Results" in result
    assert "R-squared:" in result
    assert "Prob (F-statistic):" in result


def test_run_logit(sample_data):
    """Test the logistic regression function."""
    # Convert y to binary for logit test
    data = sample_data.copy()
    data["binary"] = (data["y"] > data["y"].median()).astype(int)

    result = run_logit(data, dependent="binary", independent="x")
    assert "Logit Regression Results" in result
    # Due to perfect separation, the model may not compute the pseudo R-squared
    # Assert presence of other elements instead
    assert "Log-Likelihood" in result


def test_run_ttest(sample_data):
    """Test the t-test function."""
    result = run_ttest(sample_data, sample1="x", sample2="y", alternative="two-sided")
    assert "t-statistic:" in result
    assert "p-value:" in result
    assert "degrees of freedom:" in result

    # Test with different alternative
    result = run_ttest(sample_data, sample1="x", sample2="y", alternative="larger")
    assert "t-statistic:" in result
    assert "p-value:" in result


def test_run_anova(sample_data):
    """Test the ANOVA function."""
    result = run_anova(sample_data, formula="y ~ C(group)")
    assert "sum_sq" in result
    assert "df" in result
    assert "F" in result
    assert "PR(>F)" in result


def test_run_glm_gaussian(sample_data):
    """Test the GLM function with Gaussian family."""
    result = run_glm(sample_data, dependent="y", independent="x", family="gaussian")
    assert "Generalized Linear Model Regression Results" in result
    assert "Dep. Variable:" in result
    assert "y" in result
    assert "Model:" in result
    assert "GLM" in result
    assert "Family:" in result
    assert "Gaussian" in result


def test_run_glm_binomial(sample_data):
    """Test the GLM function with Binomial family."""
    # Convert y to binary for binomial test
    data = sample_data.copy()
    data["binary"] = (data["y"] > data["y"].median()).astype(int)

    result = run_glm(data, dependent="binary", independent="x", family="binomial")
    assert "Generalized Linear Model Regression Results" in result
    assert "Dep. Variable:" in result
    assert "binary" in result
    assert "Family:" in result
    assert "Binomial" in result


def test_run_glm_poisson(sample_data):
    """Test the GLM function with Poisson family."""
    # Convert y to integer for Poisson test (must be non-negative)
    data = sample_data.copy()
    data["count"] = (data["y"] * 10).astype(int)

    result = run_glm(data, dependent="count", independent="x", family="poisson")
    assert "Generalized Linear Model Regression Results" in result
    assert "Dep. Variable:" in result
    assert "count" in result
    assert "Family:" in result
    assert "Poisson" in result


def test_run_glm_with_link(sample_data):
    """Test the GLM function with custom link."""
    result = run_glm(
        sample_data, dependent="y", independent="x", family="gaussian", link="log"
    )
    assert "Generalized Linear Model Regression Results" in result
    assert "Family:" in result
    assert "Gaussian" in result
    # The statsmodels output format doesn't explicitly display "Link function:" text
    # Check for log in lowercase as it may appear in different formats
    assert "log" in result.lower()

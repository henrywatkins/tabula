"""Statistical models for statx.

This module contains the statistical model functions used by the CLI.
"""

from typing import Dict, Any, Optional
import pandas as pd


class StatxError(Exception):
    """Base exception class for statx errors."""

    pass


class InvalidColumnError(StatxError):
    """Raised when a requested column is not in the DataFrame."""

    pass


class ModelError(StatxError):
    """Raised when a statistical model fails to fit."""

    pass


def validate_columns(df: pd.DataFrame, *columns: str) -> None:
    """Validate that all specified columns exist in the DataFrame.

    Args:
        df: DataFrame to check
        *columns: Column names to validate

    Raises:
        InvalidColumnError: If any column is not present in the DataFrame
    """
    missing_columns = [col for col in columns if col not in df.columns]
    if missing_columns:
        raise InvalidColumnError(
            f"Column(s) not found in data: {', '.join(missing_columns)}"
        )


def run_ols(data: pd.DataFrame, dependent: str, independent: str, **kwargs: Any) -> str:
    """Run an Ordinary Least Squares regression test using statsmodels.

    Args:
        data: DataFrame containing the data
        dependent: Name of dependent variable
        independent: Formula string for independent variables (e.g. "x + z")
        **kwargs: Additional parameters (not currently used)

    Returns:
        Text summary of OLS regression results

    Raises:
        InvalidColumnError: If specified columns don't exist in data
        ModelError: If the model fails to fit
    """
    import statsmodels.formula.api as smf

    # Validate that dependent variable exists in the data
    validate_columns(data, dependent)

    # For independent variables, we need to parse the formula
    # This is a simple check to catch obvious errors - full validation
    # would be complex due to formula syntax
    ind_vars = [v.strip() for v in independent.replace("+", " ").split()]
    for var in ind_vars:
        if ":" not in var and "(" not in var and ")" not in var:
            validate_columns(data, var)

    try:
        formula = f"{dependent} ~ {independent}"
        model = smf.ols(formula, data=data).fit()
        return model.summary().as_text()
    except Exception as e:
        raise ModelError(f"OLS model fitting failed: {str(e)}") from e


def run_logit(
    data: pd.DataFrame, dependent: str, independent: str, **kwargs: Any
) -> str:
    """Run a logistic regression test using statsmodels.

    Args:
        data: DataFrame containing the data
        dependent: Name of dependent variable (should be binary)
        independent: Formula string for independent variables (e.g. "x + z")
        **kwargs: Additional parameters (not currently used)

    Returns:
        Text summary of logistic regression results

    Raises:
        InvalidColumnError: If specified columns don't exist in data
        ModelError: If the model fails to fit
    """
    import statsmodels.formula.api as smf

    # Validate columns
    validate_columns(data, dependent)
    ind_vars = [v.strip() for v in independent.replace("+", " ").split()]
    for var in ind_vars:
        if ":" not in var and "(" not in var and ")" not in var:
            validate_columns(data, var)

    try:
        formula = f"{dependent} ~ {independent}"
        # disp=False suppresses convergence output
        model = smf.logit(formula, data=data).fit(disp=False)
        return model.summary().as_text()
    except Exception as e:
        raise ModelError(f"Logistic regression model fitting failed: {str(e)}") from e


def run_ttest(
    data: pd.DataFrame,
    sample1: str,
    sample2: str,
    alternative: str = "two-sided",
    **kwargs: Any,
) -> str:
    """Run a two-sample t-test using statsmodels.

    Args:
        data: DataFrame containing the data
        sample1: Name of first sample column
        sample2: Name of second sample column
        alternative: Alternative hypothesis ('two-sided', 'larger', 'smaller')
        **kwargs: Additional parameters (not currently used)

    Returns:
        Formatted string with t-test results

    Raises:
        InvalidColumnError: If specified columns don't exist in data
        ModelError: If the test fails
        ValueError: If an invalid alternative is specified
    """
    from statsmodels.stats.weightstats import ttest_ind

    # Validate that columns exist
    validate_columns(data, sample1, sample2)

    # Validate alternative parameter
    valid_alternatives = ["two-sided", "larger", "smaller"]
    if alternative not in valid_alternatives:
        raise ValueError(
            f"Invalid alternative '{alternative}'. "
            f"Must be one of: {', '.join(valid_alternatives)}"
        )

    try:
        s1 = data[sample1].dropna()
        s2 = data[sample2].dropna()

        if len(s1) == 0 or len(s2) == 0:
            raise ModelError("Cannot perform t-test with empty data")

        tstat, pvalue, df = ttest_ind(s1, s2, alternative=alternative)
        return f"t-statistic: {tstat}\np-value: {pvalue}\ndegrees of freedom: {df}"
    except Exception as e:
        if isinstance(e, ModelError):
            raise
        raise ModelError(f"t-test failed: {str(e)}") from e


def run_anova(data: pd.DataFrame, formula: str, **kwargs: Any) -> str:
    """Run an ANOVA test using statsmodels.

    Args:
        data: DataFrame containing the data
        formula: R-style formula for the ANOVA model (e.g. "y ~ C(group)")
        **kwargs: Additional parameters (not currently used)

    Returns:
        ANOVA table as string

    Raises:
        ModelError: If the model fails to fit
    """
    from statsmodels.formula.api import ols
    import statsmodels.api as sm

    try:
        # Extract variables from formula to validate (basic check)
        # This is a simplified check and won't catch all possible issues
        parts = formula.split("~")
        if len(parts) != 2:
            raise ValueError("Invalid formula format. Must contain exactly one '~'")

        dependent = parts[0].strip()
        validate_columns(data, dependent)

        model = ols(formula, data=data).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)
        return anova_table.to_string()
    except Exception as e:
        if isinstance(e, InvalidColumnError):
            raise
        raise ModelError(f"ANOVA model fitting failed: {str(e)}") from e


def run_glm(
    data: pd.DataFrame, dependent: str, independent: str, family: str, **kwargs: Any
) -> str:
    """Run a Generalized Linear Model regression using statsmodels.

    Args:
        data: DataFrame containing the data
        dependent: Name of dependent variable
        independent: Formula string for independent variables (e.g. "x + z")
        family: Distribution family (gaussian, binomial, poisson, gamma, etc.)
        **kwargs: Additional parameters including:
            - link: Link function (identity, log, logit, probit, etc.)
            - alpha: Alpha parameter for NegativeBinomial family
            - var_power: Variance power for Tweedie family
            - power: Power parameter for Power link function

    Returns:
        Text summary of GLM results

    Raises:
        InvalidColumnError: If specified columns don't exist in data
        ValueError: If an invalid family or link is specified
        ModelError: If the model fails to fit
    """
    import statsmodels.formula.api as smf
    import statsmodels.api as sm

    # Validate columns
    validate_columns(data, dependent)
    ind_vars = [v.strip() for v in independent.replace("+", " ").split()]
    for var in ind_vars:
        if ":" not in var and "(" not in var and ")" not in var:
            validate_columns(data, var)

    # Set up family and link function objects
    family_obj = _get_family_object(family, kwargs)

    # Apply custom link if specified
    if "link" in kwargs:
        family_obj = _apply_link_to_family(family_obj, kwargs)

    try:
        formula = f"{dependent} ~ {independent}"
        model = smf.glm(formula, data=data, family=family_obj)
        results = model.fit()
        return results.summary().as_text()
    except Exception as e:
        raise ModelError(f"GLM model fitting failed: {str(e)}") from e


def _get_family_object(family: str, kwargs: Dict[str, Any]) -> Any:
    """Get the statsmodels family object based on family name.

    Args:
        family: Family name string
        kwargs: Additional parameters for family initialization

    Returns:
        Statsmodels family object

    Raises:
        ValueError: If an unsupported family is specified
    """
    import statsmodels.api as sm

    # Convert family string to statsmodels family object
    family_map = {
        "gaussian": sm.families.Gaussian(),
        "binomial": sm.families.Binomial(),
        "poisson": sm.families.Poisson(),
        "gamma": sm.families.Gamma(),
        "inverse_gaussian": sm.families.InverseGaussian(),
        "neg_binomial": sm.families.NegativeBinomial(
            alpha=float(kwargs.get("alpha", 1.0))
        ),
        "tweedie": sm.families.Tweedie(var_power=float(kwargs.get("var_power", 1.5))),
    }

    # Get the family object (case insensitive)
    fam_name = family.lower().replace("-", "_").replace(" ", "_")
    if fam_name not in family_map:
        raise ValueError(
            f"Unsupported family: {family}. "
            f"Supported families: {', '.join(family_map.keys())}"
        )

    return family_map[fam_name]


def _apply_link_to_family(family_obj: Any, kwargs: Dict[str, Any]) -> Any:
    """Apply a link function to a family object.

    Args:
        family_obj: Statsmodels family object
        kwargs: Dictionary containing link parameters

    Returns:
        Modified family object with custom link

    Raises:
        ValueError: If an unsupported link is specified
    """
    import statsmodels.api as sm

    link_name = kwargs["link"].lower().replace("-", "_").replace(" ", "_")
    link_map = {
        "identity": sm.families.links.identity(),
        "log": sm.families.links.log(),
        "logit": sm.families.links.logit(),
        "probit": sm.families.links.probit(),
        "cloglog": sm.families.links.cloglog(),
        "power": sm.families.links.Power(power=float(kwargs.get("power", 1.0))),
        "negativebinomial": sm.families.links.NegativeBinomial(
            alpha=float(kwargs.get("alpha", 1.0))
        ),
        "inverse_squared": sm.families.links.inverse_squared(),
        "inverse": sm.families.links.inverse_power(),
    }

    if link_name not in link_map:
        raise ValueError(
            f"Unsupported link: {kwargs['link']}. "
            f"Supported links: {', '.join(link_map.keys())}"
        )

    return family_obj.__class__(link=link_map[link_name])

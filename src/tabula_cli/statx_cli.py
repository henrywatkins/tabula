"""CLI interface for statx."""

import sys
from io import StringIO
from typing import Dict, List, Tuple, Any, Callable, Optional, TextIO

import click
import pandas as pd

from statx import __version__
from statx.stats import (
    run_ols,
    run_logit,
    run_ttest,
    run_anova,
    run_glm,
    StatxError,
    InvalidColumnError,
    ModelError,
)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="statx")
@click.argument("input_file", type=click.File("r"), default="-")
@click.option(
    "--program",
    "-p",
    type=str,
    required=True,
    help="Script string, the parameters for the statistical test",
)
@click.option(
    "--output",
    "-o",
    type=str,
    help="File where you would like to save the test output",
)
@click.option(
    "--file",
    "-f",
    type=click.File("r"),
    help="Script file. Instead of using a string, you can define the test parameters in a file",
)
@click.option(
    "--separator",
    "-s",
    type=str,
    default=",",
    help="Separator for input data, default is ','",
)
@click.option(
    "--columns",
    "-c",
    type=str,
    default=None,
    help="Column names for the input data, if not present in the file",
)
def statx(
    program: str,
    columns: Optional[str],
    input_file: TextIO,
    output: Optional[str],
    file: Optional[TextIO],
    separator: str,
) -> int:
    """
    Terminal-based statistical testing with statsmodels

    Perform statistical tests on tabular data (CSV or stdin) directly from the terminal.
    Supported tests:
      * ols: Ordinary Least Squares Regression. Required parameters: dependent, independent.
      * logit: Logistic Regression. Required parameters: dependent, independent.
      * ttest: Two-sample t-test. Required parameters: sample1, sample2. Optional: alternative (two-sided, larger, smaller).
      * anova: ANOVA test. Required parameter: formula (e.g., "y ~ C(x)").
      * glm: Generalized Linear Model. Required parameters: dependent, independent, family.
        Optional parameters: link, alpha, var_power, power.

    Define the test parameters using a script string. For example:

        statx data.csv -p "test:ols,dependent:y,independent:x+z"

    If no column names are provided via --columns, the first line of the file is assumed to be the header.
    """
    # If script is provided as a file, read it
    if file:
        try:
            program = file.read()
            if not program.strip():
                click.echo("Error: Script file is empty")
                return 1
        except IOError as e:
            click.echo(f"Error reading script file: {str(e)}")
            return 1

    # Parse the script string
    try:
        test_func, test_args = parse_script(program)
    except ValueError as e:
        click.echo(f"Error: Invalid script format: {str(e)}")
        return 1

    # Load and process data
    try:
        # Parse column names if provided
        column_names = parse_columns(columns)

        # Read input data
        try:
            contents = input_file.read()
        except IOError as e:
            click.echo(f"Error reading input file: {str(e)}")
            return 1

        # Parse CSV data
        try:
            # Prepare parameters for read_csv
            params = {"sep": separator}
            if column_names:
                params["names"] = column_names
            
            df = pd.read_csv(StringIO(contents), **params)
            if df.empty:
                click.echo("Error: Input data is empty")
                return 1
        except Exception as e:
            click.echo(f"Error parsing CSV data: {str(e)}")
            return 1

        # Run the statistical test
        try:
            result = test_func(df, **test_args)
        except InvalidColumnError as e:
            click.echo(f"Error: {str(e)}")
            return 1
        except ModelError as e:
            click.echo(f"Error in statistical model: {str(e)}")
            return 1
        except ValueError as e:
            click.echo(f"Error: {str(e)}")
            return 1
        except Exception as e:
            click.echo(f"Unexpected error: {str(e)}")
            return 1

        # Output results
        if output:
            try:
                with open(output, "w") as f:
                    f.write(result)
                click.echo(f"Test result saved to {output}")
            except IOError as e:
                click.echo(f"Error writing to output file: {str(e)}")
                return 1
        else:
            click.echo(result)

        return 0

    except Exception as e:
        click.echo(f"Error: {str(e)}")
        return 1


def parse_columns(column_string: Optional[str]) -> List[str]:
    """Parse comma-separated column names into a list.

    Args:
        column_string: A comma-separated string of column names

    Returns:
        A list of column names.
    """
    if column_string:
        return [col.strip() for col in column_string.strip().split(",")]
    else:
        return []


def parse_script(
    script_string: str,
) -> Tuple[Callable[[pd.DataFrame, Any], str], Dict[str, Any]]:
    """
    Parse the script string and return the test function and its arguments.

    The script string should be formatted as key:value pairs separated by commas.
    Example:
        "test:ols,dependent:y,independent:x+z"

    Args:
        script_string: The script string to parse

    Returns:
        A tuple containing:
            - The test function to call
            - A dictionary of arguments to pass to the function

    Raises:
        ValueError: If the script string is invalid or missing required parameters
    """
    if not script_string or not script_string.strip():
        raise ValueError("Empty script string")

    elements = script_string.strip()
    try:
        # Use split with maxsplit=1 for values in case they contain colons.
        elements_dict = dict(
            (item.split(":", 1)[0].strip(), item.split(":", 1)[1].strip())
            for item in elements.split(",")
        )
    except IndexError:
        raise ValueError(
            "Invalid format. Expected 'key:value' pairs separated by commas"
        )

    # Map test types to their functions
    test_types = {
        "ols": run_ols,
        "logit": run_logit,
        "ttest": run_ttest,
        "anova": run_anova,
        "glm": run_glm,
    }

    # Default to "ols" if no test key is provided
    if "test" not in elements_dict:
        test_choice = "ols"
    elif elements_dict["test"].lower() in test_types:
        test_choice = elements_dict["test"].lower()
    else:
        raise ValueError(
            f"Invalid test type. Supported tests: {', '.join(test_types.keys())}"
        )

    # Remove the test key from parameters
    elements_dict.pop("test", None)

    # Verify required parameters for each test
    if test_choice in ["ols", "logit", "glm"]:
        if "dependent" not in elements_dict or "independent" not in elements_dict:
            raise ValueError(
                f"{test_choice} requires 'dependent' and 'independent' parameters"
            )
        if test_choice == "glm" and "family" not in elements_dict:
            raise ValueError(
                "glm requires 'family' parameter (gaussian, binomial, poisson, gamma, etc.)"
            )
    elif test_choice == "ttest":
        if "sample1" not in elements_dict or "sample2" not in elements_dict:
            raise ValueError("ttest requires 'sample1' and 'sample2' parameters")
    elif test_choice == "anova":
        if "formula" not in elements_dict:
            raise ValueError("anova requires 'formula' parameter")

    return test_types[test_choice], elements_dict


# Statistical functions have been moved to the statx.stats module

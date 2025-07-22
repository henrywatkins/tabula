from io import StringIO
from typing import Any, Callable, Dict, List, Optional, TextIO, Tuple

import click
import matplotlib.pyplot as plt
import pandas as pd
import polars as pl

from tabula_cli.plots import *
from tabula_cli.stats import *
from tabula_cli.tables import *


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_file", type=click.File("r"), default="-")
@click.option(
    "-t",
    "--type",
    type=click.Choice(["csv", "tsv"], case_sensitive=False),
    default="csv",
    help="Type of input file: csv or tsv",
)
@click.option(
    "--program",
    "-p",
    type=str,
    required=True,
    help="Script string, the parameters and columns to use in plotting",
)
@click.option(
    "-o",
    "--output",
    type=click.Choice(["polars", "csv", "tsv"], case_sensitive=False),
    default="polars",
    help="Type of output format: polars, csv or tsv",
)
@click.option(
    "--no-header", is_flag=True, help="If the input file does not contain header names"
)
def main(program, input_file, type, no_header, output: str) -> None:
    """Process a CSV or TSV file with a chain of operations.

    EXPRESSION is a chain of operations like select(col1,col2).method1().method2()...

    \b
    Available methods:
    select(col1, col2, ...) - Select specific columns from the dataframe.
    upper(col) - Convert the specified column to uppercase.
    lower(col) - Convert the specified column to lowercase.
    strlen(col) - Get the length of the specified column's strings.
    where(condition) - Filter rows based on a condition.
    head(n) - Get the first n rows of the dataframe.
    tail(n) - Get the last n rows of the dataframe.
    count() - Count the number of rows in the dataframe.
    columns() - Get the list of column names in the dataframe.
    min(col) - Get the minimum value of the specified column.
    max(col) - Get the maximum value of the specified column.
    sum(col) - Get the sum of the specified column.
    strjoin(col, separator) - Join strings in the specified column with a separator.
    uniq(col) - Get unique values from the specified column.
    uniqc(col) - Count unique values in the specified column.
    mean(col) - Calculate the mean of the specified column.
    median(col) - Calculate the median of the specified column.
    mode(col) - Calculate the mode of the specified column.
    first(col) - Get the first value of the specified column.
    last(col) - Get the last value of the specified column.
    std(col) - Calculate the standard deviation of the specified column.
    var(col) - Calculate the variance of the specified column.
    round(col, decimals) - Round the specified column to a given number of decimal places.
    sortby(col, False) - Sort the dataframe by the specified column in ascending (False).
    """

    content = input_file.read()
    buffer = StringIO(content)
    separator = "," if type.lower() == "csv" else "\t"
    try:
        df = pl.read_csv(buffer, separator=separator, has_header=not no_header)
    except pl.exceptions.NoDataError:
        click.echo("Input file is empty or contains no data.", err=True)
        return

    if not validate_chain(program):
        click.echo(
            "Invalid expression format. Double check expression syntax.", err=True
        )
        return

    try:
        result = parse_chain(program, df)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return
    if output.lower() == "polars":
        click.echo(result)
    elif output.lower() == "tsv":
        separator = "\t"
        click.echo(result.write_csv(separator=separator))
    else:  # Default to CSV
        separator = ","
        click.echo(result.write_csv(separator=separator))


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_file", type=click.File("r"), default="-")
@click.option(
    "--program",
    "-p",
    type=str,
    required=True,
    help="Script string, the parameters and columns to use in plotting",
)
@click.option(
    "--output", "-o", type=str, help="File where you would like to save image output"
)
@click.option(
    "-t",
    "--type",
    type=click.Choice(["csv", "tsv"], case_sensitive=False),
    default="csv",
    help="Type of input file: csv or tsv",
)
@click.option(
    "--no-header", is_flag=True, help="If the input file does not contain header names"
)
def plotx(
    program: str,
    input_file,
    output: Optional[str],
    type: str,
    no_header: bool,
) -> int:
    """Terminal-based plotting with seaborn

    Plot data from a tabular data file or from stdin, all from the terminal. An ideal
    companion for awk, grep and other terminal-based processing tools. Uses seaborn as
    a plotting interface, so for more information see the seaborn website
    (https://seaborn.pydata.org/)

    Plot types:
      * relplot (default), kinds: scatter, line
      * catplot, kinds: strip (default), swarm, box, violin, boxen, point, bar, count
      * displot, kinds: hist (default), kde, ecdf
      * pairplot

    Define the plotting parameters and columns to use with a string.

    Example: to plot a scatterplot of data with column names col1, col2, and coloured by
    the value in col3:

        gullplot data.csv -p "plot:relplot,kind:scatter,x:col1,y:col2,hue:col3"

    If the --no-header option is passed, the input file is assumed to not have header names.
    In this case, the columns will be named column_1, column_2, etc
    """
    separator = "," if type.lower() == "csv" else "\t"
    try:
        plot_type, plot_args = parse_plots_script(program)
    except Exception as e:
        click.echo(f"Error: Invalid script format: {str(e)}")
        return 1

    try:
        contents = input_file.read()
        if no_header:
            df = pd.read_csv(StringIO(contents), sep=separator, header=None)
            name_dict = {i: f"column_{i+1}" for i in df.columns}
            df.rename(columns=name_dict, inplace=True)
        else:
            df = pd.read_csv(StringIO(contents), sep=separator, header="infer")

        fig = plot_type(data=df, **plot_args)

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        if output:
            fig.figure.savefig(output)
            click.echo(f"Plot saved to {output}")
        else:
            plt.show()
        return 0
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        return 1


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_file", type=click.File("r"), default="-")
@click.option(
    "--program",
    "-p",
    type=str,
    required=True,
    help="Script string, the parameters for the statistical test",
)
@click.option(
    "-t",
    "--type",
    type=click.Choice(["csv", "tsv"], case_sensitive=False),
    default="csv",
    help="Type of input file: csv or tsv",
)
@click.option(
    "--no-header", is_flag=True, help="If the input file does not contain header names"
)
def statx(
    program: str,
    input_file: TextIO,
    type: str,
    no_header: bool,
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

    If --no-header is passed as an option, the input file is assumed to not have header names.
    In this case, the columns will be named column_1, column_2, etc
    """

    # Parse the script string
    try:
        test_func, test_args = parse_stats_script(program)
    except ValueError as e:
        click.echo(f"Error: Invalid script format: {str(e)}")
        return 1

    separator = "," if type.lower() == "csv" else "\t"
    # Load and process data
    try:

        # Read input data
        try:
            contents = input_file.read()
        except IOError as e:
            click.echo(f"Error reading input file: {str(e)}")
            return 1

        # Parse CSV data
        try:
            # Prepare parameters for read_csv
            if no_header:
                df = pd.read_csv(StringIO(contents), sep=separator, header=None)
                name_dict = {i: f"column_{i+1}" for i in df.columns}
                df.rename(columns=name_dict, inplace=True)
            else:
                df = pd.read_csv(StringIO(contents), sep=separator, header="infer")
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

        click.echo(result)

        return 0

    except Exception as e:
        click.echo(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    main()

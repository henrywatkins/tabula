import re
from io import StringIO
from typing import Dict, List, Tuple, Any, Callable, Optional

import click
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_style("whitegrid")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="gullplot")
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
    "--file",
    "-f",
    type=click.File("r"),
    help="Script file. Instead of using a string, you can define the plotting parameters in a file",
)
@click.option(
    "--separator",
    "-s",
    type=str,
    default=",",
    help="Separator for input data, default is ',' ",
)
@click.option(
    "--columns",
    "-c",
    type=str,
    default=None,
    help="Column names for the input data, if not present in the file",
)
def gull(
    program: str,
    columns: Optional[str],
    input_file,
    output: Optional[str],
    file,
    separator: str,
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

        gullplot data.csv -p "plot:relplot,kind:scatter,x:col1,y:col2,hue:col3" -c "col1,col2,col3"

    If no column names are defined via the --columns option, the first line of the file
    is assumed to be the column names.
    """
    if file:
        program = file.read()

    try:
        plot_type, plot_args = parse_script(program)
    except Exception as e:
        click.echo(f"Error: Invalid script format: {str(e)}")
        return 1

    try:
        column_names = parse_columns(columns)
        contents = input_file.read()
        name_dict = {"names": column_names} if column_names else {}

        df = pd.read_csv(StringIO(contents), sep=separator, **name_dict)
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


def parse_columns(column_string: Optional[str]) -> List[str]:
    """Parse comma-separated column names into a list.

    Args:
        column_string: A comma-separated string of column names

    Returns:
        A list of column names
    """
    if column_string:
        return column_string.strip().split(",")
    else:
        return []


def parse_script(script_string: str) -> Tuple[Callable, Dict[str, Any]]:
    """Parse the script string and return the plot function and arguments.

    Args:
        script_string: A string with format "plot:type,kind:value,x:column,y:column,..."

    Returns:
        A tuple containing (plotting_function, arguments_dict)

    Raises:
        ValueError: If script format is invalid or required parameters are missing
    """
    if not script_string or not script_string.strip():
        raise ValueError("Empty script string")

    elements = script_string.strip()

    try:
        elements_dict = dict(
            [
                (i.split(":")[0].strip(), i.split(":")[1].strip())
                for i in elements.split(",")
            ]
        )
    except IndexError:
        raise ValueError(
            "Invalid format. Expected 'key:value' pairs separated by commas"
        )

    plot_types = {
        "relplot": sns.relplot,
        "catplot": sns.catplot,
        "displot": sns.displot,
        "pairplot": sns.pairplot,
    }

    # Check if plot type is specified
    if "plot" not in elements_dict:
        plot_choice = "relplot"
    elif elements_dict["plot"] in plot_types:
        plot_choice = elements_dict["plot"]
    else:
        raise ValueError(
            f"Invalid plot type. Supported types: {', '.join(plot_types.keys())}"
        )

    # Remove the plot key from arguments
    elements_dict.pop("plot", None)

    # Verify required arguments based on plot type
    if plot_choice != "pairplot" and "x" not in elements_dict:
        raise ValueError(f"{plot_choice} requires 'x' parameter")

    return plot_types[plot_choice], elements_dict

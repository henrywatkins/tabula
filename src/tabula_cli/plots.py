from typing import Any, Callable, Dict, List, Optional, Tuple

import seaborn as sns

sns.set_style("whitegrid")


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

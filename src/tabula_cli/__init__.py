import re
from io import StringIO

import click
import polars as pl

VALID_METHODS = [
    "select",
    "upper",
    "lower",
    "length",
    "where",
    "head",
    "tail",
    "count",
    "min",
    "max",
    "sum",
    "strjoin",
    "strlen",  # Alias for length
    "uniq",
    "uniqc",
    "mean",
    "median",
    "mode",
    "first",
    "last",
    "std",
    "var",
    "round",
    "sortby",
    "columns",
]
TERMINAL_METHODS = [
    "count",
    "columns",
    "min",
    "strjoin",
    "max",
    "sum",
    "uniq",
    "mean",
    "median",
    "mode",
    "first",
    "last",
    "std",
    "var",
]


def validate_chain(expression):
    """Validates if the expression is of the form select(col1,col2).method1().method2()..."""
    # Check if expression is empty
    if not expression or not expression.strip():
        return False
    # Split by dot to get individual method calls
    calls = expression.split(".")
    for i, call in enumerate(calls):
        call = call.strip()
        match = re.match(r"(\w+)\((.*?)\)$", call)
        if not match:
            return False
        method = match.group(1)
        # Check if method is in valid methods list
        if method not in VALID_METHODS:
            return False
        # If a terminal method is found, it must be the last in the chain
        if method in TERMINAL_METHODS and i != len(calls) - 1:
            return False
    return True


def parse_arguments(args_str):
    """Parse argument string into args."""
    args = []
    if args_str:
        # Split by commas, but ignore commas inside single or double quotes
        args_list = re.findall(
            r"""((?:(?:"(?:\\.|[^"])*")|(?:'(?:\\.|[^'])*')|[^,'"])+)""", args_str
        )
        args_list = [arg for arg in (a.strip() for a in args_list) if arg]

        for arg in args_list:
            arg = arg.strip()
            if (arg.startswith('"') and arg.endswith('"')) or (
                arg.startswith("'") and arg.endswith("'")
            ):
                args.append(arg[1:-1])
            else:
                try:
                    args.append(eval(arg))
                except Exception:
                    args.append(arg)
    return args


def find_replace_variables(text, replacement_func):
    """
    Find and replace variable names in expressions while avoiding single-quoted strings.

    Args:
        text: The input text containing expressions
        replacement_func: Function that takes a variable name and returns its replacement

    Returns:
        Text with variables replaced according to replacement_func
    """
    # Pattern explanation:
    # (?:'[^']*'|"[^"]*")  - Match single or double quoted strings (to skip them)
    # |                    - OR
    # \b([a-zA-Z_][a-zA-Z0-9_]*)\b  - Match word boundaries around identifiers

    pattern = r"(?:'[^']*'|\"[^\"]*\")|(\b[a-zA-Z_][a-zA-Z0-9_]*\b)"

    def replace_match(match):
        # If the match is a quoted string (group 1 is None), return it unchanged
        if match.group(1) is None:
            return match.group(0)

        # Otherwise, it's a variable name - apply the replacement function
        variable_name = match.group(1)
        return replacement_func(variable_name)

    return re.sub(pattern, replace_match, text)


def extract_variables(text: str) -> set[str]:
    """
    Extract all variable names from an expression, excluding quoted strings.

    Args:
        text: The input text containing expressions

    Returns:
        Set of variable names found in the text
    """
    variables = set()

    def collect_variable(var_name: str) -> str:
        variables.add(var_name)
        return var_name

    find_replace_variables(text, collect_variable)
    return variables


def polars_wrapper(var_name: str) -> str:
    return f"pl.col('{var_name}')"


def convert_to_polars_expr(expr):
    """Convert a string expression to a Polars expression."""
    replaced = find_replace_variables(expr, polars_wrapper)
    return eval(replaced)


def apply_method(method, args, df):
    """Apply a single method to the dataframe."""
    if method == "select":
        return df.select(pl.col(*args))
    elif method == "upper":
        return df.with_columns(pl.col(*args).str.to_uppercase())
    elif method == "lower":
        return df.with_columns(pl.col(*args).str.to_lowercase())
    elif method == "strlen":
        return df.with_columns(pl.col(*args).str.len_chars().alias(f"{args[0]}_length"))
    elif method == "where":
        polars_expr = convert_to_polars_expr(args[0])
        return df.filter(polars_expr)
    elif method == "head":
        n = args[0] if args else 5
        return df.head(n)
    elif method == "tail":
        n = args[0] if args else 5
        return df.tail(n)
    elif method == "count":
        return df.select(pl.count())
    elif method == "columns":
        return df.columns
    elif method == "min":
        return df.select(pl.col(*args).min())
    elif method == "max":
        return df.select(pl.col(*args).max())
    elif method == "sum":
        return df.select(pl.col(*args).sum())
    elif method == "strjoin":
        separator = args[1] if len(args) > 1 else ""
        return df.select(pl.col(args[0]).str.join(separator).alias(f"{args[0]}_joined"))
    elif method == "uniq":
        # Return unique values from the specified column
        return df.select(pl.col(args[0]).unique())
    elif method == "uniqc":
        return df.group_by(*args).agg(pl.count())
    elif method == "mean":
        return df.select(pl.col(*args).mean())
    elif method == "median":
        return df.select(pl.col(*args).median())
    elif method == "mode":
        return df.select(pl.col(*args).mode())
    elif method == "first":
        return df.select(pl.col(*args).first())
    elif method == "last":
        return df.select(pl.col(*args).last())
    elif method == "std":
        return df.select(pl.col(*args).std())
    elif method == "var":
        return df.select(pl.col(*args).var())
    elif method == "round":
        decimals = args[1] if len(args) > 1 else 0
        return df.with_columns(pl.col(args[0]).round(decimals))
    elif method == "sortby":
        descending = args[1] if len(args) > 1 and isinstance(args[1], bool) else False
        return df.sort(by=args[0], descending=descending)
    else:
        raise ValueError(f"Unknown method: {method}")


def parse_chain(expression, df):
    """Parse a chain of operations and apply them to the dataframe."""
    calls = expression.split(".")
    result = df
    for call in calls:
        call = call.strip()
        match = re.match(r"(\w+)\((.*?)\)$", call)
        method, args_str = match.group(1), match.group(2)
        args = parse_arguments(args_str)
        result = apply_method(method, args, result)

    return result


@click.command()
@click.argument("expression")
@click.argument("input_file", type=click.File("r"), default="-")
@click.option(
    "-t",
    "--type",
    type=click.Choice(["csv", "tsv"], case_sensitive=False),
    default="csv",
    help="Type of input file: csv or tsv",
)
@click.option(
    "-o",
    "--outtype",
    type=click.Choice(["polars", "csv", "tsv"], case_sensitive=False),
    default="polars",
    help="Type of output format: polars, csv or tsv",
)
@click.option(
    "--no-header", is_flag=True, help="If the input file does not contain header names"
)
def main(expression, input_file, type, no_header, outtype):
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

    if not validate_chain(expression):
        click.echo(
            "Invalid expression format. Double check expression syntax.", err=True
        )
        return

    try:
        result = parse_chain(expression, df)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return
    if outtype.lower() == "polars":
        click.echo(result)
    elif outtype.lower() == "tsv":
        separator = "\t"
        click.echo(result.write_csv(separator=separator))
    else:  # Default to CSV
        separator = ","
        click.echo(result.write_csv(separator=separator))


if __name__ == "__main__":
    main()

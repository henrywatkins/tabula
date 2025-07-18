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

def convert_to_polars_expr(expr):
    """Convert a string expression to a Polars expression."""
    pass



def apply_method(method, args, df):
    """Apply a single method to the dataframe."""
    if method == "select":
        return df.select(pl.col(*args))
    elif method == "upper":
        return df.with_columns(pl.col(*args).str.to_uppercase())
    elif method == "lower":
        return df.with_columns(pl.col(*args).str.to_lowercase())
    elif method == "length":
        return df.with_columns(pl.col(*args).str.lengths().alias(f"{args[0]}_length"))
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
        return df.unique()
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
    "--no-header", is_flag=True, help="Input file does not contain header names"
)
def main(expression, input_file, type, no_header):
    """Process a CSV or TSV file with a chain of operations."""
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
    click.echo(result)


if __name__ == "__main__":
    main()

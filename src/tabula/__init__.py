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
    "join",
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
    "groupby",
]


def validate_chain(expression):
    """Validates if the expression is of the form select(col1,col2).method1().method2()..."""
    # Check if expression is empty
    if not expression or not expression.strip():
        return False
    # Split by dot to get individual method calls
    calls = expression.split(".")
    # Check each method call
    for i, call in enumerate(calls):
        call = call.strip()
        match = re.match(r"(\w+)\((.*?)\)$", call)
        if not match:
            return False
        method = match.group(1)
        # Check if method is in valid methods list
        if method not in VALID_METHODS:
            return False
    return True


def parse_chain(expression, df):
    """Parse a chain of operations and apply them to the dataframe."""
    # Split the expression by dots to get individual method calls
    calls = expression.split(".")
    result = df

    for call in calls:
        call = call.strip()
        match = re.match(r"(\w+)\((.*?)\)$", call)
        if not match:
            raise ValueError(f"Invalid method call format: {call}")
        method, args_str = match.group(1), match.group(2)
        # Parse arguments
        args = []
        kwargs = {}
        if args_str:
            # Split by commas, but ignore commas inside quotes
            args_list = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', args_str)
            for arg in args_list:
                arg = arg.strip()
                # Check if it's a keyword argument
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    kwargs[key.strip()] = eval(value.strip())  # Be careful with eval
                else:
                    # Handle quoted strings
                    if (arg.startswith('"') and arg.endswith('"')) or (
                        arg.startswith("'") and arg.endswith("'")
                    ):
                        args.append(arg[1:-1])  # Remove quotes
                    else:
                        try:
                            # Try to convert to appropriate type
                            args.append(eval(arg))
                        except:
                            args.append(arg)

        # Apply the method based on its name
        if method == "select":
            result = result.select(pl.col(*args))
        elif method == "upper":
            result = result.with_columns(pl.col(*args).str.to_uppercase())
        elif method == "lower":
            result = result.with_columns(pl.col(*args).str.to_lowercase())
        elif method == "length":
            result = result.with_columns(
                pl.col(*args).str.lengths().alias(f"{args[0]}_length")
            )
        elif method == "where":
            # args[0] should be a filter expression
            result = result.filter(eval(f"pl.col('{args[0]}') {args[1]} {args[2]}"))
        elif method == "head":
            n = args[0] if args else 5
            result = result.head(n)
        elif method == "tail":
            n = args[0] if args else 5
            result = result.tail(n)
        elif method == "count":
            result = result.select(pl.count())
        elif method == "min":
            result = result.select(pl.col(*args).min())
        elif method == "max":
            result = result.select(pl.col(*args).max())
        elif method == "sum":
            result = result.select(pl.col(*args).sum())
        elif method == "join":
            # Join requires another dataframe - this is simplified
            other_df = args[0]
            on = args[1] if len(args) > 1 else None
            how = args[2] if len(args) > 2 else "inner"
            result = result.join(other_df, on=on, how=how)
        elif method == "uniq":
            result = result.unique()
        elif method == "uniqc":
            result = result.group_by(*args).agg(pl.count())
        elif method == "mean":
            result = result.select(pl.col(*args).mean())
        elif method == "median":
            result = result.select(pl.col(*args).median())
        elif method == "mode":
            result = result.select(pl.col(*args).mode())
        elif method == "first":
            result = result.select(pl.col(*args).first())
        elif method == "last":
            result = result.select(pl.col(*args).last())
        elif method == "std":
            result = result.select(pl.col(*args).std())
        elif method == "var":
            result = result.select(pl.col(*args).var())
        elif method == "round":
            decimals = args[1] if len(args) > 1 else 0
            result = result.with_columns(pl.col(args[0]).round(decimals))
        elif method == "sortby":
            descending = (
                args[1] if len(args) > 1 and isinstance(args[1], bool) else False
            )
            result = result.sort(by=args[0], descending=descending)
        elif method == "groupby":
            # This typically needs an aggregation function
            result = result.group_by(*args)

    return result


@click.command()
@click.argument("expression")
@click.argument("input_file", type=click.File("r"), default="-")
@click.option("-F", "--separator", default=",", help="Delimiter for input file")
@click.option(
    "--no-header", is_flag=True, help="Input file does not contain header names"
)
def main(expression, input_file, separator, no_header):
    """Process a CSV file with a chain of operations."""
    if no_header:
        df = pl.read_csv(input_file, separator=separator, has_header=False)
    else:
        df = pl.read_csv(input_file, separator=separator)

    if not validate_chain(expression):
        click.echo(
            "Invalid expression format. Please use the correct syntax.", err=True
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

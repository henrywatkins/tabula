import re

import click
import pandas as pd


class Query:
    def __init__(self, df):
        self.df = df.copy()

    def select(self, *cols):
        missing = [c for c in cols if c not in self.df.columns]
        if missing:
            raise ValueError(f"Columns not found: {missing}")
        self.df = self.df[list(cols)]
        return self

    def upper(self, col):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        self.df[col] = self.df[col].str.upper()
        return self

    def lower(self, col):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        self.df[col] = self.df[col].str.lower()
        return self

    def length(self, col):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        self.df[col] = self.df[col].str.len()
        return self

    def where(self, condition):
        try:
            self.df = self.df.query(condition)
        except Exception as e:
            raise ValueError(f"Error in where: {e}")
        return self

    def head(self, n):
        self.df = self.df.head(n)
        return self

    def tail(self, n):
        self.df = self.df.tail(n)
        return self

    def count(self, col=None):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].count()
        return len(self.df)

    def min(self, col):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].min()
        return self.df.min()

    def max(self, col):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].max()
        return self.df.max()

    def sum(self, col=None):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].sum()
        return self.df.sum()

    def join(self, col, separator=","):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        return self.df[col].astype(str).str.cat(sep=separator)

    def uniq(self, col):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        return self.df[col].unique().tolist()

    def uniqc(self, col):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        value_counts = self.df[col].value_counts().to_dict()
        return value_counts

    def mean(self, col):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].mean()
        return self.df.mean()

    def median(self, col):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].median()
        return self.df.median()

    def mode(self, col):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].mode()[0] if not self.df[col].mode().empty else None
        return self.df.mode()

    def first(self, col=None):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].iloc[0] if not self.df.empty else None
        return self.df.iloc[0] if not self.df.empty else None

    def last(self, col=None):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].iloc[-1] if not self.df.empty else None
        return self.df.iloc[-1] if not self.df.empty else None

    def std(self, col):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].std()
        return self.df.std()

    def var(self, col):
        if col:
            if col not in self.df.columns:
                raise ValueError(f"Column not found: {col}")
            return self.df[col].var()
        return self.df.var()

    def round(self, col, decimals=0):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        self.df[col] = self.df[col].round(decimals)
        return self

    def sortby(self, col, ascending=True):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")
        self.df = self.df.sort_values(by=col, ascending=ascending)
        return self

    def groupby(self, col, agg_func="count"):
        if col not in self.df.columns:
            raise ValueError(f"Column not found: {col}")

        valid_aggs = ["count", "sum", "mean", "min", "max", "median"]
        if agg_func not in valid_aggs:
            raise ValueError(
                f"Invalid aggregation function: {agg_func}. Valid options are: {valid_aggs}"
            )

        if agg_func == "count":
            self.df = self.df.groupby(col).size().reset_index(name="count")
        else:
            # For other aggregations, we need to specify which columns to aggregate
            # Here we aggregate all numeric columns
            numeric_cols = self.df.select_dtypes(include=["number"]).columns
            if len(numeric_cols) == 0:
                raise ValueError(f"No numeric columns found for {agg_func} aggregation")

            agg_dict = {col: agg_func for col in numeric_cols if col != col}
            if agg_dict:
                self.df = self.df.groupby(col).agg(agg_dict).reset_index()

        return self

    def result(self):
        return self.df.to_csv(index=False)


def parse_chain(expression, df):
    # Split the chain on dot, e.g. select(age,name).where(age>20).len(name)
    calls = expression.split(".")
    q = Query(df)
    for i, call in enumerate(calls):
        call = call.strip()
        m = re.match(r"(\w+)\((.*?)\)$", call)
        if not m:
            raise ValueError(f"Invalid chain expression: {call}")
        method, args_str = m.group(1), m.group(2).strip()

        def parse_chain(expression, df):
            # Split the chain on dot, e.g. select(age,name).where(age>20).len(name)
            calls = expression.split(".")
            q = Query(df)

            # Methods that return a value instead of self
            terminal_methods = {
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
            }

            for i, call in enumerate(calls):
                call = call.strip()
                m = re.match(r"(\w+)\((.*?)\)$", call)
                if not m:
                    raise ValueError(f"Invalid chain expression: {call}")
                method, args_str = m.group(1), m.group(2).strip()

                # Check if terminal method is used in the middle of the chain
                if method in terminal_methods and i < len(calls) - 1:
                    raise ValueError(
                        f"Method '{method}' must be the last call in the chain."
                    )

                # Parse arguments
                args = []
                if args_str:
                    args = [arg.strip().strip("\"'") for arg in args_str.split(",")]
                elif hasattr(q, method):
                    # Handle all other methods dynamically
                    result = getattr(q, method)(*args)
                    # If this is a terminal method, return its result
                    if method in terminal_methods:
                        return result
                    # Otherwise, result should be the updated query object
                    q = result
                else:
                    raise ValueError(f"Unknown method: {method}")

            # If we get here, we've processed all methods in the chain
            return q.result()


@click.command()
@click.argument("expression")
@click.argument("input_file", type=click.File("r"), default="-")
@click.option("-F", "--delimiter", default=",", help="Delimiter for input file")
def main(expression, input_file, delimiter):
    """Process INPUT_FILE with EXPRESSION and write to stdout. Use '-' for stdin."""
    # Read data from input using pandas
    df = pd.read_csv(input_file, delimiter=delimiter)
    if df.empty:
        click.echo("Input file is empty or not formatted correctly.", err=True)
        return

    # If the expression contains a dot, assume it is a chain of methods.
    try:
        result = parse_chain(expression, df)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return
    click.echo(result)


if __name__ == "__main__":
    main()

# Tabula

Process tabular data on the command line

## Overview
Tabula provides a chain-based syntax for data manipulation operations. Methods can be chained together using dot notation: `method1().method2().method3()`. One can perform operations like selecting columns, filtering rows, transforming data, and aggregating results all on the command line.

## Installation
Install Tabula using pip:
```bash
pip install tabula-cli
```

## Data Selection Methods

### `select(col1, col2, ...)`
Select specific columns from the dataset.
```bash
# Select single column
tabula "select(name)" data.csv

# Select multiple columns
tabula "select(name, age, salary)" data.csv
```

## Data Transformation Methods

### `upper(col)`
Convert text in specified column to uppercase.
```bash
tabula "select(name).upper(name)" data.csv
```

### `lower(col)`
Convert text in specified column to lowercase.
```bash
tabula "select(name).lower(name)" data.csv
```

### `strlen(col)`
Calculate the length of strings in specified column.
```bash
tabula "select(name).strlen(name)" data.csv
```

### `round(col, decimals)`
Round numeric values to specified decimal places.
```bash
tabula "select(salary).round(salary, 2)" data.csv
```

## Filtering Methods

### `where(condition)`
Filter rows based on conditions. Supports comparison operators and logical operators.
```bash
# Simple condition
tabula "where(age > 30)" data.csv

# Multiple conditions with AND
tabula "where(age > 25 & salary >= 50000)" data.csv

# Multiple conditions with OR
tabula "where(department == 'IT' | department == 'HR')" data.csv

# Complex conditions with parentheses
tabula "where((age > 30 & department == 'IT') | salary < 40000)" data.csv
```

## Data Limiting Methods

### `head(n)`
Return the first n rows (default: 5).
```bash
tabula "head(10)" data.csv
```

### `tail(n)`
Return the last n rows (default: 5).
```bash
tabula "tail(3)" data.csv
```

## Sorting Methods

### `sortby(col, descending=False)`
Sort data by specified column.
```bash
# Ascending sort
tabula "sortby(age)" data.csv

# Descending sort
tabula "sortby(salary, True)" data.csv
```

## Aggregation Methods (Terminal)

### `count()`
Count the number of rows.
```bash
tabula "count()" data.csv
tabula "where(age > 30).count()" data.csv
```

### `min(col)`, `max(col)`, `sum(col)`
Calculate minimum, maximum, or sum of a column.
```bash
tabula "min(age)" data.csv
tabula "max(salary)" data.csv
tabula "sum(salary)" data.csv
```

### `mean(col)`, `median(col)`, `mode(col)`
Calculate statistical measures.
```bash
tabula "mean(salary)" data.csv
tabula "median(age)" data.csv
```

### `std(col)`, `var(col)`
Calculate standard deviation and variance.
```bash
tabula "std(salary)" data.csv
tabula "var(age)" data.csv
```

### `first(col)`, `last(col)`
Get first or last value from a column.
```bash
tabula "first(name)" data.csv
tabula "last(name)" data.csv
```

## Unique Value Methods

### `uniq(col)`
Get unique values from a column.
```bash
tabula "uniq(department)" data.csv
```

### `uniqc(col)`
Count unique values (group by and count).
```bash
tabula "uniqc(department)" data.csv
```

## String Methods

### `strjoin(col, separator)`
Join all values in a column with a separator.
```bash
tabula "strjoin(name, ', ')" data.csv
```

## Utility Methods

### `columns()`
List all column names.
```bash
tabula "columns()" data.csv
```

## Complete Example Workflow

```bash
# Sample data.csv:
# name,age,salary,department
# Alice,25,50000,HR
# Bob,30,60000,IT
# Charlie,35,70000,Finance
# David,40,80000,IT

# Complex analysis: Find IT employees over 30, show their names and salaries, sorted by salary
tabula "where(department == 'IT' & age > 30).select(name, salary).sortby(salary)" data.csv

# Output:
# name,salary
# Bob,60000
# David,80000
```

## Method Chaining Rules

1. **Terminal Methods**: Methods like `count()`, `sum()`, `min()`, `max()` must be the last in the chain
2. **Column Selection**: Use `select()` before applying column-specific operations
3. **Filtering**: `where()` conditions support parentheses for complex logic
4. **String Operations**: Methods like `upper()`, `lower()`, `strlen()` work on text columns

## Output Formats

Use the `-o` flag to specify output format:
- `--outtype polars`: Default table format
- `--outtype csv`: CSV format
- `--outtype tsv`: Tab-separated values

```bash
tabula "select(name, age)"
# Tabula

Process tabular data on the command line, apply statistical tests and create plots. Tabula is a command-line tool for manipulating and analyzing tabular data. It allows you to perform complex data operations using a simple expression syntax directly in your terminal.

## Installation
Install Tabula using pip:
```bash
pip install tabula-cli
```

The three main components of Tabula are:
- **tabula**: For data manipulation and analysis
- **tabula-plot**: For creating plots from tabular data
- **tabula-stats**: For running statistical tests

# Tabula

Tabula provides a chain-based syntax for data manipulation operations. Methods can be chained together using dot notation: `method1().method2().method3()`. One can perform operations like selecting columns, filtering rows, transforming data, and aggregating results all on the command line.

## Data Selection Methods

### `select(col1, col2, ...)`
Select specific columns from the dataset.
```bash
# Select single column
tabula -p "select(name)" data.csv

# Select multiple columns
tabula -p "select(name, age, salary)" data.csv
```

## Data Transformation Methods

### `upper(col)`
Convert text in specified column to uppercase.
```bash
tabula -p "select(name).upper(name)" data.csv
```

### `lower(col)`
Convert text in specified column to lowercase.
```bash
tabula -p "select(name).lower(name)" data.csv
```

### `strlen(col)`
Calculate the length of strings in specified column.
```bash
tabula -p "select(name).strlen(name)" data.csv
```

### `round(col, decimals)`
Round numeric values to specified decimal places.
```bash
tabula -p "select(salary).round(salary, 2)" data.csv
```

## Filtering Methods

### `where(condition)`
Filter rows based on conditions. Supports comparison operators and logical operators.
```bash
# Simple condition
tabula -p "where(age > 30)" data.csv

# Multiple conditions with AND
tabula -p "where(age > 25 & salary >= 50000)" data.csv

# Multiple conditions with OR
tabula -p "where(department == 'IT' | department == 'HR')" data.csv

# Complex conditions with parentheses
tabula -p "where((age > 30 & department == 'IT') | salary < 40000)" data.csv
```

## Data Limiting Methods

### `head(n)`
Return the first n rows (default: 5).
```bash
tabula -p "head(10)" data.csv
```

### `tail(n)`
Return the last n rows (default: 5).
```bash
tabula -p "tail(3)" data.csv
```

## Sorting Methods

### `sortby(col, descending=False)`
Sort data by specified column.
```bash
# Ascending sort
tabula -p "sortby(age)" data.csv

# Descending sort
tabula -p "sortby(salary, True)" data.csv
```

## Aggregation Methods (Terminal)

### `count()`
Count the number of rows.
```bash
tabula -p "count()" data.csv
tabula -p "where(age > 30).count()" data.csv
```

### `min(col)`, `max(col)`, `sum(col)`
Calculate minimum, maximum, or sum of a column.
```bash
tabula -p "min(age)" data.csv
tabula -p "max(salary)" data.csv
tabula -p "sum(salary)" data.csv
```

### `mean(col)`, `median(col)`, `mode(col)`
Calculate statistical measures.
```bash
tabula -p "mean(salary)" data.csv
tabula -p "median(age)" data.csv
```

### `std(col)`, `var(col)`
Calculate standard deviation and variance.
```bash
tabula -p "std(salary)" data.csv
tabula -p "var(age)" data.csv
```

### `first(col)`, `last(col)`
Get first or last value from a column.
```bash
tabula -p "first(name)" data.csv
tabula -p "last(name)" data.csv
```

## Unique Value Methods

### `uniq(col)`
Get unique values from a column.
```bash
tabula -p "uniq(department)" data.csv
```

### `uniqc(col)`
Count unique values (group by and count).
```bash
tabula -p "uniqc(department)" data.csv
```

## String Methods

### `strjoin(col, separator)`
Join all values in a column with a separator.
```bash
tabula -p "strjoin(name, ', ')" data.csv
```

## Utility Methods

### `columns()`
List all column names.
```bash
tabula -p "columns()" data.csv
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
tabula -p "where(department == 'IT' & age > 30).select(name, salary).sortby(salary)" data.csv

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
tabula -p "select(name, age)"
```

## tabula-plot

tabula-plot allows you to create plots from tabular data directly in the terminal. It's an ideal companion for command-line data processing tools like awk and grep.

### Basic Usage

```bash
# Plot from a CSV file
tabula-plot data.csv -p "plot:relplot,kind:scatter,x:col1,y:col2,hue:col3"

# Plot from stdin (pipe data)
cat data.csv | tabula-plot - -p "plot:relplot,kind:scatter,x:col1,y:col2"

# Save plot to a file
tabula-plot data.csv -p "plot:relplot,kind:scatter,x:col1,y:col2" -o plot.png

# Specify column names if they're not in the first row
tabula-plot data.csv -p "plot:relplot,kind:scatter,x:col1,y:col2" -c "col1,col2,col3"

# Use a different separator for CSV data
tabula-plot data.tsv -p "plot:relplot,kind:scatter,x:col1,y:col2" -s "\t"
```

### Supported Plot Types

- **relplot** (default): Scatter and line plots
  - kinds: scatter, line
- **catplot**: Categorical plots
  - kinds: strip (default), swarm, box, violin, boxen, point, bar, count
- **displot**: Distribution plots
  - kinds: hist (default), kde, ecdf
- **pairplot**: Pairwise relationships in dataset

### Script Format

The plotting script uses a simple key:value format:

```
plot:plot_type,kind:plot_kind,x:x_column,y:y_column,hue:color_column,...
```

For example:
```
plot:catplot,kind:violin,x:category,y:value,hue:group
```

## tabula-stats

Statsmodels on the command line - a powerful CLI for running statistical tests directly in your terminal.

### Features

- **Simple CLI interface**: Run statistical tests without writing Python code
- **Multiple test types**: OLS, Logistic Regression, t-tests, ANOVA
- **Input flexibility**: Works with CSV files or piped stdin data
- **Integration with Unix tools**: Pairs perfectly with awk, grep, sed, jq, etc.

## Usage

```bash
# Basic syntax
tabula-stats [INPUT_FILE] -p "test:TYPE,PARAM1:VALUE1,PARAM2:VALUE2"

# Example: OLS regression on data.csv
tabula-stats data.csv -p "test:ols,dependent:y,independent:x+z"

# Read from stdin
cat data.csv | tabula-stats -p "test:ttest,sample1:group1,sample2:group2"
```

## Supported Tests

### Ordinary Least Squares (OLS) Regression

```bash
tabula-stats data.csv -p "test:ols,dependent:y,independent:x+z+w"
```

Required parameters:
- `dependent`: The dependent variable column
- `independent`: Formula for independent variables (e.g., `x+z+w` or `x*z`)

### Logistic Regression

```bash
tabula-stats data.csv -p "test:logit,dependent:binary_outcome,independent:x+z"
```

Required parameters:
- `dependent`: The binary dependent variable column
- `independent`: Formula for independent variables

### Generalized Linear Models (GLM)

```bash
tabula-stats data.csv -p "test:glm,dependent:y,independent:x+z,family:poisson,link:log"
```

Required parameters:
- `dependent`: The dependent variable column
- `independent`: Formula for independent variables
- `family`: Distribution family - one of:
  - `gaussian`: For continuous data (normal distribution)
  - `binomial`: For binary data (0/1)
  - `poisson`: For count data
  - `gamma`: For positive continuous data with variance proportional to square of mean
  - `inverse_gaussian`: For positive continuous data
  - `neg_binomial`: For overdispersed count data
  - `tweedie`: For compound Poisson-gamma distribution

Optional parameters:
- `link`: Link function - depends on the family, common options include:
  - `identity`: No transformation (default for Gaussian)
  - `log`: Log transformation (default for Poisson and Gamma)
  - `logit`: Logit transformation (default for Binomial)
  - `probit`: Probit transformation
  - `cloglog`: Complementary log-log transformation
  - `inverse`: Inverse transformation
  - `power`: Power transformation
- `alpha`: Alpha parameter for NegativeBinomial family (default 1.0)
- `var_power`: Variance power for Tweedie family (default 1.5)
- `power`: Power parameter for Power link function (default 1.0)

Examples:
```bash
# Poisson regression with log link
tabula-stats data.csv -p "test:glm,dependent:count,independent:x+z,family:poisson"

# Gamma regression with log link
tabula-stats data.csv -p "test:glm,dependent:duration,independent:x+z,family:gamma"

# Binomial regression with probit link
tabula-stats data.csv -p "test:glm,dependent:success,independent:x+z,family:binomial,link:probit"
```

### Two-sample t-test

```bash
tabula-stats data.csv -p "test:ttest,sample1:group1,sample2:group2,alternative:two-sided"
```

Required parameters:
- `sample1`: First sample column name
- `sample2`: Second sample column name

Optional parameters:
- `alternative`: Test type ('two-sided', 'larger', or 'smaller')

### ANOVA

```bash
tabula-stats data.csv -p "test:anova,formula:y ~ C(group)"
```

## Examples

### CSV with headers

```bash
$ cat data.csv
x,y,group
1,3.4,A
2,5.7,A
3,6.3,B
4,8.1,B

$ tabula-stats data.csv -p "test:ols,x:y,y:x"
```

### CSV without headers

```bash
$ cat data_no_header.csv
1,3.4,A
2,5.7,A
3,6.3,B
4,8.1,B

$ tabula-stats data_no_header.csv -p "test:ols,x:y,indepenydent:x" 
```

### Saving output to file

```bash
$ tabula-stats data.csv -p "test:ols,dependent:y,independent:x" > results.txt
```

import pandas as pd
import pytest
from click.testing import CliRunner
import io
from tabula import Query, parse_chain, main


# Sample CSV content for testing
SAMPLE_CSV = """name,age,salary
Alice,30,70000
Bob,25,50000
Carol,40,90000
"""


@pytest.fixture
def sample_df():
    data = {
        "name": ["Alice Johnson", "Bob Smith", "Carol Davis"],
        "age": [28, 35, 42],
        "department": ["Engineering", "Marketing", "Engineering"],
        "salary": [75000, 65000, 95000],
        "years_experience": [3.5, 8.2, 12.0],
        "city": ["New York", "San Francisco", "Seattle"],
        "is_manager": [False, True, True],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_csv(tmp_path):
    file_path = tmp_path / "sample.csv"
    file_path.write_text(SAMPLE_CSV)
    return str(file_path)


def test_select_chain(sample_csv):
    runner = CliRunner()
    # Chain: select columns age and salary then head(2)
    expression = "select(age, salary).head(2)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    expected_csv = "age,salary\n30,70000\n25,50000\n"
    assert expected_csv in result.output


def test_where_and_len(sample_csv):
    runner = CliRunner()
    # Chain: select age, filter rows with age > 30, then count using len(age)
    expression = "select(age).where(age>30).len(age)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    # Only Carol (age 40) satisfies age>30, so length should be 1
    assert result.output.strip() == "1"


def test_tail(sample_csv):
    runner = CliRunner()
    expression = "tail(2)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    expected_csv = "name,age,salary\nBob,25,50000\nCarol,40,90000\n"
    assert expected_csv in result.output


def test_sort_asc(sample_csv):
    runner = CliRunner()
    expression = "sort(age)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    # Should be sorted by age ascending: Bob(25), Alice(30), Carol(40)
    lines = result.output.strip().split("\n")
    assert "Bob,25,50000" in lines[1]
    assert "Alice,30,70000" in lines[2]
    assert "Carol,40,90000" in lines[3]


def test_sort_desc(sample_csv):
    runner = CliRunner()
    expression = "sort(age, desc=True)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    # Should be sorted by age descending: Carol(40), Alice(30), Bob(25)
    lines = result.output.strip().split("\n")
    assert "Carol,40,90000" in lines[1]
    assert "Alice,30,70000" in lines[2]
    assert "Bob,25,50000" in lines[3]


def test_min_terminal(sample_csv):
    runner = CliRunner()
    expression = "select(age).min()"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert result.output.strip() == "25"


def test_max_terminal(sample_csv):
    runner = CliRunner()
    expression = "select(salary).max()"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert result.output.strip() == "90000"


def test_sum_terminal(sample_csv):
    runner = CliRunner()
    expression = "select(salary).sum()"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert result.output.strip() == "210000"


def test_mean_terminal(sample_csv):
    runner = CliRunner()
    expression = "select(age).mean()"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    # Mean of 30, 25, 40 is 31.666...
    assert "31.66" in result.output


def test_lower_method(sample_csv):
    runner = CliRunner()
    expression = "select(name).lower(name)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert "alice" in result.output.lower()
    assert "bob" in result.output.lower()
    assert "carol" in result.output.lower()


def test_unique_method(sample_csv):
    runner = CliRunner()
    expression = "select(name).unique(name)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    # Should contain all unique names
    assert "Alice" in result.output
    assert "Bob" in result.output
    assert "Carol" in result.output


def test_count_method(sample_csv):
    runner = CliRunner()
    expression = "count()"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert result.output.strip() == "3"


def test_drop_method(sample_csv):
    runner = CliRunner()
    expression = "drop(age)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert "age" not in result.output
    assert "name" in result.output
    assert "salary" in result.output


def test_complex_chain(sample_csv):
    runner = CliRunner()
    expression = "select(name, age).where(age > 27).sort(age, desc=True).head(2)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    # Should filter age > 27 (Alice:30, Carol:40), sort desc, take top 2
    lines = result.output.strip().split("\n")
    assert "Carol,40" in lines[1]
    assert "Alice,30" in lines[2]


def test_empty_result(sample_csv):
    runner = CliRunner()
    expression = "where(age > 100)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    # Should return empty DataFrame with just headers
    lines = result.output.strip().split("\n")
    assert len(lines) == 1  # Just the header line
    assert "name,age,salary" in lines[0]


def test_invalid_method(sample_csv):
    runner = CliRunner()
    expression = "nonexistent_method()"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code != 0
    assert "not found" in result.output or "invalid" in result.output.lower()


def test_invalid_syntax(sample_csv):
    runner = CliRunner()
    expression = "select(name"  # Missing closing parenthesis
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code != 0


def test_multiple_terminal_methods(sample_csv):
    runner = CliRunner()
    expression = "select(age).min().max()"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code != 0
    assert "must be the last call" in result.output


def test_join_with_different_separator(sample_csv):
    runner = CliRunner()
    expression = "join(name, '|')"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert "|" in result.output
    assert "Alice|Bob|Carol" in result.output


def test_len_with_column(sample_csv):
    runner = CliRunner()
    expression = "len(name)"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert result.output.strip() == "3"


def test_where_with_string_condition(sample_csv):
    runner = CliRunner()
    expression = "where(name == 'Alice')"
    result = runner.invoke(main, [expression, sample_csv])
    assert result.exit_code == 0
    assert "Alice" in result.output
    assert "Bob" not in result.output
    assert "Carol" not in result.output


def test_select(sample_df):
    q = Query(sample_df)
    q = q.select("name", "department")
    assert list(q.df.columns) == ["name", "department"]


def test_upper(sample_df):
    q = Query(sample_df)
    q = q.upper("department")
    # check that all department entries are uppercase
    assert all(q.df["department"].str.isupper())


def test_where(sample_df):
    q = Query(sample_df)
    q = q.where("age > 30")
    # Only Bob and Carol should remain (35, 42)
    assert all(q.df["age"] > 30)


def test_chain_parse(sample_df):
    # chain expression: select specific columns then convert department to uppercase
    chain_expr = "select(name,department).upper(department)"
    result_csv = parse_chain(chain_expr, sample_df)
    # result_csv is a CSV string; verify that one of the uppercase department names is present
    assert "ENGINEERING" in result_csv or "MARKETING" in result_csv


def test_invalid_column(sample_df):
    chain_expr = "select(name,nonexistent)"
    with pytest.raises(ValueError):
        parse_chain(chain_expr, sample_df)


def test_join(sample_df):
    # Test join returns concatenated string using ';' as separator
    chain_expr = "join(name,';')"
    result = parse_chain(chain_expr, sample_df)
    # Check that the separator is present in the result string
    assert ";" in result


def test_head(sample_df):
    # Test using a terminal method to limit rows output
    chain_expr = "head(2)"
    result_csv = parse_chain(chain_expr, sample_df)
    df_result = pd.read_csv(io.StringIO(result_csv))
    assert len(df_result) == 2

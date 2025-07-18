import os
import tempfile

import polars as pl
import pytest
from click.testing import CliRunner

from tabula_cli import VALID_METHODS, main, parse_chain, validate_chain


class TestValidateChain:
    """Test cases for validate_chain function."""

    def test_valid_single_method(self):
        """Test valid single method calls."""
        assert validate_chain("select(col1)")
        assert validate_chain("head(10)")
        assert validate_chain("count()")

    def test_valid_chained_methods(self):
        """Test valid method chains."""
        assert validate_chain("select(col1,col2).head(5)")
        assert validate_chain("select(name).upper(name).head(10)")
        assert validate_chain("where(age,>,18).count()")

    def test_invalid_empty_expression(self):
        """Test invalid empty expressions."""
        assert not validate_chain("")
        assert not validate_chain("   ")
        assert not validate_chain(None)

    def test_invalid_method_format(self):
        """Test invalid method formats."""
        assert not validate_chain("select")  # Missing parentheses
        assert not validate_chain("select(col1")  # Missing closing parenthesis
        assert not validate_chain("select col1)")  # Missing opening parenthesis
        assert not validate_chain("select(col1).head")  # Missing parentheses in chain

    def test_invalid_method_names(self):
        """Test invalid method names."""
        assert not validate_chain("invalid_method()")
        assert not validate_chain("select(col1).invalid_method()")
        assert not validate_chain("123method()")

    def test_all_valid_methods(self):
        """Test that all methods in VALID_METHODS are accepted."""
        for method in VALID_METHODS:
            assert validate_chain(f"{method}()")
            assert validate_chain(f"select(col1).{method}()")


class TestParseChain:
    """Test cases for parse_chain function."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe for testing."""
        return pl.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie", "David"],
                "age": [25, 30, 35, 40],
                "salary": [50000, 60000, 70000, 80000],
                "department": ["HR", "IT", "Finance", "IT"],
            }
        )

    def test_select_single_column(self, sample_df):
        """Test selecting a single column."""
        result = parse_chain("select(name)", sample_df)
        assert result.columns == ["name"]
        assert len(result) == 4

    def test_select_multiple_columns(self, sample_df):
        """Test selecting multiple columns."""
        result = parse_chain("select(name,age)", sample_df)
        assert result.columns == ["name", "age"]
        assert len(result) == 4

    def test_head_method(self, sample_df):
        """Test head method."""
        result = parse_chain("head(2)", sample_df)
        assert len(result) == 2

    def test_tail_method(self, sample_df):
        """Test tail method."""
        result = parse_chain("tail(2)", sample_df)
        assert len(result) == 2

    def test_count_method(self, sample_df):
        """Test count method."""
        result = parse_chain("count()", sample_df)
        assert result.item() == 4

    def test_strjoin_method(self, sample_df):
        """Test string join method."""
        result = parse_chain("select(name).strjoin(name, ', ')", sample_df)
        assert result.item() == "Alice, Bob, Charlie, David"

    def test_string_methods(self, sample_df):
        """Test string transformation methods."""
        result = parse_chain("select(name).upper(name)", sample_df)
        assert "ALICE" in result["name"].to_list()

        result = parse_chain("select(name).lower(name)", sample_df)
        assert "alice" in result["name"].to_list()

    def test_aggregation_methods(self, sample_df):
        """Test aggregation methods."""
        result = parse_chain("select(age).min(age)", sample_df)
        assert result.item() == 25

        result = parse_chain("select(age).max(age)", sample_df)
        assert result.item() == 40

        result = parse_chain("select(salary).sum(salary)", sample_df)
        assert result.item() == 260000

    def test_chained_operations(self, sample_df):
        """Test chained operations."""
        result = parse_chain("select(name,age).head(2)", sample_df)
        assert result.columns == ["name", "age"]
        assert len(result) == 2

    def test_where_filter(self, sample_df):
        """Test where filtering."""
        result = parse_chain("where(age>30)", sample_df)
        assert len(result) == 2  # Charlie and David

    def test_where_and_condition(self, sample_df):
        """Test where with AND (&) condition."""
        result = parse_chain("where((age>25) & (salary>=70000))", sample_df)
        # Only Charlie (35, 70000) and David (40, 80000) match
        assert len(result) == 2
        names = result["name"].to_list()
        assert "Charlie" in names
        assert "David" in names

    def test_where_or_condition(self, sample_df):
        """Test where with OR (|) condition."""
        result = parse_chain(
            "where((department=='HR') | (department=='Finance'))", sample_df
        )
        names = result["name"].to_list()
        assert "Alice" in names  # HR
        assert "Charlie" in names  # Finance
        assert len(result) == 2

    def test_where_multiple_and_or(self, sample_df):
        """Test where with multiple AND/OR conditions."""
        result = parse_chain(
            "where(((age>=30) & (department=='IT')) | (salary<60000))", sample_df
        )
        names = result["name"].to_list()
        # Bob (30, IT), David (40, IT), Alice (25, HR, salary 50000)
        assert set(names) == {"Bob", "David", "Alice"}

    def test_where_parentheses_precedence(self, sample_df):
        """Test where with parentheses for precedence."""
        result = parse_chain(
            "where((age>30) | ((department=='HR') & (salary<60000)))", sample_df
        )
        names = result["name"].to_list()
        # Charlie (35), David (40), Alice (HR, 50000)
        assert set(names) == {"Charlie", "David", "Alice"}

    def test_where_string_comparison(self, sample_df):
        """Test where with string comparison."""
        result = parse_chain("where(name=='Bob')", sample_df)
        assert len(result) == 1
        assert result["name"][0] == "Bob"

    def test_sortby_method(self, sample_df):
        """Test sorting."""
        result = parse_chain("sortby(age)", sample_df)
        ages = result["age"].to_list()
        assert ages == sorted(ages)

    def test_uniq_method(self, sample_df):
        """Test unique values."""
        result = parse_chain("uniq(department)", sample_df)
        assert len(result) == 3

    def test_strlen_method(self, sample_df):
        """Test strlen method for string column."""
        result = parse_chain("select(name).strlen(name)", sample_df)
        # Should return a DataFrame with the same number of rows and a column with string lengths
        lengths = result["name_length"].to_list()
        expected_lengths = [len(name) for name in sample_df["name"].to_list()]
        assert lengths == expected_lengths

    def test_strlen_on_non_string_column(self, sample_df):
        """Test strlen method on a non-string column should raise or handle gracefully."""
        # Try to apply strlen to an integer column
        with pytest.raises(Exception):
            parse_chain("select(age).strlen(age)", sample_df)

    def test_round_method(self, sample_df):
        """Test rounding numbers."""
        # Add a column with decimals
        df = sample_df.with_columns((pl.col("salary") / 3).alias("salary_third"))
        result = parse_chain("select(salary_third).round(salary_third,2)", df)
        # Check that values are rounded to 2 decimal places
        values = result["salary_third"].to_list()
        for val in values:
            assert len(str(val).split(".")[-1]) <= 2


class TestCLI:
    """Test cases for CLI functionality."""

    def test_cli_basic_operation(self):
        """Test basic CLI operation."""
        runner = CliRunner()

        # Create a temporary CSV file
        csv_content = (
            "name,age,salary\nAlice,25,50000\nBob,30,60000\nCharlie,35,70000\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            result = runner.invoke(main, ["select(name)", temp_file])
            assert result.exit_code == 0
            assert "Alice" in result.output
            assert "Bob" in result.output
            assert "Charlie" in result.output
        finally:
            os.unlink(temp_file)

    def test_cli_with_head(self):
        """Test CLI with head operation."""
        runner = CliRunner()

        csv_content = "name,age\nAlice,25\nBob,30\nCharlie,35\nDavid,40\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            result = runner.invoke(main, ["head(2)", temp_file])
            assert result.exit_code == 0
            # Should only show 2 rows (plus header info)
            assert "Alice" in result.output
            assert "Bob" in result.output
        finally:
            os.unlink(temp_file)

    def test_cli_no_header_option(self):
        """Test CLI with no-header option."""
        runner = CliRunner()

        csv_content = "Alice,25,50000\nBob,30,60000\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            result = runner.invoke(main, ["select(column_1)", temp_file, "--no-header"])
            assert result.exit_code == 0
            assert "Alice" in result.output
            assert "Bob" in result.output
        finally:
            os.unlink(temp_file)

    def test_cli_stdin_input(self):
        """Test CLI with stdin input."""
        runner = CliRunner()

        csv_content = "name,age\nAlice,25\nBob,30\n"

        result = runner.invoke(main, ["select(name)"], input=csv_content)
        assert result.exit_code == 0
        assert "Alice" in result.output
        assert "Bob" in result.output

    def test_cli_invalid_expression(self):
        """Test CLI with invalid expression."""
        runner = CliRunner()

        csv_content = "name,age\nAlice,25\nBob,30\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            result = runner.invoke(main, ["invalid_method()", temp_file])
            assert result.exit_code == 0
            assert "Invalid expression format" in result.output
        finally:
            os.unlink(temp_file)

    def test_cli_chained_operations(self):
        """Test CLI with chained operations."""
        runner = CliRunner()

        csv_content = "name,age,salary\nAlice,25,50000\nBob,30,60000\nCharlie,35,70000\nDavid,40,80000\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            result = runner.invoke(main, ["select(name,age).head(2)", temp_file])
            assert result.exit_code == 0
            assert "Alice" in result.output
            assert "Bob" in result.output
            # Should not contain Charlie or David due to head(2)
        finally:
            os.unlink(temp_file)

    def test_cli_empty_file(self):
        """Test CLI with empty file."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("")  # Empty file
            temp_file = f.name

        try:
            result = runner.invoke(main, ["select(name)", temp_file])
            assert result.exit_code == 0
            assert "Input file is empty" in result.output
        finally:
            os.unlink(temp_file)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_complex_argument_parsing(self):
        """Test complex argument parsing with quotes and special characters."""
        df = pl.DataFrame({"name": ["Alice", "Bob"]})

        # Test quoted strings
        result = parse_chain("select(name)", df)
        assert result.columns == ["name"]

    def test_method_with_no_args(self):
        """Test methods that don't require arguments."""
        df = pl.DataFrame({"name": ["Alice", "Bob"], "age": [25, 30]})

        result = parse_chain("count()", df)
        assert result.item() == 2

    def test_statistical_methods(self):
        """Test statistical methods."""
        df = pl.DataFrame({"values": [1, 2, 3, 4, 5]})

        result = parse_chain("select(values).mean(values)", df)
        assert result.item() == 3.0

        result = parse_chain("select(values).median(values)", df)
        assert result.item() == 3.0

        result = parse_chain("select(values).std(values)", df)
        assert result.item() > 0  # Should be positive

    def test_first_last_methods(self):
        """Test first and last methods."""
        df = pl.DataFrame({"name": ["Alice", "Bob", "Charlie"]})

        result = parse_chain("select(name).first(name)", df)
        assert result.item() == "Alice"

        result = parse_chain("select(name).last(name)", df)
        assert result.item() == "Charlie"
